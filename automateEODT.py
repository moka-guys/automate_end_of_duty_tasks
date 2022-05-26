import dxpy
import pandas as pd
from DNAnexus_auth_token import token
import re
import os
import sys
import datetime
import config
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from jinja2 import Environment, select_autoescape, FileSystemLoader
from mokaguys_logger import log_setup, logging
from tqdm import tqdm
from my_proxy_smtplib import ProxySMTP
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
python3 = "S:\\Genetics_Data2\\Array\\Software\\Python-3.6.5\\python"
duty_bio_scripts = "S:\\Genetics_Data2\\Array\\Software\\duty_bioinformatician_scripts"

LOG_FILENAME = datetime.datetime.now().strftime('%d_%m_%Y_%H_%M_%S_automate_duty_tasks.log')

log_setup(cur_path + '/LOG/' + LOG_FILENAME)


def download_url(file_ID, project_ID):
    '''
    Create a url for a file in DNAnexus
    '''
    dxfile = dxpy.DXFile(file_ID)
    download_link = dxfile.get_download_url(
        duration=60*60*24*5, # 60 sec x 60 min x 24 hours * 5 days 
        preauthenticated=True,
        project=project_ID,
    )
    return download_link[0]

def find_project_data(project_id, _folder, filename):
    '''
    Search DNAnexus to find files based on a regexp pattern
    '''
    data = list(
        dxpy.bindings.search.find_data_objects(
            project=project_id, name=filename, name_mode="regexp", describe=True, folder=_folder
        )
    )
    return data

def find_projects(project_name, _length):
    '''
    Search DNAnexus to find projects based on regex pattern and amount of time from now
    '''
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
    '''
    Find number of executions/jobs for a given project and retrieve outcomes of the jobs e.g. done, running, failed etc.
    '''
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
    '''
    Generate URL links from a list of data and produce a pandas dataframe
    '''
    data = []
    for object in tqdm(project_data):
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

def find_project_name(project_id):
    '''
    Find the name of a project using the project id
    '''
    project_data = dxpy.bindings.dxproject.DXProject(dxid=project_id)
    return project_data.describe().get("name")

def find_project_description(project_id):
    '''
    Find the description of the project
    '''
    project_data = dxpy.bindings.dxproject.DXProject(dxid=project_id)
    return project_data.describe()

def find_previouse_files(folder):
    '''
    Find previously generates CSV files to determine if the project needs processing
    '''
    projects_csv = {}
    for filename in os.listdir(cur_path+folder):
        try:
            project = pattern.search(filename)[1]
        except:
            project = ''
        projects_csv[project]={}
    return projects_csv

def archive_after7days(folder):
    '''
    Archive CSV after seven days
    '''
    today = datetime.date.today()
    files = (file for file in os.listdir(cur_path+folder) 
        if os.path.isfile(os.path.join(cur_path+folder, file)))
    for filename in files:
        try:
            project = pattern.search(filename)[1]
            date_modified = datetime.date.fromtimestamp(find_project_description(project).get("modified")/1000)
            _delta = today - date_modified
            print("number of days modified from now: {}".format(_delta.days))
            if _delta.days > 7:
                os.replace(cur_path+folder+"/"+filename, cur_path+folder+"/archive/"+filename)
        except:
            project = ''

def send_email(to, email_subject, email_message):
    """
    Input = email address, email_subject, email_message, email_priority (optional, default = standard priority)
    Uses smtplib to send an email. 
    Returns = None
    """
    # create message object
    #m = Message()
    email_content = MIMEMultipart()
    # set priority
    #m["X-Priority"] = str(email_priority)
    # set subject
    email_content["Subject"] = email_subject
    # set body
    email_content["From"] = config.me
    email_content["To"] = to
    msgText = MIMEText("<b>%s</b>" % (email_message), "html")
    email_content.attach(msgText)
    #m.set_payload(email_message)
    # server details
    server = smtplib.SMTP(host=config.host, port=config.port, timeout=10)
    server.set_debuglevel(False)  # verbosity turned off - set to true to get debug messages
    server.starttls() # notifies a mail server that the contents of an email need to be encrypted
    server.ehlo() #Identify yourself to an ESMTP server using EHLO
    #server.login(config.user, config.pw)
    server.sendmail(config.me, to, email_content.as_string())

class Projects:
    '''
    Create a class for Projects
    '''
    def __init__(self, proj_type, pattern, length):
        self.type = proj_type #SNP, WES, MokaPipe or TSO500
        self.data = find_projects(pattern, length)
        self.time = length

    def no_projects_found(self, proj_type):
        '''
        Log message that NO projects have been found in the time frame specified
        '''
        message = f"NO { proj_type } projects were found in time frame specified: { self.time }"
        print(message)
        log = logging.getLogger(datetime.datetime.now().strftime('log_%d/%m/%Y_%H:%M:%S'))
        log.info(message)
        return message

class Project:
    '''
    Create a Class for One Project
    '''
    def __init__(self, proj):
        self.id = proj.get("id")
        self.name = proj.get("describe").get("name")
        self.jobs = find_project_executions(proj.get("id"))
        self.project_name = find_project_name(proj.get("id"))

    def message1(self):
        '''
        Log message that the project has been previously porcessed
        '''
        message = f"csv file for this project already created: { self.name }"
        print(message)
        log = logging.getLogger(datetime.datetime.now().strftime('log_%d/%m/%Y_%H:%M:%S'))
        log.info(message)
        return message
    
    def message2(self, proj_type):
        '''
        Log message that one or more projects are running
        '''
        message = f"one or more jobs are running for { proj_type } project: { self.name }"
        print(message)
        log = logging.getLogger(datetime.datetime.now().strftime('log_%d/%m/%Y_%H:%M:%S'))
        log.info(message)
        return message

    def message3(self, proj_type):
        '''
        Log message that no target files have been found for a specific project
        '''
        message = f"no files were found for { proj_type } project: { self.name }"
        print(message)
        log = logging.getLogger(datetime.datetime.now().strftime('log_%d/%m/%Y_%H:%M:%S'))
        log.info(message)
        return message

        
# WES Project
class WES(Project):
    '''
    Class for WES Project that inherits information from Project
    '''
    proj_type = "WES"
    folder = "/WES/"
    def data(self):
        '''
        Find files in the project that are required to be placed on the trust computer:
        chanjo_txt
        '''
        data = find_project_data(self.id,"/coverage", "\S+.chanjo_txt$") 
        return data
    def make_csv_and_email(self, list):
        '''
        Create CSV and send email
        '''
        download_links = create_download_links(list)
        filepath = cur_path + self.folder + self.id + "__"+  self.name + "_chanjo_txt.csv"
        download_links.to_csv(filepath, index=False, sep=",")
        subject = "WES run: " + self.name
        text = python3 + " " + duty_bio_scripts +"\\process_WES.py " + filepath
        html = template.render(copy_text=text, num_jobs=self.jobs[1], jobs_executed=self.jobs[0], project_name = self.project_name)
        send_email(config.test, subject, html)
        log = logging.getLogger(datetime.datetime.now().strftime('log_%d/%m/%Y_%H:%M:%S'))
        log.info(f"CSV file(s) generated succesffully and email sent to { config.test } for project: { self.name }")

class SNP(Project):
    '''
    Class for SNP Project that inherits information from Project
    '''
    proj_type = "SNP"
    folder = "/SNP/"
    def data(self):
        '''
        Find files in the project that are required to be placed on the trust computer:
        sites_present_reheader_filtered_normalised.vcf
        '''
        data = find_project_data(self.id, "/Output", "\S+.sites_present_reheader_filtered_normalised.vcf$")
        return data
    def make_csv_and_email(self, list):
        download_links = create_download_links(list)
        filepath = cur_path + self.folder  + self.id + "__"+  self.name + "_VCFs.csv"
        download_links.to_csv(filepath, index=False, sep=",")
        subject = "SNP run: " + self.name
        text = python3+ " " + duty_bio_scripts +"\\process_SNP.py " + filepath
        html = template.render(copy_text=text, num_jobs=self.jobs[1], jobs_executed=self.jobs[0], project_name = self.project_name)
        send_email(config.test, subject, html)
        log = logging.getLogger(datetime.datetime.now().strftime('log_%d/%m/%Y_%H:%M:%S'))
        log.info(f"CSV file(s) generated succesffully and email sent to { config.test } for project: { self.name }")

class MokaPipe(Project):
    '''
    Class for MokaPipe Project that inherits information from Project
    '''
    proj_type = "MokaPipe"
    folder = "/MokaPipe/"
    def data(self):
        '''
        Find files in the project that are required to be placed on the trust computer:
        exon_level.txt
        combined_bed_summary
        '''
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
        text = python3 + " " + duty_bio_scripts +"\\process_MokaPipe.py " + RPKM_filepath + " " + coverage_filepath
        html = template.render(copy_text=text, num_jobs=self.jobs[1], jobs_executed=self.jobs[0], project_name = self.project_name)
        send_email(config.test, subject, html)
        log = logging.getLogger(datetime.datetime.now().strftime('log_%d/%m/%Y_%H:%M:%S'))
        log.info(f"CSV file(s) generated succesffully and email sent to { config.test } for project: { self.name }")

class TSO(Project):
    '''
    Class for TSO500 Project that inherits information from Project
    '''
    proj_type = "TSO500"
    folder = "/TSO500/"
    def data(self):
        '''
        Find files in the project that are required to be placed on the trust computer:
        gene_level.txt
        exon_level.txt
        Results.zip
        '''
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
        text = python3 + " " + duty_bio_scripts +"\\process_TSO.py " + results_filepath + " " + coverage_filepath
        html = template.render(copy_text=text, num_jobs=self.jobs[1], jobs_executed=self.jobs[0], project_name = self.project_name)
        send_email(config.test, subject, html)
        log = logging.getLogger(datetime.datetime.now().strftime('log_%d/%m/%Y_%H:%M:%S'))
        log.info(f"CSV file(s) generated succesffully and email sent to { config.test } for project: { self.name }")


if __name__ == "__main__":
    """
    Key for length:
    “s”, “m”, “d”, “w”, or “y” (for seconds, minutes, days, weeks, or years)
    """
    length = sys.argv[1] #searches projects created within the last seven days

    patterns = { 
                "/WES": "002_[2-5]\d+_\S+WES", 
                "/MokaPipe" : "002_[2-5]\d+_\S+NGS", 
                "/SNP" : "002_[2-5]\d+_\S+SNP", 
                "/TSO500" : "002_[2-5]\d+_\S+TSO"
                }

    '''
    Search WES, MokaPipe, SNP and TSO500 projects using the patterns shown in the dictionary of 'patterns' 
    for projects created in the last seven days 

    If projects are found a csv file is created with download links for the required files 
    that need to be placed onto the trsut drives

    The script also checks if the csv files have already been generated and skips generating new files if that is the case

    The script also checks if the projects for the csv files are older than 7 days, if that is the case
    they are moved to the archived folder.

    Variouse steps are logged to a text file
    '''
    for proj_type in patterns:
        projects = Projects(proj_type,patterns[proj_type],length) 
        print(f"the project is: { proj_type }") 
        if projects.data:
            prev_proj_csv = find_previouse_files(proj_type)
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
                print(f"Project_id: {project.id}, Project_name: { project.name }, Project_jobs_status: { project.jobs}") 
                log = logging.getLogger(datetime.datetime.now().strftime('log_%d/%m/%Y_%H:%M:%S'))
                log.info(f"Project_id: {project.id}, Project_name: { project.name }, Project_jobs_status: { project.jobs}")
                if project.id in prev_proj_csv:
                    project.message1()
                else:
                    print(f'project id: {project.id} and prev_proj_csc: {prev_proj_csv}')
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
    archive_after7days("/SNP")
    archive_after7days("/MokaPipe")
    archive_after7days("/TSO500")
    archive_after7days("/WES")
    log = logging.getLogger(datetime.datetime.now().strftime('log_%d/%m/%Y_%H:%M:%S'))
    log.info(f"Script finished running!")