import json
import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/tasks",
    "https://www.googleapis.com/auth/calendar.events",
]
ROOT = Path(__file__).resolve().parent.parent.parent.parent


def _from_root(value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else ROOT / path


TOKEN_PATH = _from_root(os.environ.get("GMAIL_TOKEN_PATH", "token.json"))
CREDENTIALS_PATH = _from_root(
    os.environ.get("GMAIL_CREDENTIALS_PATH", "credentials.json")
)


class GoogleConfigurationError(RuntimeError):
    """Raised when local Google OAuth configuration is missing or invalid."""


def validate_credentials_file() -> None:
    if not CREDENTIALS_PATH.is_file():
        raise GoogleConfigurationError(
            f"Google OAuth credentials were not found at {CREDENTIALS_PATH}. "
            "See the Google Cloud setup section in ReadMe.md."
        )
    try:
        with CREDENTIALS_PATH.open(encoding="utf-8") as file:
            data = json.load(file)
    except (json.JSONDecodeError, OSError) as err:
        raise GoogleConfigurationError(
            "The Google OAuth credentials file is unreadable or is not valid JSON."
        ) from err
    if "installed" not in data:
        raise GoogleConfigurationError(
            "This local app requires a Google OAuth client of type Desktop app; "
            "download that client's JSON file and set GMAIL_CREDENTIALS_PATH to it."
        )


def _stored_scopes() -> set:
    try:
        with TOKEN_PATH.open(encoding="utf-8") as f:
            data = json.load(f)
        return set(data.get("scopes") or [])
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return set()


def _load_stored_credentials():
    if not TOKEN_PATH.exists():
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
            validate_credentials_file()
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
        with TOKEN_PATH.open("w", encoding="utf-8") as f:
            f.write(creds.to_json())
    return creds
