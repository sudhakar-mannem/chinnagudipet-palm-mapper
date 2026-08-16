"""Print TOML-safe base64 secrets for Streamlit Community Cloud.

Run:
  python make_cloud_secrets.py

Then paste the printed lines into Cloud → Manage app → Settings → Secrets.
Does not print raw tokens — only base64 blobs.
"""
from __future__ import annotations

import base64
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def b64_file(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


def main() -> None:
    cred = ROOT / "credentials" / "credentials.json"
    tok = ROOT / "credentials" / "token.json"
    print("# Paste into Streamlit Community Cloud Secrets (TOML-safe)")
    print("# Remove any old GOOGLE_*_JSON lines that failed validation.")
    print()
    if cred.exists():
        print('GOOGLE_CREDENTIALS_B64 = "%s"' % b64_file(cred))
        print()
    else:
        print("# missing credentials/credentials.json")
    if tok.exists():
        print('GOOGLE_TOKEN_B64 = "%s"' % b64_file(tok))
        print()
    else:
        print("# missing credentials/token.json — run: python auth_drive.py")
    out = ROOT / ".streamlit" / "secrets_cloud_snippet.toml"
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Auto-generated — do not commit", ""]
    if cred.exists():
        lines.append('GOOGLE_CREDENTIALS_B64 = "%s"' % b64_file(cred))
        lines.append("")
    if tok.exists():
        lines.append('GOOGLE_TOKEN_B64 = "%s"' % b64_file(tok))
        lines.append("")
    out.write_text("\n".join(lines), encoding="utf-8")
    print("Also wrote: %s" % out)
    print("(This file is gitignored if named under secrets*; keep it private.)")


if __name__ == "__main__":
    main()
