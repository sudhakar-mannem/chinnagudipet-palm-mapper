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


def _default_data_root() -> Path:
    local_app = os.environ.get("LOCALAPPDATA")
    if local_app:
        return Path(local_app) / "PalmMapper"
    return Path.home() / ".palm_mapper"


_DATA_ROOT = _default_data_root()

# Writable credentials dir (Cloud app tree can be read-only; repo copy is a seed only)
CREDENTIALS_DIR = _DATA_ROOT / "credentials"
_REPO_CREDENTIALS_DIR = ROOT / "credentials"


def _migrate_credentials() -> None:
    """Copy repo credentials/token into the writable data dir when newer/missing."""
    CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
    for name in ("credentials.json", "token.json"):
        src = _REPO_CREDENTIALS_DIR / name
        dest = CREDENTIALS_DIR / name
        if not src.exists():
            continue
        try:
            if (not dest.exists()) or (src.stat().st_mtime > dest.stat().st_mtime):
                dest.write_bytes(src.read_bytes())
        except Exception:
            pass


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
        "credentials_dir": str(CREDENTIALS_DIR),
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

    _migrate_credentials()
    cred_dir = CREDENTIALS_DIR
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
    global CREDENTIALS_FILE, TOKEN_FILE
    env_path = ROOT / ".env"
    load_dotenv(dotenv_path=env_path, override=True, encoding="utf-8-sig")
    _migrate_credentials()
    CREDENTIALS_FILE = CREDENTIALS_DIR / "credentials.json"
    TOKEN_FILE = CREDENTIALS_DIR / "token.json"
    secret_status = _apply_streamlit_secrets()

    DRIVE_FOLDER_ID = (
        os.getenv("GOOGLE_DRIVE_FOLDER_ID") or "1_ZkYcDg4zu42RKNN5o4ChipG7Wlz43Gs"
    ).strip()
    OPENAI_API_KEY = (os.getenv("OPENAI_API_KEY") or OPENAI_API_KEY or "").strip().strip('"').strip("'")
    OPENAI_VISION_MODEL = (os.getenv("OPENAI_VISION_MODEL") or "gpt-4o").strip()
    return secret_status


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
    "green": {"hex": "#22c55e", "kml_aabbggrr": "ff2ec522", "label": "ఆరోగ్యంగా ఉంది"},
    "amber": {"hex": "#f59e0b", "kml_aabbggrr": "ff0b9ef5", "label": "దృష్టి అవసరం"},
    "red": {"hex": "#ef4444", "kml_aabbggrr": "ff4444ef", "label": "తీవ్రం / వ్యాధి"},
    "white": {"hex": "#f8fafc", "kml_aabbggrr": "fff8faf8", "label": "తెలియదు"},
}

# ---------------------------------------------------------------------------
# Map View outliers (durable denylist)
# ---------------------------------------------------------------------------
# Resolved from Map View sequential labels (1-based over mapped clusters in
# build_map / plant select) against bundled data/plant_state.json, then stored
# as Drive file_ids so exclusions survive renumbering after removal.
# Photos remain in plant_state with excluded_from_map=true and original GPS.
#
# Original map numbers at exclusion time:
#   176, 189, 419, 421, 426, 455, 457, 521, 526, 597,
#   1094, 1221, 1403, 1554, 1584, 1763, 1815
EXCLUDED_OUTLIER_MAP_NUMBERS = (
    176,
    189,
    419,
    421,
    426,
    455,
    457,
    521,
    526,
    597,
    1094,
    1221,
    1403,
    1554,
    1584,
    1763,
    1815,
)

# Representative file_ids for the 17 clusters (stable identity).
EXCLUDED_OUTLIER_REP_FILE_IDS = frozenset(
    {
        "1CWXkMr4-zmObF64lrlnHUxuvwz2dAdgc",  # was #176
        "1SU8jnTdii_OEwsdIQ212fcxfClUkvjSg",  # was #189
        "1Cv-4JTVPizoVS1uxZkCv3BK4Fz7kHKKM",  # was #419
        "13TxYQ2LEUh1H5esx9ZbpvzUp33TJqj49",  # was #421
        "17msK1hbrE4NkB2tJu_wm_RdTzzNoby_2",  # was #426
        "1mW1QnW4LncqxjUjxK_eP7ZFgfYLAmMam",  # was #455
        "12wyIMKKL6BBg1yJcfaXHQEIvDS-q6WvQ",  # was #457
        "1TbTuj6lg8X-CS35gjl7so0d6tyYguoq8",  # was #521
        "1RmS82sjLGj-72oIZ5e13lUbNyOHQ6P9I",  # was #526
        "1usSuihEW7kmxCw3T5RzaTPvnWwn-Pq3d",  # was #597
        "1GIhEN8SkpTXJL0u23DekXWTVyWU34Wt6",  # was #1094
        "1h6B9VLgXCe72I8KqufDSXk33TDFxRvtA",  # was #1221
        "1ack2PMThELXfHMwdPfq-0JxVdjf7BFtz",  # was #1403
        "1JScZuKol8Ul35UfHj6vm03HTkN7H7DEr",  # was #1554
        "1NxK94UqB21Y3giNqchq1j7sfyx1QNkw-",  # was #1584
        "1Da5hcL6x0m4MhEZp3CHUk_aRjTlTuuT2",  # was #1763 (plant_id OCR: 6JQJ+4C5)
        "1_kD1-RNTRTK1PYX-mrOmzXEyJYZ1vhHn",  # was #1815 (plant_id OCR: address)
    }
)

# All member photos of those clusters (prevents orphan photos reappearing).
# Keep in sync with plant_state meta.outlier_exclusions.member_file_ids.
EXCLUDED_OUTLIER_FILE_IDS = frozenset(
    {
        "12wyIMKKL6BBg1yJcfaXHQEIvDS-q6WvQ",
        "13TxYQ2LEUh1H5esx9ZbpvzUp33TJqj49",
        "14U2Kdruh-1fK6bE4tsFglJLbLXVt7ZNZ",
        "16JC4B56I4gfsZ42LfxXO_QaBw66CdSux",
        "16b-gtlR4tHPRJxKWOUpuIHr7Xa77keX-",
        "17msK1hbrE4NkB2tJu_wm_RdTzzNoby_2",
        "19PUKAx6PD9UkLHqVf01si5Okbk9KFFDk",
        "1Btgxaim8AqdrckPteyjAV6y3DracAfzW",
        "1CWXkMr4-zmObF64lrlnHUxuvwz2dAdgc",
        "1Cv-4JTVPizoVS1uxZkCv3BK4Fz7kHKKM",
        "1Da5hcL6x0m4MhEZp3CHUk_aRjTlTuuT2",
        "1EPb-gpPYesQGKYYWXlRUc_10e5Hx0cuM",
        "1FE0f5O3Gwn42Q91tllurTbT_nMeNp6fD",
        "1GIhEN8SkpTXJL0u23DekXWTVyWU34Wt6",
        "1JB0_9zZYaNddPiGjcz5iTjSCh_v5J5WK",
        "1JScZuKol8Ul35UfHj6vm03HTkN7H7DEr",
        "1JttqQL3xtvN2w59bA88PGvb1qnwystlK",
        "1K0I8uvW2ysNSDbz-eKWwOn_GNG5jL3wW",
        "1KQyCOuwPgJSkduu1zq9pjuAYN_von-NF",
        "1NxK94UqB21Y3giNqchq1j7sfyx1QNkw-",
        "1ORYms5w1FJsLWeY-3fjRD7dnjJ2XjWz2",
        "1RmS82sjLGj-72oIZ5e13lUbNyOHQ6P9I",
        "1SU8jnTdii_OEwsdIQ212fcxfClUkvjSg",
        "1TbTuj6lg8X-CS35gjl7so0d6tyYguoq8",
        "1YE-NzMicOcR9qXg6GR35mm4__1noq3xP",
        "1_kD1-RNTRTK1PYX-mrOmzXEyJYZ1vhHn",
        "1ack2PMThELXfHMwdPfq-0JxVdjf7BFtz",
        "1bCYG8hDTt7i8K_2pG6Ywyh2JRRGcIt0p",
        "1eRZPo-jEKmbHkY0LnZpZprtvndp4ZeNM",
        "1fbiOBAduTJ2Ht0snbSQmd6Ds0VdDmi-S",
        "1h4p6LktBYUS01nSG8Lx2WDW5u17QzRqY",
        "1h6B9VLgXCe72I8KqufDSXk33TDFxRvtA",
        "1lDVy9pAi8koLxw40iXkSHRdPlaoACwr_",
        "1mW1QnW4LncqxjUjxK_eP7ZFgfYLAmMam",
        "1nDMXLVYLOF42ubJgLGc3RK_621mxA5S4",
        "1qhZTxFhMugr_xyTGs0n2kAnUUJ4uvSPB",
        "1thNiRv_1tlkJPqt5O4NfXIqWTsrrWZaD",
        "1usSuihEW7kmxCw3T5RzaTPvnWwn-Pq3d",
        "1vjjyCGXlr_rLcudOprW0_rGCMsvU8hA3",
        "1xD6TRogKDL3tRdKsLjXpItJIkh2FaNpV",
    }
)

ICON_URLS = {
    "green": "http://maps.google.com/mapfiles/kml/paddle/grn-circle.png",
    "amber": "http://maps.google.com/mapfiles/kml/paddle/ylw-circle.png",
    "red": "http://maps.google.com/mapfiles/kml/paddle/red-circle.png",
    "white": "http://maps.google.com/mapfiles/kml/paddle/wht-circle.png",
}


def ensure_dirs():
    _migrate_credentials()
    for path in (CREDENTIALS_DIR, _REPO_CREDENTIALS_DIR, CACHE_DIR, PHOTOS_DIR, OUTPUT_DIR):
        path.mkdir(parents=True, exist_ok=True)
    _seed_bundled_state()


def _seed_bundled_state() -> None:
    """
    On Streamlit Cloud (empty cache), copy bundled farm map state so Map view
    works immediately. Photos download on demand from Drive when opened.
    """
    bundled = ROOT / "data" / "plant_state.json"
    if not bundled.exists():
        return

    needs_seed = True
    if STATE_PATH.exists():
        try:
            existing = json.loads(STATE_PATH.read_text(encoding="utf-8"))
            obs = existing.get("observations") or []
            # Keep richer local/cloud state; only replace empty shells
            if len(obs) >= 10:
                needs_seed = False
        except Exception:
            needs_seed = True

    if needs_seed:
        try:
            STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
            STATE_PATH.write_bytes(bundled.read_bytes())
        except Exception:
            pass

    exports = ROOT / "data" / "exports"
    if not exports.exists():
        return
    for name in ("palm_health_consolidated.kml", "palm_health_consolidated.json"):
        src = exports / name
        dest = OUTPUT_DIR / name
        if src.exists() and (not dest.exists() or dest.stat().st_size < 1000):
            try:
                OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(src.read_bytes())
            except Exception:
                pass
