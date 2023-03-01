# Automate End of Duty Tasks

The generates download links for a runfolder that are saved to a .csv file.

The script supports runtypes that have downstream outputs requiring
download onto the trust network as part of duty bioinformatician end of run processing tasks. These runtypes are as follows:

* WES
* TSO500
* SNP
* MokaPipe

The script generates a CSV file containing urls for the files requiring download, and attaches this file to an email containing instructions on how to download the files to the appropriate locations on the GSTT network. This email is sent to the duty bioinformatician.

## Running the script

The script takes the following command line arguments:

```
Required named arguments:
  -P PROJECT_NAME, --project_name PROJECT_NAME
                        Name of project to obtain download links from
  -I PROJECT_ID, --project_id PROJECT_ID
                        ID of project to obtain download links from
  -A AUTH_TOKEN, --auth_token AUTH_TOKEN
                        DNAnexus authentication token
  -EU EMAIL_USER, --email_user EMAIL_USER
                        Username for mail server
  -PW EMAIL_PW, --email_pw EMAIL_PW
                        Password for mail server
```

It can be run manually as follows:

```bash
duty_csv.py [-h] -P PROJECT_NAME -I PROJECT_ID -A AUTH_TOKEN -EU EMAIL_USER -PW EMAIL_PW
```

## Docker image

The docker image is built, tagged and saved as a .tar.gz file using the Makefile as follows:

```bash
sudo make build
```

The docker image can be run as follows:

```bash
```

The current and all previous versions of the tool are stored as dockerised versions in 001_ToolsReferenceData project as .tar.gz files.

### Developed by the Synnovis Genome Informatics Team
