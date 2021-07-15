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

    server = smtplib.SMTP(os.environ.get('Email_SMTP'), os.environ.get('Email_Port'))
    try:
        server.ehlo()
        server.starttls()
        server.login(FROM, secret)
        server.sendmail(FROM, TO, message.as_string())
        server.close()
    except Exception as e:
        print(f"Email Exception: \n{str(e)}")
