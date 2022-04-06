from pydoc import describe
import dxpy
import pandas as pd
from DNAnexus_auth_token import token
import requests
import re
import sys, os

'''
Automate End of Run Tasks
Python 3
'''

dxpy.set_security_context({"auth_token_type": "Bearer", "auth_token": token})

def download(url: str, dest_folder: str):
    '''
    Download function for Clinvar vcf files if not already present
    '''
    if not os.path.exists(dest_folder):
        os.makedirs(dest_folder)  # create folder if it does not exist
    #
    filename = url.split('/')[-1].replace(" ", "_")  # be careful with file names
    file_path = os.path.join(dest_folder, filename)
    #
    r = requests.get(url, stream=True)
    if r.ok:
        print("saving to", os.path.abspath(file_path))
        with open(file_path, 'wb') as f:
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
def find_project_data(project_id, filename):
    data = list(
        dxpy.bindings.search.find_data_objects(
           project=project_id, name=filename, name_mode="regexp", describe=True
        )
    )
    return data

# find data based on the name of the file
def find_projects(project_name, _length):
    data = list(
        dxpy.bindings.search.find_projects(
            name=project_name, name_mode="glob", created_after=_length, level='VIEW', describe=True
        )
    )
    return data

def create_download_links(project_data):
    data = []
    for object in project_data:
        file_name = object.get("describe").get("name")
        folder = object.get("describe").get("folder")
        object_id = object.get("id")
        project_id = object.get("project")
        url = download_url(object_id, project_id)+ "/" + file_name
        merged_data = [file_name, folder, project_id, object_id, url]
        data.append(merged_data)
    return pd.DataFrame(data, columns=["name", "folder", "project_id", "file_id", "url"])

def download_SNP_vcfs(df):
    for i in range(0, len(df)):
        download(df['url'][i], dest_folder='/media/igor/B08E-849B/home/automate_end_of_run_tasks/links')
    

'''
Key:
 “s”, “m”, “d”, “w”, or “y” (for seconds, minutes, days, weeks, or years)
'''
if __name__=="__main__":
    project = find_projects('*SNP*', '-10d')
    project_data = find_project_data(project[0].get('id'), '\S+.sites_present_reheader_filtered_normalised.vcf$')
    download_links = create_download_links(project_data)
    download_links.to_csv("links.csv", index=False, sep=",")
    download_SNP_vcfs(download_links)

