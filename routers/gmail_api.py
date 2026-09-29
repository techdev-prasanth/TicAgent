"""
Gmail real-time new-mail backend (FastAPI).

Flow:
  1. GET  /auth/login     -> redirect user to Google consent screen
  2. GET  /auth/callback  -> exchange code for tokens, save them, call gmail.users.watch()
  3. POST /gmail/webhook  -> Pub/Sub push endpoint. Google calls this the moment
                              a mailbox change happens. We diff historyId and
                              fetch only the new messages.

Run:
  uvicorn main:app --reload --port 8000

Notes:
  - Token storage here uses a local JSON file for demo simplicity.
    In production, store per-user tokens (encrypted) in your DB, keyed by user id.
  - Gmail's watch() expires after ~7 days. An APScheduler job renews it daily.
  - The webhook endpoint MUST be a public HTTPS URL that matches the Pub/Sub
    push subscription endpoint you configured in Cloud Console.
"""

import os
import json
import base64
import logging
from datetime import datetime

from fastapi import FastAPI, Request, HTTPException , APIRouter
from fastapi.responses import RedirectResponse, JSONResponse
from flower import app
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("gmail-realtime")

router = APIRouter(prefix="/api/v1/gmail", tags=["gmail"])
# ---------- Config ----------
CLIENT_SECRETS_FILE = os.getenv("CLIENT_SECRETS_FILE", "client_secret.json")
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
REDIRECT_URI = os.getenv("REDIRECT_URI", "http://127.0.0.1:8000/api/v1/gmail/auth/callback")
PUBSUB_TOPIC = os.getenv("PUBSUB_TOPIC")  # e.g. projects/YOUR_PROJECT_ID/topics/gmail-notifications
TOKEN_STORE = "tokens.json"  # demo only — replace with a real DB table


# ---------- Token storage helpers (swap for DB in production) ----------
def _load_all_tokens() -> dict:
    if os.path.exists(TOKEN_STORE):
        with open(TOKEN_STORE, "r") as f:
            return json.load(f)
    return {}


def _save_tokens(email: str, creds: Credentials, last_history_id: str = None):
    data = _load_all_tokens()
    entry = data.get(email, {})
    entry.update({
        "token": creds.token,
        "refresh_token": creds.refresh_token or entry.get("refresh_token"),
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": creds.scopes,
    })
    if last_history_id:
        entry["last_history_id"] = last_history_id
    data[email] = entry
    with open(TOKEN_STORE, "w") as f:
        json.dump(data, f, indent=2)


def _creds_for(email: str) -> Credentials:
    data = _load_all_tokens()
    if email not in data:
        raise HTTPException(status_code=404, detail=f"No stored credentials for {email}")
    e = data[email]
    return Credentials(
        token=e["token"],
        refresh_token=e["refresh_token"],
        token_uri=e["token_uri"],
        client_id=e["client_id"],
        client_secret=e["client_secret"],
        scopes=e["scopes"],
    )


def _gmail_service(creds: Credentials):
    return build("gmail", "v1", credentials=creds)


# ---------- OAuth ----------
@router.get("/auth/login")
def login():
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES, redirect_uri=REDIRECT_URI
    )
    auth_url, _ = flow.authorization_url(
        access_type="offline",       # needed to get a refresh_token
        include_granted_scopes="true",
        prompt="consent",            # forces refresh_token on repeat logins too
    )
    return RedirectResponse(auth_url)


@router.get("/auth/callback")
def auth_callback(request: Request):
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES, redirect_uri=REDIRECT_URI
    )
    flow.fetch_token(authorization_response=str(request.url))
    creds = flow.credentials

    service = _gmail_service(creds)
    profile = service.users().getProfile(userId="me").execute()
    email = profile["emailAddress"]

    _save_tokens(email, creds, last_history_id=str(profile["historyId"]))

    # Start (or restart) the watch on this mailbox
    watch_response = _start_watch(email)

    return JSONResponse({
        "message": "Gmail watch started",
        "email": email,
        "watch": watch_response,
    })


def _start_watch(email: str):
    if not PUBSUB_TOPIC:
        raise RuntimeError("PUBSUB_TOPIC env var not set")
    creds = _creds_for(email)
    service = _gmail_service(creds)
    body = {
        "labelIds": ["INBOX"],
        "topicName": PUBSUB_TOPIC,
        "labelFilterAction": "include",
    }
    resp = service.users().watch(userId="me", body=body).execute()
    log.info(f"watch() started for {email}: expires {resp.get('expiration')}")
    return resp


# ---------- Pub/Sub push webhook ----------
@router.post("/webhook")
async def gmail_webhook(request: Request):
    envelope = await request.json()

    # Pub/Sub push format: {"message": {"data": "<base64>", "attributes": {...}}, "subscription": "..."}
    message = envelope.get("message")
    if not message or "data" not in message:
        raise HTTPException(status_code=400, detail="Invalid Pub/Sub message")

    payload = json.loads(base64.b64decode(message["data"]).decode("utf-8"))
    # payload looks like: {"emailAddress": "user@gmail.com", "historyId": "123456"}
    email = payload["emailAddress"]
    new_history_id = str(payload["historyId"])

    log.info(f"[{datetime.utcnow().isoformat()}] notification for {email}, historyId={new_history_id}")

    try:
        _process_new_mail(email, new_history_id)
    except Exception as e:
        log.exception(f"Error processing history for {email}: {e}")
        # Still 200 so Pub/Sub doesn't retry-storm; log/alert separately in production

    # Must ack quickly (2xx) or Pub/Sub will redeliver
    return JSONResponse({"status": "ok"})


def _process_new_mail(email: str, new_history_id: str):
    data = _load_all_tokens()
    entry = data.get(email)
    if not entry:
        log.warning(f"No stored tokens for {email}, skipping")
        return

    creds = _creds_for(email)
    service = _gmail_service(creds)

    start_history_id = entry.get("last_history_id", new_history_id)

    history_resp = service.users().history().list(
        userId="me",
        startHistoryId=start_history_id,
        historyTypes=["messageAdded"],
    ).execute()

    for record in history_resp.get("history", []):
        for added in record.get("messagesAdded", []):
            msg_id = added["message"]["id"]
            msg = service.users().messages().get(
                userId="me", id=msg_id, format="metadata",
                metadataHeaders=["From", "Subject", "Date"],
            ).execute()
            headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
            log.info(f"NEW MAIL for {email}: from={headers.get('From')} subject={headers.get('Subject')}")

            # ---- Your real-time handling goes here ----
            # e.g. push to a websocket, save to DB, trigger a notification, etc.

    # Save new historyId as checkpoint
    _save_tokens(email, creds, last_history_id=new_history_id)


# ---------- Renew watch daily (watch expires after ~7 days) ----------
def _renew_all_watches():
    for email in _load_all_tokens().keys():
        try:
            _start_watch(email)
        except Exception as e:
            log.exception(f"Failed to renew watch for {email}: {e}")


scheduler = BackgroundScheduler()
scheduler.add_job(_renew_all_watches, "interval", hours=24)
scheduler.start()


@router.get("/")
def root():
    return {"status": "running", "watched_mailboxes": list(_load_all_tokens().keys())}