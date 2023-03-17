#!/usr/bin/env python3
"""duty_csv.py

Generate DNAnexus download links for end of run processing file downloads for
run types that require file downloads, and save to a .csv file
"""
import sys
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
import argparse
import subprocess
import json
import pandas as pd
import dxpy
import jinja2
import config
from logger import Logger


class GenerateOutput:
    """
    Create a CSV file with download links for required files for that runtype
    that need to be placed on the trust shared drives

    CSV file is then sent over email to the config-specified recipient, if
    that runfolder has files requiring download. The HTML file used as the
    email message is output

    A log file is created with information about the processing steps

    Methods
        get_runtype()
            String comparison with config variables to determine runtype
        get_jobs()
            Find all executions/jobs for a given project
        get_data_dicts()
            Search DNAnexus to find file data objects based on
            config-defined regexp patterns
        create_url_dataframe()
            Generate URL links from a list of data and
            produce a pandas dataframe
        get_url_attrs()
            Return list of lists, each list containing the items that populate
            the rows of the CSV file
        get_trust_dirs()
            Return list of trust directories that the file requires download
            to. If file name contains StG pan number, only download to the
            config-specified StG dir. If file name contains custom panels
            capture pan number, download to both StG and Synnovis config-
            specified dirs. Otherwise, only download to the config-specified
            Synnovis dir.
        get_url()
            Create a url for a file in DNAnexus
        create_csv()
            Write dataframe to CSV, and return CSV format as string
        get_filetype_html()
            Generate HTML for files by filetype
        get_number_of_files()
            Calculate number of files to download for project
        generate_email_html()
            Generate HTML
        get_message_obj()
            Create message object
        send_email()
            Use smtplib to send an email
    """

    def __init__(
        self,
        project_name: str,
        project_id: str,
        email_user: str,
        email_pw: str,
        stg_pannumbers: list,
        cp_capture_pannos: list,
        mode: str,
    ):
        """
        Constructor for the GenerateOutput class
            :param project_name (str):          DNAnexus project name
            :param project_id (str):            DNAnexus project ID
            :param email_user (str):            Mail server username
            :param email_pw (str):              Mail server password
            :param stg_pannumbers (list):       List of St George's pan numbers
            :param cp_capture_pannos (list):    Custom panels whole capture
                                                pan numbers
            :mode (str):                        Script mode ("TEST" or "PROD")
        """
        self.email_user = email_user
        self.email_pw = email_pw
        self.stg_pannumbers = stg_pannumbers
        self.cp_capture_pannos = cp_capture_pannos
        self.script_mode = mode
        self.project_name = project_name
        self.project_id = project_id
        self.runtype = self.get_runtype()
        self.email_recipient = config.EMAIL_RECIPIENT[self.script_mode]
        self.project_jobs = self.get_jobs()
        self.csvfile_name = (
            f"{self.project_name}.{self.project_id}.{self.runtype}"
            f".duty_csv.csv"
        )
        self.htmlfile_name = (
            f"{self.project_name}.{self.project_id}.{self.runtype}"
            f".duty_csv.html"
        )
        self.csvfile_path = os.path.join(os.getcwd(), self.csvfile_name)
        self.htmlfile_path = os.path.join(os.getcwd(), self.htmlfile_name)
        self.template = jinja2.Environment(
            loader=jinja2.FileSystemLoader(config.TEMPLATE_DIR),
            autoescape=True,
        ).get_template(config.EMAIL_TEMPLATE)

        self.email_subject = config.EMAIL_SUBJECT[self.script_mode].format(
            self.runtype, self.project_name
        )
        self.file_dict = config.PER_RUNTYPE_DOWNLOADS[self.runtype]
        self.data_obj_dict, self.data_num_dict = self.get_data_dicts()
        self.url_dataframe = self.create_url_dataframe()
        self.csv_contents = self.create_csv()
        self.filetype_html = self.get_filetype_html()
        self.number_of_files = self.get_number_of_files()
        self.html = self.generate_email_html()
        self.email_msg = self.get_message_obj()
        self.send_email()
        logger.info("Script completed")

    def get_runtype(self) -> str | None:
        """
        String comparison with config variables to detetrmine runtype
            :return runtype (str, None):    Runtype string, or none if
                                            cannot be parsed
        """
        project_runtype = None
        for runtype in config.RUNTYPE_IDENTIFIERS:
            if all(
                identifier in self.project_name
                for identifier in config.RUNTYPE_IDENTIFIERS[runtype][
                    "present"
                ]
            ) and all(
                identifier not in self.project_name
                for identifier in config.RUNTYPE_IDENTIFIERS[runtype]["absent"]
            ):
                project_runtype = runtype
        if project_runtype:
            logger.info("This run is a %s run", project_runtype)
            return project_runtype
        else:
            logger.error(
                "Runtype in runfolder name does not "
                "match config-defined runtypes"
            )
            sys.exit(1)

    def get_jobs(self) -> list:
        """
        Find all executions/jobs for a given project
            :return project_jobs (list): List of job ID strings within project
        """
        try:
            project_jobs = list(
                dxpy.bindings.search.find_executions(
                    project=self.project_id, describe=True
                )
            )
            states = []
            for job in project_jobs:
                state = job.get("describe").get("state")
                states.append(state)
            logger.info(
                "%s jobs were identified in the DNAnexus project",
                len(project_jobs),
            )
            return project_jobs
        except Exception as exception:
            logger.error(
                "There was a problem identifying jobs "
                "in the DNAnexus project: %s",
                exception,
            )
            sys.exit(1)

    def get_data_dicts(self) -> tuple[dict, dict] | tuple[None, None]:
        """
        Search DNAnexus to find file data objects based on
        config-defined regexp patterns. N.B. find_data_objects finds files
        both at the defined folder level and within any subdirectories
            :return data_obj_dict(dict) | None: Dictionary of data objects for
                                                use in downloading files
            :return data_num_dict(dict) | None: Dictionary of number of data
                                                object per file type
        """
        if self.file_dict:
            logger.info(
                "The config defines that this run should "
                "have files for download"
            )
            data_obj_dict = {}
            data_num_dict = {}
            logger.info(
                "Searching for data objects in DNAnexus project "
                "using regular expressions"
            )
            for filetype in self.file_dict:
                data_obj_dict[filetype] = list(
                    dxpy.bindings.search.find_data_objects(
                        project=self.project_id,
                        name=self.file_dict[filetype]["regex"],
                        name_mode="regexp",
                        describe=True,
                        folder=self.file_dict[filetype]["folder"],
                    )
                )
                try:
                    data_num = len(data_obj_dict[filetype])
                    logger.info(
                        "The number of items for %s is %s", filetype, data_num
                    )
                    data_num_dict[filetype] = data_num
                except Exception:
                    logger.error(
                        "No data requiring download was found for "
                        "the following file type: %s"
                    )
                    sys.exit(1)
            return data_obj_dict, data_num_dict
        else:
            logger.info(
                "No DNAnexus data objects dictionary was created as the "
                "config defines that this run will not have files for download"
            )
            return None, None

    def create_url_dataframe(self) -> pd.core.frame.DataFrame | None:
        """
        Generate URL links from a list of data and produce a pandas dataframe
            :return dataframe (tabular) | None: Pandas dataframe containing
                                                URL links, or None if runtype
                                                has no files for download
        """
        if self.data_obj_dict:
            try:
                logger.info(
                    "Creating urls dataframe for %s project: %s",
                    self.runtype,
                    self.project_name,
                )
                # Load into dataframe, explode so rows with more than one trust
                # dir are split into distinct rows, sort values by sample name
                dataframe = (
                    pd.DataFrame(
                        self.get_url_attrs(),
                        columns=config.COLS,
                    )
                    .explode("GSTT_dir")
                    .sort_values(
                        by=["Type", "Name"],
                        ascending=True,
                        ignore_index=True,
                    )
                )
                dataframe.index += 1  # Start sample numbering from 1
                logger.info(
                    "Created urls dataframe for %s project: %s",
                    self.runtype,
                    self.project_name,
                )
                return dataframe

            except Exception as exception:
                logger.error(
                    "An error was encountered when creating the urls "
                    "dataframe: %s",
                    exception,
                )
                sys.exit(1)
        else:
            logger.info(
                "No URLs dataframe was created as there is no DNAnexus data "
                "objects dictionary"
            )

    def get_url_attrs(self) -> list:
        """
        Return list of lists, each list containing the items that populate the
        rows of the CSV file
            :return attrs_list (list): List of lists, each
        """
        try:
            attrs_list = []
            for filetype in self.data_obj_dict:
                subdir = config.GSTT_PATHS[self.script_mode][self.runtype][
                    filetype
                ]["subdir"]
                for data_obj in self.data_obj_dict[filetype]:
                    file_name = data_obj.get("describe").get("name")
                    folder = data_obj.get("describe").get("folder")
                    file_id = data_obj.get("id")
                    url = self.get_url(file_id, self.project_id, file_name)
                    trust_dirs = self.get_trust_dirs(filetype, url)
                    attrs_list.append(
                        [file_name, folder, filetype, url, trust_dirs, subdir]
                    )
            return attrs_list
        except Exception as exception:
            logger.error(
                "An exception was encountered when building the urls "
                "attributes list, with exception: %s",
                exception,
            )
            sys.exit(1)

    def get_trust_dirs(self, filetype: str, url: str) -> list:
        """
        Return list of trust directories that the file requires download to. If
        file name contains StG pan number, only download to the config-
        specified StG dir. If file name contains custom panels capture pan
        number, download to both StG and Synnovis config-specified dirs.
        Otherwise, only download to the config-specified Synnovis dir.
            :return trust_dirs (list): List of directories (strs)
        """
        trust_dirs = []
        try:
            if any(pannumber in url for pannumber in self.stg_pannumbers):
                trust_dirs.append(
                    config.GSTT_PATHS[self.script_mode][self.runtype][
                        filetype
                    ]["StG"]
                )
            elif any(pannumber in url for pannumber in self.cp_capture_pannos):
                trust_dirs.extend(
                    (
                        config.GSTT_PATHS[self.script_mode][self.runtype][
                            filetype
                        ]["StG"],
                        config.GSTT_PATHS[self.script_mode][self.runtype][
                            filetype
                        ]["Via"],
                    )
                )
            else:
                trust_dirs.append(
                    config.GSTT_PATHS[self.script_mode][self.runtype][
                        filetype
                    ]["Via"]
                )
            return trust_dirs
        except Exception as exception:
            logger.error(
                "Could not return trust directory list for url %s, "
                "with exception: %s",
                url,
                exception,
            )
            sys.exit(1)

    def get_url(self, file_id: str, project_id: str, file_name: str) -> str:
        """
        Create a url for a file in DNAnexus
            :return url (str): DNAnexus URL for a file
        """
        dxfile = dxpy.DXFile(file_id)
        try:
            url = dxfile.get_download_url(
                duration=60
                * 60
                * 24
                * 5,  # 60 sec x 60 min x 24 hours * 5 days
                preauthenticated=True,
                project=project_id,
                filename=file_name,
            )[0]
            logger.info("Url for %s retrieved successfully", dxfile)
            return url
        except Exception as exception:
            logger.error(
                "Could not retrieve url for file %s, with exception: %s",
                dxfile,
                exception,
            )
            sys.exit(1)

    def create_csv(self) -> str | None:
        """
        Write dataframe to CSV, and return CSV format as string
            :return csv_contents (str): Return resulting CSV format as string
        """
        if self.url_dataframe is not None:
            logger.info(
                "Creating csv file for %s project: %s",
                self.runtype,
                self.project_name,
            )
            try:
                # Write to file
                self.url_dataframe.to_csv(self.csvfile_path, index=False)
                # Save as variable
                csv_contents = self.url_dataframe.to_csv(index=False)
                logger.info("CSV file has been created: %s", self.csvfile_path)
                return csv_contents

            except Exception as exception:
                logger.error(
                    "An error was encountered when writing the urls "
                    "dataframe to CSV: %s",
                    exception,
                )
                sys.exit(1)
        else:
            logger.info("No CSV file was created as no URL dataframe exists")

    def get_filetype_html(self) -> str:
        """
        Generate HTML for files by filetype
            :return filetype_html (str):    Html string
        """
        if self.data_num_dict:
            filetype_html = ""
            try:
                for filetype in self.data_num_dict:
                    filetype_html += (
                        f"{self.data_num_dict[filetype]} "
                        f"{filetype} files<br>"
                    )
                logger.info("Filetype HTML successfully generated")
                return filetype_html
            except Exception as exception:
                logger.error(
                    "There was an exception when generating the "
                    "filetype html: %s",
                    exception,
                )
                sys.exit(1)
        else:
            logger.info(
                "Filetype HTML was not generated for this project as "
                "there are no DNAnexus data objects marked for download"
            )

    def get_number_of_files(self) -> int | None:
        """
        Calculate number of files to download for project
            :return number_of_files (int) | None: Number of files
        """
        if self.data_num_dict:
            number_of_files = sum(self.data_num_dict.values())
            logger.info(
                "%s files were identified for download for this project",
                number_of_files,
            )
            # If there are no files and files were expected from this runtype
            if number_of_files == 0 and self.file_dict:
                logger.error(
                    "Files were expected to be identified for download for "
                    "this project but none were found"
                )
                sys.exit(1)
            else:
                return number_of_files
        else:
            logger.info(
                "Files could not be counted as there are no DNAnexus data "
                "objects marked for download"
            )

    def generate_email_html(self) -> str:
        """
        Generate HTML
            :return html (str): Rendered html as a string
        """
        # If the runfolder has files that need download
        try:
            html = self.template.render(
                runtype=self.runtype,
                num_jobs=len(self.project_jobs),
                project_name=self.project_name,
                number_of_files=self.number_of_files,
                files_by_filetype=self.filetype_html,
                git_tag=git_tag(),
                script_mode=self.script_mode,
            )
            logger.info("Successfully generated email HTML")
            with open(self.htmlfile_path, "w+", encoding="utf-8") as htmlfile:
                htmlfile.write(html)
            logger.info("HTML successfully written to file")
            return html
        except Exception as exception:
            logger.error(
                "There was a problem generating the html file, with "
                "the following exception: %s",
                exception,
            )
            sys.exit(1)

    def get_message_obj(self) -> MIMEMultipart | None:
        """
        Create message object
            :return msg (object) | None: Message object for email
        """
        msg = MIMEMultipart()
        # Both header types for maximum compatibility
        msg["X-Priority"] = "1"
        msg["X-MSMail-Priority"] = "High"
        msg["Subject"] = self.email_subject
        msg["From"] = config.EMAIL_SENDER
        msg["To"] = self.email_recipient
        msg.attach(MIMEText(self.html, "html"))

        if self.csv_contents:
            attachment = MIMEApplication(self.csv_contents)
            attachment["Content-Disposition"] = (
                f"attachment; " f'filename="{self.csvfile_name}"'
            )
            msg.attach(attachment)
            logger.info("Successfully created email message")
        else:
            logger.info("No CSV file was attached for this run")
        return msg

    def send_email(self) -> None:
        """
        Use smtplib to send an email
        """
        try:
            # Configure SMTP server connection for sending log msgs via e-mail
            server = smtplib.SMTP(
                host=config.HOST, port=config.PORT, timeout=10
            )

            # Verbosity turned off - set to true to get debug messages
            server.set_debuglevel(False)
            server.starttls()  # Encrypt SMTP commands using TLS
            server.ehlo()  # Identify client to ESMTP server using EHLO cmds
            # Login to server with user credentials
            server.login(self.email_user, self.email_pw)
            server.sendmail(
                config.EMAIL_SENDER,
                self.email_recipient,
                self.email_msg.as_string(),
            )
            logger.info(
                "CSV file has been emailed to %s",
                self.email_recipient,
            )
        except Exception as exception:
            logger.error(
                "There was a problem sending the email, with "
                "the following exception: %s",
                exception,
            )
            sys.exit(1)


def arg_parse() -> dict:
    """
    Parse arguments supplied by the command line. Create argument parser,
    define command line arguments, then parse supplied command line arguments
    using the created argument parser
        :return (dict): Parsed command line attributes
    """
    parser = argparse.ArgumentParser(
        description="Generate a CSV file containing links for downloading "
        "files from that runfolder for end-of-duty tasks"
    )
    requirednamed = parser.add_argument_group("Required named arguments")
    requirednamed.add_argument(
        "-P",
        "--project_name",
        type=str,
        help="Name of project to obtain download links from",
        required=True,
    )
    requirednamed.add_argument(
        "-I",
        "--project_id",
        type=str,
        help="ID of project to obtain download links from",
        required=True,
    )
    requirednamed.add_argument(
        "-EU",
        "--email_user",
        type=str,
        help="Username for mail server",
        required=True,
    )
    requirednamed.add_argument(
        "-PW",
        "--email_pw",
        type=str,
        help="Password for mail server",
        required=True,
    )
    requirednamed.add_argument(
        "-TP",
        "--tso_pannumbers",
        type=str,
        help="Space separated pan numbers",
        required=True,
        nargs="+",
    )
    requirednamed.add_argument(
        "-SP",
        "--stg_pannumbers",
        type=str,
        help="Space separated pan numbers",
        required=True,
        nargs="+",
    )
    requirednamed.add_argument(
        "-CP",
        "--cp_capture_pannos",
        type=str,
        help="Synnovis Custom Panels whole capture pan numbers, space separated",
        required=True,
        nargs="+",
    )
    requirednamed.add_argument(
        "-T",
        "--testing",
        action="store_true",
        help="Test mode",
        default=False,
        required=False,
    )
    return vars(parser.parse_args())


def update_tso_config_regex(tso_pannumbers: list) -> None:
    """
    Update config TSO500 regex incorporating command-line parsed Pan numbers
    """
    logger.info(
        "Updating TSO500 regex with the following pan numbers:  %s",
        tso_pannumbers,
    )
    try:
        for filetype in [
            "gene_level_coverage",
            "exon_level_coverage",
            "results_zip",
        ]:
            config.PER_RUNTYPE_DOWNLOADS["TSO500"][filetype][
                "regex"
            ] = config.PER_RUNTYPE_DOWNLOADS["TSO500"][filetype][
                "regex"
            ].format(
                ("|").join(tso_pannumbers)
            )
    except Exception as exception:
        logger.info(
            "The following error was encountered when trying to update the"
            "TSO500 regex: %s",
            exception,
        )
        sys.exit(1)


def git_tag() -> str:
    """
    Obtain git tag from current commit
        :return stdout (str):   String containing stdout,
                                with newline characters removed
    """
    filepath = os.path.dirname(os.path.realpath(__file__))
    cmd = f"git -C {filepath} describe --tags"

    proc = subprocess.Popen(
        [cmd], stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True
    )
    out, _ = proc.communicate()
    return out.rstrip().decode("utf-8")


if __name__ == "__main__":
    args = arg_parse()

    logfile_path = os.path.join(
        os.getcwd(),
        f"{args['project_name']}.{args['project_id']}.duty_csv.log",
    )
    logger = Logger(logfile_path).logger
    logger.info("Running duty_csv %s", git_tag())

    # Read access token from environment
    try:
        token = os.environ["DX_API_TOKEN"]
        assert token
    except (AssertionError, KeyError):
        logger.error("No DNAnexus token found in environment (DX_API_TOKEN)")
        sys.exit(1)

    # Set security context of dxpy instance (and ENV just in case)
    sec_context = '{"auth_token":"' + token + '", "auth_token_type": "Bearer"}'
    os.environ["DX_SECURITY_CONTEXT"] = sec_context
    dxpy.set_security_context(json.loads(sec_context))

    # Check dxpy is authenticated
    try:
        token = os.environ["DX_API_TOKEN"]
        whoami = dxpy.api.system_whoami()
    except Exception as exception:
        logger.error(
            "Unable to authenticate with DNAnexus API: %s", str(exception)
        )
        sys.exit(1)
    else:
        logger.info("Authenticated as %s", whoami)

    # Update PER_RUNTYPE_DOWNLOADS for TSO runs with Pan number regex
    update_tso_config_regex(args["tso_pannumbers"])

    if args["testing"]:
        SCRIPT_MODE = "TEST"
    else:
        SCRIPT_MODE = "PROD"

    logger.info("Script is being run in %s mode", SCRIPT_MODE)

    GenerateOutput(
        args["project_name"],
        args["project_id"],
        args["email_user"],
        args["email_pw"],
        args["stg_pannumbers"],
        args["cp_capture_pannos"],
        SCRIPT_MODE,
    )
