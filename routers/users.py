from fastapi import APIRouter , Depends
from database.db_config import get_session
from sqlalchemy.orm import Session
from utils.security import get_current_user
from models.auth_models import User
from schemas.auth_schema import UserDetails
from typing import List
router = APIRouter(prefix="/api/v1/users",tags=["users"])
import uuid
from fastapi import status
from fastapi.responses  import JSONResponse
from fastapi.exceptions import HTTPException

import imaplib
import email
from email.header import decode_header

# Configuration
# GMAIL_USER = "prasanth520100@gmail.com"
# GMAIL_APP_PASSWORD = ""  # Replace with generated App Password
# IMAP_SERVER = "imap.gmail.com"


@router.get("/",response_model=List[UserDetails])
async def get_users(users : User = Depends(get_current_user), 
              session : Session = Depends(get_session),
              limit : int = 100,
              offset : int = 0):
    users = session.query(User).order_by(User.created_at.desc()
                                         ).limit(limit).offset(offset)
    return  users




def connect_and_fetch_emails(max_emails: int = 10):
    try:
        # Connect to Gmail IMAP server
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        mail.select("inbox")  # Select the Inbox folder

        # Search for all emails (Use 'UNSEEN' instead of 'ALL' for unread emails only)
        status, messages = mail.search(None, "ALL")
        if status != "OK":
            return []

        email_ids = messages[0].split()
        
        # Get the last `max_emails` IDs (most recent emails)
        recent_email_ids = email_ids[-max_emails:]
        recent_email_ids.reverse()  # Newest first

        emails_list = []

        for e_id in recent_email_ids:
            # Fetch the email message by ID
            res, msg_data = mail.fetch(e_id, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    
                    # Decode Email Subject
                    subject, encoding = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding or "utf-8")

                    # Decode Email Sender
                    from_addr = msg.get("From")

                    # Extract Email Body
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            content_type = part.get_content_type()
                            content_disposition = str(part.get("Content-Disposition"))

                            if content_type == "text/plain" and "attachment" not in content_disposition:
                                body = part.get_payload(decode=True).decode(errors="ignore")
                                break
                    else:
                        body = msg.get_payload(decode=True).decode(errors="ignore")

                    emails_list.append({
                        "id": e_id.decode("utf-8"),
                        "from": from_addr,
                        "subject": subject,
                        "body": body.strip()
                    })

        mail.logout()
        return emails_list

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch emails: {str(e)}")


@router.get("/get-emails")
def get_emails(limit: int = 10):
    """Endpoint to fetch incoming emails from Gmail."""
    emails = connect_and_fetch_emails(max_emails=limit)
    return {
        "status": "success",
        "count": len(emails),
        "emails": emails
    }


@router.get('/gmail/webhook')
def gmail_webhook():
    """Endpoint to handle Gmail webhook notifications."""
    # Here you would handle the incoming webhook data from Gmail
    # For example, you might want to parse the request body and process the notification
    return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "Webhook received successfully."})