import resend
import os


def send_mail(recipient, subject, body):
    FROM = os.environ.get('Email_User')
    TO = recipient if type(recipient) is list else [recipient]
    SUBJECT = subject
    TEXT = body
    resend.api_key = os.environ.get('RESEND_API_KEY')

    try:
        resend.Emails.send({
            'from': FROM,
            'to': TO,
            'subject': SUBJECT,
            'text': TEXT
        })
    except Exception as e:
        print(f"Email Exception: \n{str(e)}")
