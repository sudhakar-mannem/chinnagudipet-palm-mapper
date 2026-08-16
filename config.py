"""Application configuration."""
from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent


def _materialize_json_secret(raw, target: Path) -> None:
    """Write a secrets value (dict / JSON text / base64 JSON) to target path."""
    import base64

    if isinstance(raw, dict):
        text = json.dumps(raw)
    else:
        text = str(raw).strip()
        if text.startswith("```"):
            lines = text.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines).strip()
        # Prefer plain JSON; fall back to base64 (TOML-safe for Cloud secrets)
        try:
            json.loads(text)
        except Exception:
            decoded = base64.b64decode(text).decode("utf-8")
            json.loads(decoded)  # validate
            text = decoded
    target.write_text(text, encoding="utf-8")


def _apply_streamlit_secrets() -> dict:
    """
    Copy Streamlit Community Cloud / local secrets.toml into os.environ
    and materialize OAuth JSON files. Returns a small status dict for UI.
    """
    status = {
        "secrets_available": False,
        "openai_from_secrets": False,
        "credentials_written": False,
        "token_written": False,
        "credentials_error": "",
        "token_error": "",
    }
    try:
        import streamlit as st

        if not hasattr(st, "secrets"):
            return status
        secrets = st.secrets
        _ = len(secrets)
        status["secrets_available"] = True
    except Exception as exc:
        status["credentials_error"] = "secrets unavailable: %s" % exc
        return status

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
        if key == "OPENAI_API_KEY":
            status["openai_from_secrets"] = True

    cred_dir = ROOT / "credentials"
    cred_dir.mkdir(parents=True, exist_ok=True)

    # Prefer *_B64 keys (valid TOML always). Fall back to *_JSON.
    secret_specs = (
        (
            ("GOOGLE_CREDENTIALS_B64", "GOOGLE_CREDENTIALS_JSON"),
            "credentials.json",
            "credentials_written",
            "credentials_error",
        ),
        (
            ("GOOGLE_TOKEN_B64", "GOOGLE_TOKEN_JSON"),
            "token.json",
            "token_written",
            "token_error",
        ),
    )
    for keys, filename, flag_key, err_key in secret_specs:
        raw = None
        used = None
        for key in keys:
            raw = _get(key)
            if raw is not None and raw != "":
                used = key
                break
        if raw is None or raw == "":
            status[err_key] = "set %s (recommended) or %s" % (keys[0], keys[1])
            continue
        target = cred_dir / filename
        try:
            _materialize_json_secret(raw, target)
            status[flag_key] = True
            status[err_key] = "ok via %s" % used
        except Exception as exc:
            status[err_key] = "could not write %s from %s: %s" % (filename, used, exc)
    return status


def reload_env():
    """Load .env then overlay Streamlit secrets (Cloud / local secrets.toml)."""
    global DRIVE_FOLDER_ID, OPENAI_API_KEY, OPENAI_VISION_MODEL, CACHE_DIR, PHOTOS_DIR, OUTPUT_DIR, STATE_PATH
    env_path = ROOT / ".env"
    load_dotenv(dotenv_path=env_path, override=True, encoding="utf-8-sig")
    secret_status = _apply_streamlit_secrets()

    DRIVE_FOLDER_ID = (
        os.getenv("GOOGLE_DRIVE_FOLDER_ID") or "1_ZkYcDg4zu42RKNN5o4ChipG7Wlz43Gs"
    ).strip()
    OPENAI_API_KEY = (os.getenv("OPENAI_API_KEY") or "").strip().strip('"').strip("'")
    OPENAI_VISION_MODEL = (os.getenv("OPENAI_VISION_MODEL") or "gpt-4o").strip()
    return secret_status


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

# Apply .env / Streamlit secrets after path defaults exist
reload_env()


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
