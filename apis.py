from fastapi import FastAPI , BackgroundTasks
from fastapi_mail import FastMail ,MessageSchema , ConnectionConfig , MessageType
app = FastAPI()
from dotenv import load_dotenv
from pydantic import EmailStr
from fastapi.responses import JSONResponse
load_dotenv(override=True)
import os
from services.emails import send_mails_worker



@app.post("/sendmail/")
async def send_mail(background_tasks : BackgroundTasks):
    send_mails_worker(background_tasks)
    return {"message":"mail has been sent"}


