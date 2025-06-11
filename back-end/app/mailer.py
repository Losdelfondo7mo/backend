from .config import HOST, PORT, PASSWORD, USER, MailBody
from ssl import create_default_context
from email.mime.text import MIMEText
from smtplib import SMTP

def send_mail(data:dict|None=None):
    msg = MailBody(**data)
    message = MIMEText(msg.body, "html")
    message["from"] = USER
    message["to"] = ", ".join(msg.to)
    message["subject"] = msg.subject

    ctx = create_default_context()
    
    
    try:
        with SMTP(HOST, PORT) as server:
            server.ehlo()
            server.starttls(context=ctx)
            server.ehlo()
            server.login(user=USER, password=PASSWORD)
            server.send_message(message)
            print("Success")
            server.quit
        return {"status": 200, "errors": None}
    except Exception as e:
        return {"status": 500, "errors": str(e)}
    
    