'''
Email server settings
'''
import os
#document_root = "/".join(os.path.dirname(os.path.realpath(__file__)).split("/")[:-2])
document_root = os.getcwd()
mokaguys_email = "gst-tr.mokaguys@nhs.net"


username_file_path = "{document_root}/.amazon_email_username".format(
    document_root=document_root
)
with open(username_file_path, "r") as username_file:
    user = username_file.readline().rstrip()
pw_file = "{document_root}/.amazon_email_pw".format(document_root=document_root)
with open(pw_file, "r") as email_password_file:
    pw = email_password_file.readline().rstrip()
host = "smtp://relay.gstt.local"
port = 25
me = "moka.alerts@gstt.nhs.uk"
you = mokaguys_email
test = 'igor.malashchuk@nhs.net'
smtp_do_tls = True

