# Automate End of Duty Tasks

The script searches the DNAnexus for recently created production projects '002_' and generates download links that are saved to a .csv file. 

An email is sent to the Duty Bioinformatician with instructions on how to download the files to the appropriate locations on the GST-Trust network. 

The script supports the following projects:

* WES
* TSO500
* SNP
* MokaPipe

## Deployment with Ansible-Playbook

The script runs on the Genapp test server. To deploy the scrip please use the ansible-playbook:
[automate_end_of_duty_tasks.yml](https://github.com/moka-guys/deployment/blob/develop/playbooks/automate_end_of_duty_tasks.yml)\
On the Genapp Test Server go to the deployment directory:
```xml
cd /home/mokaguys/code/deployment
```
Run the ansible playbook:
```xml
ansible-playbook playbooks/automate_end_of_duty_tasks.yml
```
The variables are located here:
```xml
/home/mokaguys/code/deployment/playbooks/vars/automate_end_of_duty_tasks.yml
```

## Deployment without Ansible-Playbook

To use the script without using ansible-playbook requires the user to generate the following folder structure:
* Automate_Duty
    * LOG
    * SNP/archive
    * WES/archive
    * MokaPipe/archive
    * TSO500/archive
    * automate_end_of_duty_tasks (obtained from GitHub repository)

Use the following commands:
~~~
mkdir Automate_Duty
cd Automate_Duty
mkdir LOG
mkdir SNP
mkdir SNP/archive
mkdir WES
mkdir WES/archive
mkdir MokaPipe
mkdir MokaPipe/archive
mkdir TSO500
mkdir TSO500/archive
git clone https://github.com/moka-guys/automate_end_of_duty_tasks.git
~~~
To run the script:
~~~
python automate_end_of_duty_tasks/automateEODT.py -7d
~~~

-7d refers to the time frame the script will search the DNAnexus for projects created in the last 7 days from now.
The period of time can be changed by using the following key:
    “s”, “m”, “d”, “w”, or “y” (for seconds, minutes, days, weeks, or years)

Note:\ 
To run the script requires DNAnexus read-only token saved to a file called DNAnexus_auth_token.py inside the automate_end_of_duty_tasks folder. 
Inside the DNAnexus_auth_token.py type:
~~~
token = 'XXXXXXXXXXXXXXXXXXXXXXX'
~~~
The read only token can be found in [BitWarden](https://vault.bitwarden.com/#/login) by searching for dnanexus interpretation request login. The token is valid for one year. 

## Downloading files using links from CSV files on the Trust Network

The script is set up to search for DNAnexus projects created in the previous 7 days. 

The email containing csv attachment is sent to mokaguys (gst-tr.mokaguys@nhs.net) 

The duty Bioinformatician has to save the csv file(s) to the following location:
```xml
P:\Bioinformatics\Duty_Bioinformatics_CSV
```
The Duty Bioinformatician needs to Open PowerShell.

Please set up a PowerShell profile on the Trust Computer (Citrix) by following this link: [article](https://viapath.service-now.com/nav_to.do?uri=%2Fkb_view.do%3Fsys_kb_id%3Df076201c1b4cd5500dc321f6b04bcbc7)

In PowerShell type:
```xml
duty
```
## Developers
Igor Malashchuk\
STP Trainee in Clinical Bioinformatics\
Guy's and St Thomas's NHS Trust\
Sign off date: 22nd June 2022






