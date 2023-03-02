#!/usr/bin/env python3
"""duty_csv.py

Generate DNAnexus download links for end of run processing file downloads.
Save to a .csv file.
"""
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
import argparse
import subprocess
import pandas as pd
import dxpy
import jinja2
import config
from logger import Logger
import json


# TODO make it so if it doesn't match runtypes in config, it sends an email
# saying there is nothing to process


class GenerateOutput:
    """
    Create a CSV file with download links for required files for that runtype
    that need to be placed on the trust shared drives

    CSV file is then sent over email to the config specified recipient

    A log file is created with information about the processing steps

    Methods
        get_runtype()
            String comparison with config variables to detetrmine runtype
        get_jobs()
            Find number of executions/jobs for a given project
        get_data_dicts()
            Search DNAnexus to find file data objects based on
            config-defined regexp patterns
        get_url_dataframe()
            Generate URL links from a list of data and
            produce a pandas dataframe
        get_url()
            Create a url for a file in DNAnexus
        create_csv()
            Write URLs to CSV
        generate_html()
            Create CSV and send email
        get_message_obj()
            Create message object
        send_email()
            Use smtplib to send an email
    """

    def __init__(self, project_name, project_id, email_user, email_pw):
        """
        Constructor for the GenerateOutput class
            :param project_name (str):  DNAnexus project name
            :param project_id (str):    DNAnexus project ID
            :param email_user (str):    Mail server username
            :param email_pw (str):      Mail server password
        """
        self.email_user = email_user
        self.email_pw = email_pw
        self.project_name = project_name
        self.project_id = project_id
        self.logfile_path = os.path.join(
            config.DOCUMENT_ROOT, f"{self.project_name}.duty_csv.log"
        )
        self.logger = Logger(self.logfile_path).logger
        self.logger.info("Running duty_csv %s", git_tag())
        self.runtype = self.get_runtype()
        self.logger.info(
            "Project %s is a %s runfolder",
            self.project_name,
            self.runtype,
        )
        self.project_jobs = self.get_jobs()
        self.file_dict = config.PER_RUNTYPE_DOWNLOADS[self.runtype]
        self.data_obj_dict, self.data_num_dict = self.get_data_dicts()
        self.url_dataframe = self.get_url_dataframe()
        self.csvfile_name = (
            f"{self.project_id}.{self.runtype}."
            f"{self.project_name}.duty_csv.csv"
        )
        self.csvfile_path = os.path.join(
            config.DOCUMENT_ROOT, self.csvfile_name
        )
        self.create_csv()
        self.template = jinja2.Environment(
            loader=jinja2.FileSystemLoader(config.TEMPLATE_DIR),
            autoescape=True,
        ).get_template(config.EMAIL_TEMPLATE)
        self.html = self.generate_html()
        self.email_subject = f"{self.runtype} run: {self.project_name}"
        self.email_msg = self.get_message_obj()
        # self.send_email()
        self.logger.info("Script completed")

    def get_runtype(self):
        """
        String comparison with config variables to detetrmine runtype
        """
        for runtype in config.RUNTYPE_IDENTIFIERS:
            if all(
                runtype in self.project_name
                for runtype in config.RUNTYPE_IDENTIFIERS[runtype]
            ):
                self.logger.info("This run is a %s run", runtype)
                return runtype

    def get_jobs(self):
        """
        Find number of executions/jobs for a given project
            :return project_jobs (list):    List of jobs within project
        """
        project_jobs = list(
            dxpy.bindings.search.find_executions(
                project=self.project_id, describe=True
            )
        )
        states = []
        for job in project_jobs:
            state = job.get("describe").get("state")
            states.append(state)
        self.logger.info(
            "Collected job states for project %s", self.project_name
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
            data_num = len(data_obj_dict[filetype])
            data_num_dict[filetype] = data_num
            self.logger.info(
                "The number of items for %s is %s", filetype, data_num
            )
        return data_obj_dict, data_num_dict

    def get_url_dataframe(self):
        """
        Generate URL links from a list of data and produce a pandas dataframe
            :return dataframe (tabular): Pandas dataframe containing URL links
        """
        data = []
        self.logger.info(
            "Creating urls dataframe for %s project: %s",
            self.runtype,
            self.project_name,
        )
        for filetype in self.data_obj_dict:
            for data_obj in self.data_obj_dict[filetype]:
                file_name = data_obj.get("describe").get("name")
                file_id = data_obj.get("id")
                url = self.get_url(file_id, self.project_id, file_name)
                merged_data = [
                    file_name,
                    data_obj.get("describe").get("folder"),
                    filetype,
                    url,
                ]
                data.append(merged_data)

        dataframe = pd.DataFrame(
            data, columns=["Name", "Folder", "Type", "Url"]
        )
        dataframe.sort_values(
            by=["Type", "Name"],
            inplace=True,
            ascending=True,
            ignore_index=True,
        )  # Sort values by sample name
        dataframe.index += 1  # Start sample numbering from 1
        self.logger.info(
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
        url = dxfile.get_download_url(
            duration=60 * 60 * 24 * 5,  # 60 sec x 60 min x 24 hours * 5 days
            preauthenticated=True,
            project=project_id,
            filename=file_name,
        )[0]
        return url

    def create_csv(self):
        """
        Write URLs to CSV
        """
        self.logger.info(
            "Creating csv file for %s project: %s",
            self.runtype,
            self.project_name,
        )
        self.url_dataframe.to_csv(self.csvfile_path, index=False)

        self.logger.info("CSV file has been created: %s", self.csvfile_path)

    def generate_html(self):
        """
        Create CSV and send email
            :return html (str): Rendered html as a string
        """
        files_by_filetype = ""
        for filetype in self.data_num_dict:
            files_by_filetype += (
                f"{self.data_num_dict[filetype]} " f"{filetype} files<br>"
            )

        if self.runtype == config.RUNTYPE_IDENTIFIERS["TSO500"]:
            tso_message = config.TSO_MESSAGE
        else:
            tso_message = ""

        html = self.template.render(
            TSO_message=tso_message,
            num_jobs=len(self.project_jobs),
            project_name=self.project_name,
            number_of_files=sum(self.data_num_dict.values()),
            files_by_filetype=files_by_filetype,
            git_tag=git_tag(),
        )
        self.logger.info("Generated email html for %s", self.project_name)
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

        attachment = MIMEApplication(self.url_dataframe.to_csv())
        attachment["Content-Disposition"] = (
            f"attachment; " f'filename="{self.csvfile_name}"'
        )
        msg.attach(attachment)
        self.logger.info("Created email message for %s", self.project_name)
        return msg

    def send_email(self):
        """
        Use smtplib to send an email
        """
        self.logger.info(
            "CSV file for project %s has been emailed to %s",
            self.project_name,
            config.EMAIL_RECIPIENT,
        )

        # Configure SMTP server connection for sending log messages via e-mail
        server = smtplib.SMTP(host=config.HOST, port=config.PORT, timeout=10)

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


def arg_parse():
    """
    Parse arguments supplied by the command line. Create argument parser,
    define command line arguments, then parse supplied command line arguments
    using the created argument parser
        :return (Namespace object): parsed command line attributes
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
    return vars(parser.parse_args())


def update_tso_config_regex():
    """
    Update config TSO500 regex incorporating command-line parsed Pan numbers
    """
    for filetype in [
        "gene_level_coverage",
        "exon_level_coverage",
        "results_zip",
    ]:
        config.PER_RUNTYPE_DOWNLOADS["TSO500"][filetype][
            "regex"
        ] = config.PER_RUNTYPE_DOWNLOADS["TSO500"][filetype]["regex"].format(
            ("|").join(args["tso_pannumbers"])
        )


def git_tag():
    """Obtain git tag from current commit
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
    dxpy.config["DX_USERNAME"] = os.environ["DX_USERNAME"]
    dxpy.config["DX_SECURITY_CONTEXT"] = os.environ["DX_SECURITY_CONTEXT"]
    dxpy.config["DX_WORKSPACE_ID"] = os.environ["DX_WORKSPACE_ID"]
    dxpy.config["DX_PROJECT_CONTEXT_ID"] = os.environ["DX_PROJECT_CONTEXT_ID"]
    dxpy.config["DX_APISERVER_PROTOCOL"] = os.environ["DX_APISERVER_PROTOCOL"]
    dxpy.config["DX_APISERVER_HOST"] = os.environ["DX_APISERVER_HOST"]
    dxpy.config["DX_APISERVER_PORT"] = os.environ["DX_APISERVER_PORT"]
    dxpy.set_security_context(json.loads(dxpy.config["DX_SECURITY_CONTEXT"]))

    print(dxpy.config["DX_USERNAME"])
    print(dxpy.config["DX_SECURITY_CONTEXT"])
    print(dxpy.config["DX_WORKSPACE_ID"])
    print(dxpy.config["DX_PROJECT_CONTEXT_ID"])
    print(dxpy.config["DX_APISERVER_PROTOCOL"])
    print(dxpy.config["DX_APISERVER_HOST"])
    print(dxpy.config["DX_APISERVER_PORT"])

    # TODO set DX_PROJECT_CONTEXT_ID as project_id input
    # TODO set WORKSPACE_ID

    # dxpy.set_workspace_id()

    # Update PER_RUNTYPE_DOWNLOADS for TSO runs with Pan number regex
    update_tso_config_regex(args["tso_pannumbers"])

    GenerateOutput(
        args["project_name"],
        args["project_id"],
        args["email_user"],
        args["email_pw"],
    )
