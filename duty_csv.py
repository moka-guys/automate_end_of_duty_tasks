#!/usr/bin/env python3
"""duty_csv.py

Generate DNAnexus download links for end of run processing file downloads for
run types that require file downloads, and save to a .csv file.
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
    that runfolder has files requiring download

    A log file is created with information about the processing steps

    Methods
        get_runtype()
            String comparison with config variables to determine runtype
        get_jobs()
            Find all executions/jobs for a given project
        get_data_dicts()
            Search DNAnexus to find file data objects based on
            config-defined regexp patterns
        get_url_dataframe()
            Generate URL links from a list of data and
            produce a pandas dataframe
        get_url()
            Create a url for a file in DNAnexus
        create_csv()
            Write URLs to CSV, and return CSV format as string
        get_filetype_html()
            Generate HTML for files by filetype
        get_number_of_files()
            Calculate number of files to download for project
        generate_html()
            Generate HTML
        get_message_obj()
            Create message object
        send_email()
            Use smtplib to send an email
    """

    def __init__(
        self,
        project_name,
        project_id,
        email_user,
        email_pw,
        stg_pannumbers,
        mode,
    ):
        """
        Constructor for the GenerateOutput class
            :param project_name (str):      DNAnexus project name
            :param project_id (str):        DNAnexus project ID
            :param email_user (str):        Mail server username
            :param email_pw (str):          Mail server password
            :param stg_pannumbers (list):   List of St George's pan numbers
            :mode (str):                    Script mode ("TEST" or "PROD")
        """
        self.email_user = email_user
        self.email_pw = email_pw
        self.stg_pannumbers = stg_pannumbers
        self.script_mode = mode
        self.project_name = project_name
        self.project_id = project_id
        self.runtype = self.get_runtype()
        logger.info(
            "Project %s is a %s runfolder",
            self.project_name,
            self.runtype,
        )
        self.project_jobs = self.get_jobs()
        self.csvfile_name = (
            f"{self.project_id}.{self.runtype}."
            f"{self.project_name}.duty_csv.csv"
        )
        self.htmlfile_name = (
            f"{self.project_id}.{self.runtype}."
            f"{self.project_name}.duty_csv.html"
        )
        self.csvfile_path = os.path.join(
            config.DOCUMENT_ROOT, self.csvfile_name
        )
        self.htmlfile_path = os.path.join(
            config.DOCUMENT_ROOT, self.htmlfile_name
        )
        self.template = jinja2.Environment(
            loader=jinja2.FileSystemLoader(config.TEMPLATE_DIR),
            autoescape=True,
        ).get_template(config.EMAIL_TEMPLATE)

        if self.runtype:
            self.file_dict = config.PER_RUNTYPE_DOWNLOADS[self.runtype]
            self.email_subject = config.EMAIL_SUBJECT[self.script_mode].format(
                self.runtype, self.project_name
            )
            # If the runfolder has files that need download
            if self.file_dict:
                logger.info("The run has files requiring download")
                self.data_obj_dict, self.data_num_dict = self.get_data_dicts()
                self.url_dataframe = self.get_url_dataframe()
                self.csv_contents = self.create_csv()
                self.filetype_html = self.get_filetype_html()
                self.number_of_files = self.get_number_of_files()
            else:
                logger.info("The run has no files requiring download")
                (
                    self.data_obj_dict,
                    self.data_num_dict,
                    self.url_dataframe,
                    self.csv_contents,
                    self.filetype_html,
                    self.number_of_files,
                ) = (False, False, False, False, None, 0)
            self.html = self.generate_html()
            self.email_msg = self.get_message_obj()
            self.send_email()
        else:
            logger.error("Script halted due to absence of runtype")
        logger.info("Script completed")

    def get_runtype(self):
        """
        String comparison with config variables to detetrmine runtype
            :return runtype (str, None):    Runtype string, or none if
                                            cannot be parsed
        """
        for runtype in config.RUNTYPE_IDENTIFIERS:
            if all(
                runtype in self.project_name
                for runtype in config.RUNTYPE_IDENTIFIERS[runtype]
            ):
                logger.info("This run is a %s run", runtype)
                return runtype
            else:
                logger.error("Unable to determine runtype for this run")
                return None

    def get_jobs(self):
        """
        Find all executions/jobs for a given project
            :return project_jobs (list):    List of jobs within project
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
            logger.info("Jobs were identified in the DNAnexus project")
        except Exception as exception:
            logger.error(
                "There was a problem identifying jobs in the DNAnexus project"
            )
        return project_jobs

    def get_data_dicts(self):
        """
        Search DNAnexus to find file data objects based on
        config-defined regexp patterns
            :return data_obj_dict:  Dictionary of data objects for use in
                                    downloading files
            :return data_num_dict:  Dictionary of number of data objects per
                                    file type
        """
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
        return data_obj_dict, data_num_dict

    def get_url_dataframe(self):
        """
        Generate URL links from a list of data and produce a pandas dataframe
            :return dataframe (tabular): Pandas dataframe containing URL links
        """
        data = []
        logger.info(
            "Creating urls dataframe for %s project: %s",
            self.runtype,
            self.project_name,
        )
        for filetype in self.data_obj_dict:
            for data_obj in self.data_obj_dict[filetype]:
                file_name = data_obj.get("describe").get("name")
                file_id = data_obj.get("id")
                url = self.get_url(file_id, self.project_id, file_name)
                gstt_dir = [
                    config.GSTT_PATHS[self.script_mode][self.runtype][
                        filetype
                    ]["Via"]
                ]
                if any(pannumber in url for pannumber in self.stg_pannumbers):
                    gstt_dir.append(
                        config.GSTT_PATHS[self.script_mode][self.runtype][
                            filetype
                        ]["StG"]
                    )

                merged_data = [
                    file_name,
                    data_obj.get("describe").get("folder"),
                    filetype,
                    url,
                    gstt_dir,
                ]
                data.append(merged_data)

        dataframe = pd.DataFrame(
            data,
            columns=config.COLS,
        )
        dataframe.sort_values(
            by=["Type", "Name"],
            inplace=True,
            ascending=True,
            ignore_index=True,
        )  # Sort values by sample name
        dataframe.index += 1  # Start sample numbering from 1
        logger.info(
            "Created urls dataframe for %s project: %s",
            self.runtype,
            self.project_name,
        )

        return dataframe

    def get_url(self, file_id, project_id, file_name):
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
        except Exception as exception:
            logger.error(
                "Could not retrieve url for file %s, with exception: %s",
                dxfile,
                exception,
            )
        return url

    def create_csv(self):
        """
        Write URLs to CSV, and return CSV format as string
            :return csv_contents (str): Return resulting CSV format as string
        """
        logger.info(
            "Creating csv file for %s project: %s",
            self.runtype,
            self.project_name,
        )
        # Write to file
        self.url_dataframe.to_csv(self.csvfile_path, index=False)
        # Save as variable
        csv_contents = self.url_dataframe.to_csv(index=False)

        logger.info("CSV file has been created: %s", self.csvfile_path)
        return csv_contents

    def get_filetype_html(self):
        """
        Generate HTML for files by filetype
            :return filetype_html (str):    Html string
        """
        filetype_html = ""
        try:
            for filetype in self.data_num_dict:
                filetype_html += (
                    f"{self.data_num_dict[filetype]} " f"{filetype} files<br>"
                )
            logger.info("Filetype HTML successfully generated")
        except Exception as exception:
            logger.error(
                "There was an exception when generating the filetype html: %s",
                exception,
            )
        return filetype_html

    def get_number_of_files(self):
        """
        Calculate number of files to download for project
            :return number_of_files (int):      Number of files

        """
        if self.data_num_dict:
            number_of_files = sum(self.data_num_dict.values())
            logger.info(
                "%s files were identified for download for this project",
                number_of_files,
            )
        logger.error("No files were identified for download for this project")
        return number_of_files

    def generate_html(self):
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
        except Exception as exception:
            logger.error(
                "There was a problem generating the html file, with "
                "the following exception: %s",
                exception,
            )

        return html

    def get_message_obj(self):
        """
        Create message object
            :return msg (object): Message object for email
        """
        msg = MIMEMultipart()
        # Both header types for maximum compatibility
        msg["X-Priority"] = "1"
        msg["X-MSMail-Priority"] = "High"
        msg["Subject"] = self.email_subject
        msg["From"] = config.EMAIL_SENDER
        msg["To"] = config.EMAIL_RECIPIENT
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

    def send_email(self):
        """
        Use smtplib to send an email
        """
        try:
            # Configure SMTP server connection for sending log messages via e-mail
            server = smtplib.SMTP(
                host=config.HOST, port=config.PORT, timeout=10
            )

            # Verbosity turned off - set to true to get debug messages
            server.set_debuglevel(False)
            server.starttls()  # Encrypt SMTP commands using TLS
            server.ehlo()  # Identify client to ESMTP server using EHLO commands
            # Login to server with user credentials
            server.login(self.email_user, self.email_pw)
            server.sendmail(
                config.EMAIL_SENDER,
                config.EMAIL_RECIPIENT,
                self.email_msg.as_string(),
            )
            logger.info(
                "CSV file has been emailed to %s",
                config.EMAIL_RECIPIENT,
            )
        except Exception as exception:
            logger.error(
                "There was a problem sending the email, with "
                "the following exception: %s",
                exception,
            )


def arg_parse():
    """
    Parse arguments supplied by the command line. Create argument parser,
    define command line arguments, then parse supplied command line arguments
    using the created argument parser
        :return (Namespace object): Parsed command line attributes
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
        "-T",
        "--testing",
        type=bool,
        help="Test mode, True or False",
        required=True,
    )
    return vars(parser.parse_args())


def update_tso_config_regex(tso_pannumbers):
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


def git_tag():
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
        config.DOCUMENT_ROOT, f"{args['project_name']}.duty_csv.log"
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
    except Exception as e:
        logger.error("Unable to authenticate with DNAnexus API: %s", str(e))
        sys.exit(1)
    else:
        logger.info("Authenticated as %s", whoami)

    # Update PER_RUNTYPE_DOWNLOADS for TSO runs with Pan number regex
    update_tso_config_regex(args["tso_pannumbers"])

    if args["testing"]:
        SCRIPT_MODE = "TEST"
    else:
        SCRIPT_MODE = "PROD"

    logger.info("Script is being run in  %s mode", SCRIPT_MODE)

    GenerateOutput(
        args["project_name"],
        args["project_id"],
        args["email_user"],
        args["email_pw"],
        args["stg_pannumbers"],
        SCRIPT_MODE,
    )
