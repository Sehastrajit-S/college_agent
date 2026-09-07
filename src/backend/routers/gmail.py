import threading
from pathlib import Path

from fastapi import APIRouter, HTTPException

from ..services.gmail_client import CREDENTIALS_PATH, get_credentials
from ..services.google_auth import has_valid_credentials

router = APIRouter(prefix="/api", tags=["gmail"])


_state = {"busy": False, "message": None, "error": None}


@router.get("/gmail-auth")
def gmail_auth_status():
    return {
        "connected": has_valid_credentials(),
        "hasCredentials": Path(CREDENTIALS_PATH).exists(),
        "busy": _state["busy"],
        "message": _state["message"],
        "error": _state["error"],
    }


def _run_gmail_auth():
    _state.update(busy=True, message=None, error=None)
    try:
        get_credentials()
        _state.update(busy=False, message="Connected.")
    except Exception as err: 
        _state.update(busy=False, error=str(err))


@router.post("/gmail-auth")
def gmail_auth_start():
    if not Path(CREDENTIALS_PATH).exists():
        raise HTTPException(
            400,
            "credentials.json not found at the repo root. Download your OAuth "
            "client secret from Google Cloud Console first.",
        )
    if has_valid_credentials():
        return {"status": "already_connected"}
    if _state["busy"]:
        return {"status": "already_running"}
    threading.Thread(target=_run_gmail_auth, daemon=True).start()
    return {
        "status": "started",
        "message": "A browser window should open — sign in and approve access "
        "to Gmail, Google Tasks, and Google Calendar, then this page will update "
        "automatically.",
    }
