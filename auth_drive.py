"""One-time Google Drive login (run outside Streamlit — required for Cloud photos)."""
from __future__ import annotations

import sys
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from google_auth_oauthlib.flow import InstalledAppFlow  # noqa: E402

from config import (  # noqa: E402
    CREDENTIALS_FILE,
    DRIVE_SCOPES,
    TOKEN_FILE,
    _REPO_CREDENTIALS_DIR,
    ensure_dirs,
)


def _save_token(creds) -> None:
    text = creds.to_json()
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.write_text(text, encoding="utf-8")
    try:
        _REPO_CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
        (_REPO_CREDENTIALS_DIR / "token.json").write_text(text, encoding="utf-8")
    except Exception:
        pass


def main() -> None:
    ensure_dirs()
    if not CREDENTIALS_FILE.exists():
        raise SystemExit(
            "Missing OAuth client file: %s\n"
            "Put credentials.json there (Desktop OAuth client)." % CREDENTIALS_FILE
        )

    # Drop revoked/expired tokens so we always do a fresh browser consent
    for path in (TOKEN_FILE, _REPO_CREDENTIALS_DIR / "token.json"):
        try:
            if path.exists():
                path.unlink()
                print("Removed old token: %s" % path)
        except Exception as exc:
            print("Could not remove %s: %s" % (path, exc))

    print("Starting Google Drive login…")
    print("Sign in with the Google account that owns the farm photos.")

    flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), DRIVE_SCOPES)
    creds = None
    last_err = None
    # Try several ports — a previous hung login often leaves 8090 occupied
    for port in (8090, 8091, 8092, 0):
        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE), DRIVE_SCOPES
            )
            creds = flow.run_local_server(
                port=port,
                open_browser=True,
                prompt="consent",
                access_type="offline",
                authorization_prompt_message="Opening browser for Google Drive login…",
                success_message="Drive login OK. You can close this tab and return to the terminal.",
            )
            break
        except Exception as exc:
            last_err = exc
            print("Port %s failed: %s" % (port, exc))

    if creds is None:
        print("Automatic browser callback failed (%s)." % last_err)
        print("Manual login:")
        flow = InstalledAppFlow.from_client_secrets_file(
            str(CREDENTIALS_FILE), DRIVE_SCOPES
        )
        auth_url, _ = flow.authorization_url(
            access_type="offline",
            prompt="consent",
            include_granted_scopes="true",
        )
        print()
        print(auth_url)
        print()
        try:
            webbrowser.open(auth_url)
        except Exception:
            pass
        code = input("After signing in, paste the authorization code here: ").strip()
        if not code:
            raise SystemExit("No code entered — login cancelled.")
        flow.fetch_token(code=code)
        creds = flow.credentials

    _save_token(creds)
    print("Success. Token saved to: %s" % TOKEN_FILE)
    print("Next: python make_cloud_secrets.py")
    print("Then paste GOOGLE_*_B64 into Streamlit Cloud Secrets and reboot the app.")


if __name__ == "__main__":
    main()
