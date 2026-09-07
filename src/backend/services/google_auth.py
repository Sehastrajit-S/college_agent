import json
import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/tasks",
    "https://www.googleapis.com/auth/calendar.events",
]
TOKEN_PATH = os.environ.get("GMAIL_TOKEN_PATH", "token.json")
CREDENTIALS_PATH = os.environ.get("GMAIL_CREDENTIALS_PATH", "credentials.json")


def _stored_scopes() -> set:
    try:
        with open(TOKEN_PATH, encoding="utf-8") as f:
            data = json.load(f)
        return set(data.get("scopes") or [])
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return set()


def _load_stored_credentials():
    if not os.path.exists(TOKEN_PATH):
        return None
    if not set(SCOPES).issubset(_stored_scopes()):
        return None
    try:
        return Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    except (ValueError, OSError):
        return None


def has_valid_credentials() -> bool:
    creds = _load_stored_credentials()
    if creds is None:
        return False
    return creds.valid or bool(creds.expired and creds.refresh_token)


def get_credentials() -> Credentials:
    creds = _load_stored_credentials()
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "w", encoding="utf-8") as f:
            f.write(creds.to_json())
    return creds
