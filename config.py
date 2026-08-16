"""Application configuration."""
from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent


def _apply_streamlit_secrets() -> None:
    """Copy Streamlit Community Cloud / local secrets.toml into os.environ."""
    try:
        import streamlit as st

        if not hasattr(st, "secrets"):
            return
        secrets = st.secrets
    except Exception:
        return

    def _get(key: str):
        try:
            return secrets[key]
        except Exception:
            return None

    mapping = {
        "OPENAI_API_KEY": _get("OPENAI_API_KEY"),
        "OPENAI_VISION_MODEL": _get("OPENAI_VISION_MODEL"),
        "GOOGLE_DRIVE_FOLDER_ID": _get("GOOGLE_DRIVE_FOLDER_ID"),
        "PALM_CACHE_DIR": _get("PALM_CACHE_DIR"),
        "PALM_OUTPUT_DIR": _get("PALM_OUTPUT_DIR"),
    }
    for key, value in mapping.items():
        if value is None or value == "":
            continue
        os.environ[key] = str(value)

    # Optional: paste full OAuth client JSON / token JSON into secrets for Cloud
    cred_dir = ROOT / "credentials"
    cred_dir.mkdir(parents=True, exist_ok=True)
    for secret_key, filename in (
        ("GOOGLE_CREDENTIALS_JSON", "credentials.json"),
        ("GOOGLE_TOKEN_JSON", "token.json"),
    ):
        raw = _get(secret_key)
        if not raw:
            continue
        target = cred_dir / filename
        try:
            if isinstance(raw, dict):
                target.write_text(json.dumps(raw), encoding="utf-8")
            else:
                text = str(raw).strip()
                # Validate JSON before writing
                json.loads(text)
                target.write_text(text, encoding="utf-8")
        except Exception:
            pass


def reload_env():
    """Load .env then overlay Streamlit secrets (Cloud / local secrets.toml)."""
    env_path = ROOT / ".env"
    load_dotenv(dotenv_path=env_path, override=True, encoding="utf-8-sig")
    _apply_streamlit_secrets()


reload_env()

CREDENTIALS_DIR = ROOT / "credentials"

# Local Windows: keep heavy I/O off OneDrive. Cloud/Linux: use home cache.
def _default_data_root() -> Path:
    local_app = os.environ.get("LOCALAPPDATA")
    if local_app:
        return Path(local_app) / "PalmMapper"
    return Path.home() / ".palm_mapper"


_DATA_ROOT = _default_data_root()
CACHE_DIR = Path(os.getenv("PALM_CACHE_DIR") or (_DATA_ROOT / "cache"))
PHOTOS_DIR = CACHE_DIR / "photos"
OUTPUT_DIR = Path(os.getenv("PALM_OUTPUT_DIR") or (_DATA_ROOT / "output"))
STATE_PATH = CACHE_DIR / "plant_state.json"

CREDENTIALS_FILE = CREDENTIALS_DIR / "credentials.json"
TOKEN_FILE = CREDENTIALS_DIR / "token.json"

DRIVE_FOLDER_ID = (
    os.getenv("GOOGLE_DRIVE_FOLDER_ID") or "1_ZkYcDg4zu42RKNN5o4ChipG7Wlz43Gs"
).strip()
OPENAI_API_KEY = (os.getenv("OPENAI_API_KEY") or "").strip().strip('"').strip("'")
OPENAI_VISION_MODEL = (os.getenv("OPENAI_VISION_MODEL") or "gpt-4o").strip()


def openai_key_configured() -> bool:
    key = (os.getenv("OPENAI_API_KEY") or OPENAI_API_KEY or "").strip().strip('"').strip("'")
    if not key:
        return False
    if key.startswith("sk-your") or key == "sk-your-key-here":
        return False
    return key.startswith("sk-") and len(key) > 20


DRIVE_SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
]

HEALTH_COLORS = {
    "green": {"hex": "#22c55e", "kml_aabbggrr": "ff2ec522", "label": "Healthy"},
    "amber": {"hex": "#f59e0b", "kml_aabbggrr": "ff0b9ef5", "label": "Needs attention"},
    "red": {"hex": "#ef4444", "kml_aabbggrr": "ff4444ef", "label": "Critical / diseased"},
    "white": {"hex": "#f8fafc", "kml_aabbggrr": "fff8faf8", "label": "Unknown"},
}

ICON_URLS = {
    "green": "http://maps.google.com/mapfiles/kml/paddle/grn-circle.png",
    "amber": "http://maps.google.com/mapfiles/kml/paddle/ylw-circle.png",
    "red": "http://maps.google.com/mapfiles/kml/paddle/red-circle.png",
    "white": "http://maps.google.com/mapfiles/kml/paddle/wht-circle.png",
}


def ensure_dirs():
    for path in (CREDENTIALS_DIR, CACHE_DIR, PHOTOS_DIR, OUTPUT_DIR):
        path.mkdir(parents=True, exist_ok=True)
