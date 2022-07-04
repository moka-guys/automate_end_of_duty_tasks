'''
Email server settings
'''
#document_root = "/".join(os.path.dirname(os.path.realpath(__file__)).split("/")[:-2])
#document_root = os.getcwd()
'''
import os
doucment_path = os.path.realpath(__file__)
doucment_path_list = doucment_path.split('/')
document_root = '/'.join(doucment_path_list[:(len(doucment_path_list)-1)])

username_file_path = "{document_root}/.amazon_email_username".format(
    document_root=document_root
)
with open(username_file_path, "r") as username_file:
    user = username_file.readline().rstrip()
pw_file = "{document_root}/.amazon_email_pw".format(document_root=document_root)
with open(pw_file, "r") as email_password_file:
    pw = email_password_file.readline().rstrip()

host = "email-smtp.eu-west-1.amazonaws.com"
port = 587
'''
mokaguys_email = "gst-tr.mokaguys@nhs.net"
host = "relay.gstt.local"
port = 25
email_send_from = "moka.alerts@gstt.nhs.uk"
email_send_to = 'igor.malashchuk@nhs.net'  #mokaguys_email
email_send_test = 'igor.malashchuk@nhs.net'
smtp_do_tls = True

