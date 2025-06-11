import os
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

HOST = os.getenv('MAIL_HOST')
PORT = os.getenv('MAIL_PORT')
USER = os.getenv('MAIL_USER')
PASSWORD = os.getenv('MAIL_PASSWORD')


class MailBody(BaseModel):
    to: str
    subject: str
    body: str