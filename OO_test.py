from pydoc import describe
import dxpy
import pandas as pd
from DNAnexus_auth_token import token
import requests
import re
import sys, os
import datetime
import time
import config
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from jinja2 import Environment, PackageLoader, select_autoescape, FileSystemLoader
from mokaguys_logger import log_setup, logging

"""
Automate End of Duty Tasks
Python 3
"""

dxpy.set_security_context({"auth_token_type": "Bearer", "auth_token": token})

cur_path = os.getcwd()
pattern = re.compile("(project-\S+)__")
env = Environment(
    loader=FileSystemLoader("email_templates"),
    autoescape=select_autoescape(["html"])
)
template = env.get_template("email.html")
python3 = "S:\Genetics_Data2\Array\Software\Python-3.6.5\python"

LOG_FILENAME = datetime.datetime.now().strftime('%d_%m_%Y_%H_%M_%S_automate_duty_tasks.log')

log_setup(cur_path + '/LOG/' + LOG_FILENAME)
log = logging.getLogger(datetime.datetime.now().strftime('log_%d/%m/%Y_%H:%M:%S'))
log.info("test")
log = logging.getLogger(datetime.datetime.now().strftime('log_%d/%m/%Y_%H:%M:%S'))
log.info("test2")

def download(url: str, dest_folder: str):
    """
    Download function for Clinvar vcf files if not already present
    """
    if not os.path.exists(dest_folder):
        os.makedirs(dest_folder)  # create folder if it does not exist
    #
    filename = url.split("/")[-1].replace(" ", "_")  # be careful with file names
    file_path = os.path.join(dest_folder, filename)
    #
    r = requests.get(url, stream=True)
    if r.ok:
        print("saving to", os.path.abspath(file_path))
        with open(file_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 8):
                if chunk:
                    f.write(chunk)
                    f.flush()
                    os.fsync(f.fileno())
    else:  # HTTP status code 4XX/5XX
        print("Download failed: status code {}\n{}".format(r.status_code, r.text))


# generate download link for DNAnexus object
def download_url(file_ID, project_ID):
    dxfile = dxpy.DXFile(file_ID)
    download_link = dxfile.get_download_url(
        duration=82800,
        preauthenticated=True,
        project=project_ID,
    )
    return download_link[0]


# find data based on the name of the file
def find_project_data(project_id, _folder, filename):
    data = list(
        dxpy.bindings.search.find_data_objects(
            project=project_id, name=filename, name_mode="regexp", describe=True, folder=_folder
        )
    )
    return data


# find data based on the name of the file
def find_projects(project_name, _length):
    data = list(
        dxpy.bindings.search.find_projects(
            name=project_name,
            name_mode="regexp",
            created_after=_length,
            level="VIEW",
            describe=True,
        )
    )
    return data


def find_project_executions(project_id):
    data = list(
        dxpy.bindings.search.find_executions(
            project=project_id, 
            describe=True
            )
        )
    jobs = []
    for job in data:
        state = job.get("describe").get("state")
        jobs.append(state)
    _jobs = list(set(jobs))
    len(data)
    return _jobs, len(data)


def create_download_links(project_data):
    data = []
    for object in project_data:
        file_name = object.get("describe").get("name")
        folder = object.get("describe").get("folder")
        object_id = object.get("id")
        project_id = object.get("project")
        url = download_url(object_id, project_id) + "/" + file_name
        merged_data = [file_name, folder, project_id, object_id, url]
        data.append(merged_data)
    return pd.DataFrame(
        data, columns=["name", "folder", "project_id", "file_id", "url"]
    )


def download_SNP_vcfs(df):
    for i in range(0, len(df)):
        download(
            df["url"][i],
            dest_folder="/media/igor/B08E-849B/home/automate_end_of_run_tasks/SNP",
        )

# find project name using unique project id
def find_project_name(project_id):
    project_data = dxpy.bindings.dxproject.DXProject(dxid=project_id)
    return project_data.describe().get("name")

def find_project_description(project_id):
    project_data = dxpy.bindings.dxproject.DXProject(dxid=project_id)
    return project_data.describe()


def download_NGS_coverage(df):
    for i in range(0, len(df)):
        download(
            df["url"][i],
            dest_folder="/media/igor/B08E-849B/home/automate_end_of_run_tasks/NGS_coverage",
        )

def archive_after7days(folder):
    today = datetime.date.today()
    for filename in os.listdir(cur_path+folder):
        project = pattern.search(filename)[1]
        date_modified = datetime.date.fromtimestamp(find_project_description(project).get("modified")/1000)
        _delta = today - date_modified
        print("number of days modified from now: {}".format(_delta.days))
        if _delta.days > 7:
            os.replace(cur_path+folder+"/"+filename, cur_path+folder+"/archive/"+filename)

def find_previouse_files(folder):
    projects_csv = {}
    for filename in os.listdir(cur_path+folder):
        project = pattern.search(filename)[1]
        projects_csv[project]={}
    return projects_csv

def send_email(to, email_subject, email_message):
    """
    Input = email address, email_subject, email_message, email_priority (optional, default = standard priority)
    Uses smtplib to send an email. 
    Returns = None
    """
    # create message object
    #m = Message()
    m = MIMEMultipart()
    # set priority
    #m["X-Priority"] = str(email_priority)
    # set subject
    m["Subject"] = email_subject
    # set body
    m["From"] = config.me
    m["To"] = to
    msgText = MIMEText("<b>%s</b>" % (email_message), "html")
    m.attach(msgText)
    #m.set_payload(email_message)
    # server details
    server = smtplib.SMTP(host=config.host, port=config.port, timeout=10)
    server.set_debuglevel(False)  # verbosity turned off - set to true to get debug messages
    server.starttls()
    server.ehlo()
    server.login(config.user, config.pw)
    server.sendmail(config.me, to, m.as_string())
    # write to logfile
    log.info(
        "UA_pass Email sent to {}. Subject {}".format(
            to, email_subject
        )
    )


class Projects:
    def __init__(self, proj_type, pattern, length):
        self.type = proj_type #SNP, WES, MokaPipe or TSO500
        self.data = find_projects(pattern, length)
        self.time = length

    def find_previouse_files(folder):
        projects_csv = {}
        files = (file for file in os.listdir(cur_path+folder) 
            if os.path.isfile(os.path.join(cur_path+folder, file)))
        for filename in files:
            project = pattern.search(filename)[1]
            projects_csv[project]={}
        return projects_csv

    def no_projects_found(self, proj_type):
        message = f"no { proj_type } projects were found in time frame specified: { self.time }"
        print(message)
        log = logging.getLogger(datetime.datetime.now().strftime('log_%d/%m/%Y_%H:%M:%S'))
        log.info(message)
        return message


class Project:
    def __init__(self, proj):
        self.id = proj.get("id")
        self.name = proj.get("describe").get("name")
        self.jobs = find_project_executions(proj.get("id"))

    def message1(self):
        message = f"csv file for this project already created: { self.name }"
        print(message)
        log = logging.getLogger(datetime.datetime.now().strftime('log_%d/%m/%Y_%H:%M:%S'))
        log.info(message)
        return message
    
    def message2(self, proj_type):
        message = f"one or more jobs are running for { proj_type } project: { self.name }"
        print(message)
        log = logging.getLogger(datetime.datetime.now().strftime('log_%d/%m/%Y_%H:%M:%S'))
        log.info(message)
        return message

    def message3(self, proj_type):
        message = f"no files were found for { proj_type } project: { self.name }"
        print(message)
        log = logging.getLogger(datetime.datetime.now().strftime('log_%d/%m/%Y_%H:%M:%S'))
        log.info(message)
        return message

        

class WES(Project):
    proj_type = "WES"
    folder = "/WES/"
    def data(self):
        data = find_project_data(self.id,"/coverage", "\S+.chanjo_txt$") 
        return data
    def make_csv_and_email(self, list):
        download_links = create_download_links(list)
        filepath = cur_path + self.folder + self.id + "__"+  self.name + "_chanjo_txt.csv"
        download_links.to_csv(filepath, index=False, sep=",")
        subject = "WES run: " + self.name
        text = python3 + " H:\\Tickets\\scripts\\process_WES.py " + filepath
        html = template.render(copy_text=text)
        send_email(config.test, subject, html)
        log = logging.getLogger(datetime.datetime.now().strftime('log_%d/%m/%Y_%H:%M:%S'))
        log.info(f"CSV file(s) generated succesffully and email sent to { config.test } for project: { self.name }")

class SNP(Project):
    proj_type = "SNP"
    folder = "/SNP/"
    def data(self):
        data = find_project_data(self.id, "/Output", "\S+.sites_present_reheader_filtered_normalised.vcf$")
        print(data)
        return data
    def make_csv_and_email(self, list):
        download_links = create_download_links(list)
        filepath = cur_path + self.folder  + self.id + "__"+  self.name + "_VCFs.csv"
        download_links.to_csv(filepath, index=False, sep=",")
        subject = "SNP run: " + self.name
        text = python3 + " H:\\Tickets\\scripts\\process_SNP.py " + filepath
        html = template.render(copy_text=text)
        send_email(config.test, subject, html)
        log = logging.getLogger(datetime.datetime.now().strftime('log_%d/%m/%Y_%H:%M:%S'))
        log.info(f"CSV file(s) generated succesffully and email sent to { config.test } for project: { self.name }")


class MokaPipe(Project):
    proj_type = "MokaPipe"
    folder = "/MokaPipe/"
    def data(self):
        coverage = find_project_data(self.id, "/coverage", "\S+.exon_level.txt$")
        rpkm = find_project_data(self.id, "/conifer_output","combined_bed_summary\S+")
        return [rpkm, coverage]
    def make_csv_and_email(self, list):
        rpkm  = list[0]
        coverage = list[1]
        download_RPKM_links = create_download_links(rpkm)
        download_coverage_links = create_download_links(coverage)
        RPKM_filepath = cur_path + self.folder  + self.id + "__"+  self.name + "_RPKM.csv"
        coverage_filepath = cur_path + self.folder  +  self.id + "__" + self.name + "_Coverage.csv"
        download_RPKM_links.to_csv(RPKM_filepath, index=False, sep=",")
        download_coverage_links.to_csv(coverage_filepath, index=False, sep=",")
        subject = "TSO500 run: " + self.name
        text = python3 + " H:\\Tickets\\scripts\\process_TSO.py " + RPKM_filepath + " " + coverage_filepath
        html = template.render(copy_text=text)
        send_email(config.test, subject, html)
        log = logging.getLogger(datetime.datetime.now().strftime('log_%d/%m/%Y_%H:%M:%S'))
        log.info(f"CSV file(s) generated succesffully and email sent to { config.test } for project: { self.name }")

class TSO(Project):
    proj_type = "TSO500"
    folder = "/TSO500/"
    def data(self):
        gene = find_project_data(self.id, "/coverage", "\S+.gene_level.txt$")
        exon = find_project_data(self.id, "/coverage", "\S+.exon_level.txt$")
        results = find_project_data(self.id, "/","^Results.zip$")
        return [results, gene+exon]
    def make_csv_and_email(self, list):
        results  = list[0]
        coverage = list[1]
        download_results_links = create_download_links(results)
        download_coverage_links = create_download_links(coverage)
        results_filepath = cur_path + self.folder  + self.id + "__"+ self.name + "_Results.csv"
        coverage_filepath = cur_path + self.folder  +  self.id + "__" + self.name + "_Coverage.csv"
        download_results_links.to_csv(results_filepath, index=False, sep=",")
        download_coverage_links.to_csv(coverage_filepath, index=False, sep=",")
        subject = "TSO500 run: " + self.name
        text = python3 + " H:\\Tickets\\scripts\\process_TSO.py " + results_filepath + " " + coverage_filepath
        html = template.render(copy_text=text)
        send_email(config.test, subject, html)
        log.info(f"CSV file(s) generated succesffully and email sent to { config.test } for project: { self.name }")


if __name__ == "__main__":

    """
    Key:
    “s”, “m”, “d”, “w”, or “y” (for seconds, minutes, days, weeks, or years)
    """

    length = "-7d"


    patterns = { 
                "/WES": "002_[2-5]\d+_\S+WES", 
                "/MokaPipe" : "002_[2-5]\d+_\S+NGS", 
                "/SNP" : "002_[2-5]\d+_\S+SNP", 
                "/TSO500" : "002_[2-5]\d+_\S+TSO"
                }

    for proj_type in patterns:
        projects = Projects(proj_type,patterns[proj_type],length) 
        print(f"the project is: { proj_type }") 
        if projects.data:
            prev_proj_csv = Projects.find_previouse_files(proj_type)
            print(prev_proj_csv)
            for item in projects.data:
                if proj_type == "/SNP":
                    project = SNP(item)
                elif proj_type == "/WES":
                    project = WES(item)
                elif proj_type == "/MokaPipe":
                    project = MokaPipe(item)  
                elif proj_type == "/TSO500":
                    project = TSO(item)   
                else:
                    print(f"file job not recognised: { proj_type }")
                print(f"{project.id}, { project.name }, { project.jobs}") 
                if project.id in prev_proj_csv:
                    project.message1()
                else:
                    if "running" not in project.jobs and "done" in project.jobs[0]:
                        project_data = project.data()
                        if project_data:
                            project.make_csv_and_email(project_data)
                        else: 
                            project.message3()
                    if "running" in project.jobs:
                        project.message2()
        else:
            projects.no_projects_found(proj_type)            
    archive_after7days

