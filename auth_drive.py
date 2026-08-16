"""One-time Google Drive login (run outside Streamlit — much faster/reliable)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import TOKEN_FILE, ensure_dirs  # noqa: E402
from services.drive import get_credentials  # noqa: E402


def main():
    ensure_dirs()
    print("Starting Google Drive login…")
    print("A browser window will open. Sign in with the account that owns the photos.")
    get_credentials(interactive=True)
    print("Success. Token saved to: %s" % TOKEN_FILE)
    print("You can now use Streamlit: streamlit run app.py")


if __name__ == "__main__":
    main()
