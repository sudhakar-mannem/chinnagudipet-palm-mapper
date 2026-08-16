"""Google Drive photo sync."""
from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from config import CREDENTIALS_FILE, DRIVE_FOLDER_ID, DRIVE_SCOPES, PHOTOS_DIR, TOKEN_FILE, ensure_dirs


IMAGE_MIME_PREFIXES = ("image/",)
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".tif", ".tiff"}


class DriveAuthRequired(RuntimeError):
    """Raised when interactive Google login is needed (do this via auth_drive.py)."""


def get_credentials(interactive: bool = False) -> Credentials:
    """Load/refresh Drive credentials. Interactive login only when interactive=True."""
    ensure_dirs()
    if not CREDENTIALS_FILE.exists():
        raise FileNotFoundError(
            "Missing credentials/credentials.json.\n"
            "Create a Desktop OAuth client in Google Cloud Console, enable the "
            "Google Drive API, and save the JSON as credentials/credentials.json."
        )

    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), DRIVE_SCOPES)

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
        except Exception:
            creds = None

    if not creds or not creds.valid:
        if not interactive:
            raise DriveAuthRequired(
                "Google Drive is not authenticated yet.\n"
                "Run this once in a terminal (fast, outside Streamlit):\n\n"
                "  python auth_drive.py\n"
            )
        flow = InstalledAppFlow.from_client_secrets_file(
            str(CREDENTIALS_FILE), DRIVE_SCOPES
        )
        # Fixed port is more reliable/faster than port=0 inside some environments
        creds = flow.run_local_server(
            port=8090,
            open_browser=True,
            prompt="consent",
            authorization_prompt_message="Opening browser for Google Drive login…",
            success_message="Drive login OK. You can close this tab and return to the app.",
        )
        TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")

    return creds


def get_drive_service(interactive: bool = False):
    """Authenticate with Google Drive and return API client."""
    creds = get_credentials(interactive=interactive)
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def _is_image(file_meta: Dict[str, Any]) -> bool:
    mime = (file_meta.get("mimeType") or "").lower()
    name = (file_meta.get("name") or "").lower()
    if any(mime.startswith(p) for p in IMAGE_MIME_PREFIXES):
        return True
    return Path(name).suffix in IMAGE_EXTENSIONS


def _list_children(service, parent_id: str) -> List[Dict[str, Any]]:
    """List non-trashed children of a Drive folder."""
    items: List[Dict[str, Any]] = []
    page_token = None
    query = "'%s' in parents and trashed = false" % parent_id
    while True:
        resp = (
            service.files()
            .list(
                q=query,
                spaces="drive",
                fields=(
                    "nextPageToken, files(id, name, mimeType, modifiedTime, "
                    "createdTime, size, webViewLink, thumbnailLink, md5Checksum)"
                ),
                pageSize=200,
                pageToken=page_token,
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
            )
            .execute()
        )
        items.extend(resp.get("files", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return items


def list_subfolders(
    root_folder_id: Optional[str] = None,
    recursive: bool = True,
    service=None,
) -> List[Dict[str, Any]]:
    """
    List subfolders under the palm photos root.

    Returns dicts: id, name, path (e.g. "10Aug/Block-A"), parent_id.
    """
    service = service or get_drive_service(interactive=False)
    root_folder_id = root_folder_id or DRIVE_FOLDER_ID
    found: List[Dict[str, Any]] = []
    # queue items: (folder_id, path_prefix)
    queue: List[Any] = [(root_folder_id, "")]

    while queue:
        current_id, prefix = queue.pop(0)
        for item in _list_children(service, current_id):
            if item.get("mimeType") != "application/vnd.google-apps.folder":
                continue
            name = item.get("name") or "Untitled"
            path = "%s/%s" % (prefix, name) if prefix else name
            found.append(
                {
                    "id": item["id"],
                    "name": name,
                    "path": path,
                    "parent_id": current_id,
                    "modifiedTime": item.get("modifiedTime") or "",
                }
            )
            if recursive:
                queue.append((item["id"], path))

    found.sort(key=lambda f: f.get("path", "").lower())
    return found


def list_folder_images(
    service=None,
    folder_id: Optional[str] = None,
    folder_ids: Optional[List[str]] = None,
    recursive: bool = True,
) -> List[Dict[str, Any]]:
    """List image files in one or more Drive folders (optionally nested)."""
    service = service or get_drive_service(interactive=False)
    if folder_ids:
        roots = [fid for fid in folder_ids if fid]
    else:
        roots = [folder_id or DRIVE_FOLDER_ID]

    results: List[Dict[str, Any]] = []
    seen_ids = set()
    folders = list(roots)

    while folders:
        current = folders.pop(0)
        for item in _list_children(service, current):
            mime = item.get("mimeType", "")
            if mime == "application/vnd.google-apps.folder":
                if recursive:
                    folders.append(item["id"])
            elif _is_image(item):
                if item["id"] in seen_ids:
                    continue
                seen_ids.add(item["id"])
                entry = dict(item)
                entry["source_folder_id"] = current
                results.append(entry)

    results.sort(key=lambda f: f.get("modifiedTime") or "", reverse=True)
    return results


def download_file(service, file_id: str, dest: Path) -> Path:
    """Download a Drive file to dest."""
    ensure_dirs()
    dest.parent.mkdir(parents=True, exist_ok=True)
    request = service.files().get_media(fileId=file_id, supportsAllDrives=True)
    buffer = io.BytesIO()
    downloader = MediaIoBaseDownload(buffer, request, chunksize=1024 * 1024)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    dest.write_bytes(buffer.getvalue())
    return dest


def sync_photos(
    folder_id: Optional[str] = None,
    folder_ids: Optional[List[str]] = None,
    force: bool = False,
) -> List[Dict[str, Any]]:
    """
    Download new/changed photos from Drive into the local cache folder.

    Prefer folder_ids (selected subfolders). Falls back to folder_id / root.
    """
    ensure_dirs()
    service = get_drive_service(interactive=False)
    files = list_folder_images(
        service,
        folder_id=folder_id,
        folder_ids=folder_ids,
        recursive=True,
    )
    synced: List[Dict[str, Any]] = []
    manifest_path = PHOTOS_DIR / "_manifest.json"
    manifest: Dict[str, Any] = {}
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            manifest = {}

    for meta in files:
        file_id = meta["id"]
        name = meta["name"]
        safe_name = "%s__%s" % (file_id, Path(name).name)
        local_path = PHOTOS_DIR / safe_name
        checksum = meta.get("md5Checksum") or meta.get("modifiedTime") or ""
        previous = manifest.get(file_id, {})
        needs_download = force or (not local_path.exists()) or previous.get("checksum") != checksum

        if needs_download:
            download_file(service, file_id, local_path)
            manifest[file_id] = {
                "checksum": checksum,
                "name": name,
                "local_path": str(local_path),
                "modifiedTime": meta.get("modifiedTime"),
            }

        entry = dict(meta)
        entry["local_path"] = str(local_path)
        entry["photo_url"] = "https://drive.google.com/uc?export=view&id=%s" % file_id
        synced.append(entry)

    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return synced
