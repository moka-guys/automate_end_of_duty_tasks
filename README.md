# Duty CSV

This repository processes DNAnexus runfolders, identifying those requiring download to the GSTT network.

The script supports all runtypes. For those runtypes that have downstream outputs requiring download onto the GSTT network, it will generate a CSV file containing URLs for the files requiring download, and attach the CSV file to an email containing instructions on how to download the files to the GSTT network. For those runtypes with no downstream outputs, an email will still be sent but no CSV file will be attached. The email is sent to the bioinformatics shared inbox. Run types are defined in the configuration file.

## Running the script

The script takes the following command line arguments:

```
Required named arguments:
  -P PROJECT_NAME, --project_name PROJECT_NAME
                        Name of project to obtain download links from
  -I PROJECT_ID, --project_id PROJECT_ID
                        ID of project to obtain download links from
  -EU EMAIL_USER, --email_user EMAIL_USER
                        Username for mail server
  -PW EMAIL_PW, --email_pw EMAIL_PW
                        Password for mail server
  -TP TSO_PANNUMBERS [TSO_PANNUMBERS ...], --tso_pannumbers TSO_PANNUMBERS [TSO_PANNUMBERS ...]
                        Space separated pan numbers
  -SP STG_PANNUMBERS [STG_PANNUMBERS ...], --stg_pannumbers STG_PANNUMBERS [STG_PANNUMBERS ...]
                        Space separated pan numbers
  -CP CP_CAPTURE_PANNOS [CP_CAPTURE_PANNOS ...], --cp_capture_pannos CP_CAPTURE_PANNOS [CP_CAPTURE_PANNOS ...]
                        Synnovis Custom Panels whole capture pan numbers, space separated
  -T, --testing         Test mode
```

TSO pan numbers should be Synnovis pan numbers - these are used by the scripts to define which samples to download to the trust network, and we only want to download Synnovis samples.

St George's pan numbers are used to define which files need to be downloaded to the St George's area and which need to be downloaded to the Synnovis area.

Custom Panels whole capture pan numbers are used to define which Custom Panels output files need to be downloaded to both the St George's area and the Synnovis area.

Before running the script, the DX_API_TOKEN environment variable must be set and exported, where DNANEXUS_AUTH_TOKEN is the DNAnexus authentication token:

```bash
export DX_API_TOKEN=$DNANEXUS_AUTH_TOKEN
```

The script can then be run as follows:

```bash
python3 duty_csv.py [-h] -P PROJECT_NAME -I PROJECT_ID -EU EMAIL_USER -PW EMAIL_PW -TP TSO_PANNUMBERS
                   [TSO_PANNUMBERS ...] -SP STG_PANNUMBERS [STG_PANNUMBERS ...] -CP CP_CAPTURE_PANNOS
                   [CP_CAPTURE_PANNOS ...] [-T]
```

### Test mode

If running during development, the `-T` flag should be used. This ensures that:
1. Emails are sent to the email recipient specified in the config for test mode, as opposed to the production email address. This prevents spam
2. The filepaths written to the CSV file are for the test area on the P drive as opposed to the production area. This ensures that when testing integration with the downstream [process_duty_csv](https://github.com/moka-guys/Automate_Duty_Process_CSV) script, files are not written to the production output areas on the P drive

It is important that any changes to this script are fully tested for integration with the downstream [process_duty_csv](https://github.com/moka-guys/Automate_Duty_Process_CSV) script as part of the development cycle

## Outputs

The script has 3 file outputs:
* CSV file - contains information required by the [process_duty_csv](https://github.com/moka-guys/Automate_Duty_Process_CSV) script to download the required files output by the pipeline from DNAnexus to the required locations on the GSTT network
* HTML file - this file is the HTMl that is used as the email message contents
* Log file - contains all log messages from running the script

## Docker image

The docker image is built, tagged and saved as a .tar.gz file using the Makefile as follows:

```bash
sudo make build
```

The docker image can be run as follows, making sure to supply the DNAnexus authentication token as an environment variable:

```bash
sudo docker run --rm -e DX_API_TOKEN=$DNANEXUS_AUTH_TOKEN -v $PATH_TO_OUTPUTS:/outputs seglh/duty_csv:$TAG [-h] -P PROJECT_NAME -I PROJECT_ID -EU EMAIL_USER -PW EMAIL_PW -TP TSO_PANNUMBERS -SP STG_PANNUMBERS -CP CP_CAPTURE_PANNOS
```

The current and all previous versions of the tool are stored as dockerised versions in 001_ToolsReferenceData project as .tar.gz files.

### Developed by the Synnovis Genome Informatics Team
