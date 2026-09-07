import json
from pathlib import Path


CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config.json"

DEFAULTS = {
    "gmailQuery": None,
    "limit": 10,
}


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        return dict(DEFAULTS)
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return dict(DEFAULTS)
    merged = dict(DEFAULTS)
    merged.update({k: v for k, v in data.items() if v not in (None, "")})
    return merged
