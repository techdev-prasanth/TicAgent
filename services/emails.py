from fastapi import FastAPI , BackgroundTasks
from fastapi_mail import FastMail ,MessageSchema , ConnectionConfig , MessageType
from dotenv import load_dotenv
import os
load_dotenv(override=True)



config = ConnectionConfig(
    MAIL_SERVER=os.getenv("MAIL_SERVER"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_FROM_NAME=os.getenv("MAIL_FROM_NAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_PORT=int(os.getenv("MAIL_PORT")),
    MAIL_SSL_TLS=True,
    MAIL_STARTTLS=False,
    USE_CREDENTIALS=True,
    MAIL_USERNAME=os.getenv("MAIL_USERNAME")
    
)

def send_mails_worker(background_tasks: BackgroundTasks):
    message = MessageSchema(
        subject="Test mail",
        recipients=["prasanth520100@gmail.com"],
        body="this is just a test mail",
        subtype=MessageType.plain
    )
    fm = FastMail(config=config)
    background_tasks.add_task(fm.send_message,message)

