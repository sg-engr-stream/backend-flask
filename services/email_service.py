import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate
import os


def send_mail(recipient, subject, body):
    FROM = os.environ.get('Email_User')
    TO = recipient if type(recipient) is list else [recipient]
    SUBJECT = subject
    TEXT = body
    secret = os.environ.get('Email_Pass')
    message = MIMEMultipart(From=FROM, Date=formatdate(localtime=True), Subject=SUBJECT)
    message['subject'] = SUBJECT
    message['to'] = ','.join(TO)
    message.attach(MIMEText(TEXT))

    smtp_server = os.environ.get('Email_SMTP') or ''
    smtp_port = int(os.environ.get('Email_Port'))
    
    try:
        server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=10)
        server.login(FROM, secret)
        server.sendmail(FROM, TO, message.as_string())
        server.quit()
    except smtplib.SMTPAuthenticationError as e:
        print(f"SMTP Authentication Error: {str(e)}")
    except Exception as e:
        print(f"Email Exception: \n{str(e)}")
