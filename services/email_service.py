import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate


def send_mail(recipient, subject, body):
    FROM = 'shorturl@hiddenworld.in'
    TO = recipient if type(recipient) is list else [recipient]
    SUBJECT = subject
    TEXT = body
    secret = '5UJ4XWK5u3JEB'
    message = MIMEMultipart(From=FROM, Date=formatdate(localtime=True), Subject=SUBJECT)
    message['subject'] = SUBJECT
    message['to'] = ','.join(TO)
    message.attach(MIMEText(TEXT))

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.ehlo()
    server.starttls()
    server.login(FROM, secret)
    server.sendmail(FROM, TO, message.as_string())
    server.close()
