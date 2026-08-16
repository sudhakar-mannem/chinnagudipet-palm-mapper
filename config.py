"""Application configuration."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent


def reload_env():
    """Load .env into process env (override so edits take effect after restart)."""
    env_path = ROOT / ".env"
    load_dotenv(dotenv_path=env_path, override=True, encoding="utf-8-sig")


reload_env()

CREDENTIALS_DIR = ROOT / "credentials"

# Keep heavy photo/cache I/O off OneDrive — OneDrive sync makes the app feel frozen.
_LOCAL_DATA = Path(os.environ.get("LOCALAPPDATA") or (Path.home() / "AppData" / "Local"))
CACHE_DIR = Path(os.getenv("PALM_CACHE_DIR") or (_LOCAL_DATA / "PalmMapper" / "cache"))
PHOTOS_DIR = CACHE_DIR / "photos"
OUTPUT_DIR = Path(os.getenv("PALM_OUTPUT_DIR") or (_LOCAL_DATA / "PalmMapper" / "output"))
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
