# Automate End of Duty Tasks

The script searches the DNAnexus for recently created production projects '002_' and generates download links that are saved to a .csv file. 

An email is sent to the Duty Bioinformatican with instruction of how to download the files to the appropriate locations on the GST-Trust network. 

The script supports the following projects:
### WES
### TSO500
### SNP
### MokaPipe

## Deployment

The script runs on the Genapp test server. To depploy the scrip please use the ansible-playbook:
[automate_end_of_duty_tasks.yml]()
on the Genapp Test Server go to the deployment directory:
'''xml
cd /home/mokaguys/code/deployment
'''
Run the ansible playbook:
'''xml
ansible-playbook playbooks/automate_end_of_duty_tasks.yml
'''
The variables are located here:
'''xml
/home/mokaguys/code/deployment/playbooks/vars/automate_end_of_duty_tasks.yml
'''

## Running on Trust Network

The script is set up to search for DNAnexus projects created in the previous 7 days.\ 

The email containting csv attachment is send to mokaguys (gst-tr.mokaguys@nhs.net)\

The duty Bioinfromatician has not save the csv file(s) to the following location:\
'''xml
P:\Bioinformatics\Duty_Bioinformatics_CSV
'''
Open powershell\

Please set up a powershell profile on the Trust Computer (Citrix) by following this link: [article](https://viapath.service-now.com/nav_to.do?uri=%2Fkb_view.do%3Fsys_kb_id%3Df076201c1b4cd5500dc321f6b04bcbc7)

In powershell type:\
duty

## Developers
Igor Malashchuk\
STP Trainee in Clinical Bioinformatics\
Guy's and St Thomas's NHS Trust\
Sign off date: 21st June 2022







