"""Palm Plant Health Mapper — Streamlit app (kept light for responsiveness)."""
from __future__ import annotations

import hashlib
import io
import os
import sys
from pathlib import Path
from typing import List, Optional

import folium
import pandas as pd
import streamlit as st
from PIL import Image
from streamlit_folium import st_folium

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import (  # noqa: E402
    CACHE_DIR,
    CREDENTIALS_FILE,
    DRIVE_FOLDER_ID,
    HEALTH_COLORS,
    OUTPUT_DIR,
    STATE_PATH,
    TOKEN_FILE,
    ensure_dirs,
    openai_key_configured,
    reload_env,
)
from services.drive import (  # noqa: E402
    DriveAuthRequired,
    ensure_local_photo,
    fetch_drive_thumbnail_url,
    list_subfolders,
)
from services.models import (  # noqa: E402
    DEFAULT_PHOTO_RADIUS_M,
    PlantCluster,
    PlantObservation,
    cluster_by_radius,
    haversine_m,
)
from services.pipeline import load_state, run_pipeline  # noqa: E402

st.set_page_config(
    page_title="Palm Plant Health Mapper",
    page_icon="🌴",
    layout="wide",
)

ensure_dirs()
reload_env()

THUMBS_DIR = CACHE_DIR / "thumbs"
THUMBS_DIR.mkdir(parents=True, exist_ok=True)

try:
    import inspect as _inspect

    _img_params = _inspect.signature(st.image).parameters
    if "use_container_width" in _img_params:
        _IMAGE_WIDTH_KW = {"use_container_width": True}
    elif "use_column_width" in _img_params:
        _IMAGE_WIDTH_KW = {"use_column_width": True}
    else:
        _IMAGE_WIDTH_KW = {}
except Exception:
    _IMAGE_WIDTH_KW = {"use_column_width": True}


def setup_ok():
    reload_env()
    return {
        "openai": openai_key_configured(),
        "credentials": CREDENTIALS_FILE.exists(),
        "token": TOKEN_FILE.exists(),
        "folder": bool(DRIVE_FOLDER_ID),
    }


@st.cache_data(show_spinner=False)
def observations_from_state(_mtime: float):
    state = load_state()
    return [PlantObservation.from_dict(x) for x in state.get("observations", [])]


@st.cache_data(show_spinner=False, ttl=300)
def cached_subfolders(root_id: str, _token_mtime: float):
    return list_subfolders(root_folder_id=root_id, recursive=True)


@st.cache_data(show_spinner=False)
def load_thumbnail_bytes(path_str: str, mtime: float, max_side: int = 480) -> Optional[bytes]:
    """
    Fast display thumbnails: disk-cached JPEG so Streamlit never ships
    multi‑MB field photos into the browser on every rerun.
    """
    path = Path(path_str)
    if not path.exists():
        return None
    key = hashlib.md5(("%s|%s|%d" % (path_str, mtime, max_side)).encode("utf-8")).hexdigest()
    thumb_path = THUMBS_DIR / ("%s.jpg" % key)
    if thumb_path.exists():
        try:
            return thumb_path.read_bytes()
        except Exception:
            pass
    try:
        with Image.open(path) as img:
            # Faster JPEG decode when only a preview is needed
            if getattr(img, "format", None) == "JPEG":
                try:
                    img.draft("RGB", (max_side, max_side))
                except Exception:
                    pass
            img = img.convert("RGB")
            img.thumbnail((max_side, max_side), Image.BILINEAR)
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=72, optimize=True)
            data = buf.getvalue()
        try:
            thumb_path.write_bytes(data)
        except Exception:
            pass
        return data
    except Exception:
        return None


def show_fast_image(path: Path, caption: str = "", max_side: int = 480) -> bool:
    """Show a cached thumbnail; return False if the file could not be loaded."""
    try:
        mtime = path.stat().st_mtime
    except OSError:
        return False
    data = load_thumbnail_bytes(str(path), mtime, max_side=max_side)
    if not data:
        return False
    # Fixed width avoids stretching huge originals through the Streamlit image pipeline
    st.image(data, caption=caption or None, width=min(max_side, 420))
    return True


@st.cache_data(show_spinner=False, ttl=3600)
def load_drive_preview_bytes(file_id: str) -> Optional[bytes]:
    """Fetch a small Drive preview (thumbnail) without downloading the full photo."""
    if not file_id:
        return None
    try:
        import urllib.request

        url = fetch_drive_thumbnail_url(file_id)
        if not url:
            return None
        req = urllib.request.Request(url, headers={"User-Agent": "PalmMapper/1.0"})
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = resp.read()
        return data if data else None
    except Exception:
        return None


def resolve_photo_preview(photo: PlantObservation):
    """
    Fast resolve order:
    1) local file (no Drive download)
    2) Drive thumbnail bytes
    Returns (local_path_or_None, preview_bytes_or_None).
    """
    local = ensure_local_photo(
        photo.file_id or "",
        photo.file_name or "",
        photo.local_path,
        download=False,
    )
    if local and local.exists():
        return local, None
    preview = load_drive_preview_bytes(photo.file_id or "")
    return None, preview


def open_in_google_earth(path: Path) -> str:
    if not path.exists():
        return "File not found: %s" % path
    try:
        if sys.platform.startswith("win"):
            os.startfile(str(path))  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            os.system('open "%s"' % path)
        else:
            os.system('xdg-open "%s"' % path)
        return "Opened in Google Earth: %s" % path.name
    except Exception as exc:
        return "Could not open Google Earth (%s). Open the file manually: %s" % (exc, path)


def build_map(clusters: List[PlantCluster]):
    mapped = [c for c in clusters if c.representative.latitude is not None]
    if not mapped:
        return None
    center_lat = sum(c.representative.latitude for c in mapped) / len(mapped)
    center_lon = sum(c.representative.longitude for c in mapped) / len(mapped)
    fmap = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=17,
        tiles=None,
        max_zoom=21,
        control_scale=True,
    )
    folium.TileLayer(
        tiles="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
        attr="Google",
        name="Google Hybrid",
        max_zoom=21,
        overlay=False,
        control=True,
    ).add_to(fmap)
    folium.TileLayer(
        tiles="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
        attr="Google",
        name="Google Satellite",
        max_zoom=21,
        overlay=False,
        control=True,
    ).add_to(fmap)
    folium.TileLayer(
        tiles="https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
        attr="Google",
        name="Google Roadmap",
        max_zoom=21,
        overlay=False,
        control=True,
    ).add_to(fmap)

    for c in mapped:
        p = c.representative
        color = HEALTH_COLORS.get(p.health, HEALTH_COLORS["white"])["hex"]
        title = p.plant_id or Path(p.file_name).stem
        label = HEALTH_COLORS.get(p.health, HEALTH_COLORS["white"])["label"]
        popup = folium.Popup(
            "<b>%s</b><br/>%s<br/>%d photo(s) — see panel →"
            % (title, label, c.photo_count),
            max_width=220,
        )
        folium.CircleMarker(
            location=[p.latitude, p.longitude],
            radius=8,
            color="#111",
            weight=1,
            fill=True,
            fill_color=color,
            fill_opacity=0.92,
            popup=popup,
            tooltip="%s · %d photos" % (title, c.photo_count),
        ).add_to(fmap)

    folium.LayerControl().add_to(fmap)
    return fmap


def nearest_cluster_index(clusters, lat, lon):
    best_i = 0
    best_d = 1e18
    for i, c in enumerate(clusters):
        p = c.representative
        if p.latitude is None or p.longitude is None:
            continue
        d = haversine_m(lat, lon, float(p.latitude), float(p.longitude))
        if d < best_d:
            best_d = d
            best_i = i
    return best_i


def load_all_clusters() -> List[PlantCluster]:
    state_mtime = STATE_PATH.stat().st_mtime if STATE_PATH.exists() else 0.0
    all_obs = observations_from_state(state_mtime)
    return cluster_by_radius(
        [o for o in all_obs if o.latitude is not None],
        radius_m=DEFAULT_PHOTO_RADIUS_M,
    )


def render_photo_panel(cluster: PlantCluster) -> None:
    """Show plant photos as small cached thumbnails (paginated, plant-scoped keys)."""
    selected = cluster.representative
    plant_key = (
        selected.plant_id
        or selected.file_id
        or Path(selected.file_name or "plant").stem
    )
    # Isolate this plant's widgets so Streamlit does not reuse the previous plant's image UI
    panel = st.container()
    with panel:
        st.write(
            "**%s** — %s · **%d** photo(s) within %.0f m"
            % (
                selected.plant_id or Path(selected.file_name).stem,
                HEALTH_COLORS.get(selected.health, HEALTH_COLORS["white"])["label"],
                cluster.photo_count,
                cluster.radius_m,
            )
        )
        if selected.source_folder_path:
            st.caption(selected.source_folder_path)
        if selected.summary:
            st.caption(selected.summary)
        if selected.altitude is not None:
            st.caption("Altitude: %.1f m" % selected.altitude)

        max_show = int(st.session_state.get("photo_page_size") or 1)
        members = cluster.members
        total = len(members)
        show_n = min(max_show, total)

        shown = 0
        for idx, photo in enumerate(members[:show_n]):
            file_key = photo.file_id or ("%s_%d" % (plant_key, idx))
            st.markdown(
                "**%s%d / %d** — `%s` · alt %s"
                % (
                    "LATEST · " if idx == 0 else "",
                    idx + 1,
                    total,
                    photo.file_name,
                    ("%.1f m" % photo.altitude) if photo.altitude is not None else "n/a",
                )
            )
            local, preview = resolve_photo_preview(photo)
            if local and local.exists():
                ok = show_fast_image(local, caption=photo.file_name or local.name, max_side=420)
                if ok:
                    shown += 1
                else:
                    st.warning("Could not load preview")
                with st.expander("Full-size image", expanded=False):
                    # Reuse thumb-sized decode — avoid shipping multi-MB originals through Streamlit
                    show_fast_image(local, caption="", max_side=900)
            elif preview:
                st.image(preview, caption=photo.file_name or "Drive preview", width=420)
                shown += 1
                download_key = "dl_photo_%s" % file_key
                if st.button("Download full photo", key=download_key):
                    with st.spinner("Downloading from Drive…"):
                        got = ensure_local_photo(
                            photo.file_id or "",
                            photo.file_name or "",
                            photo.local_path,
                            download=True,
                        )
                    if got and got.exists():
                        st.rerun()
                    else:
                        st.error("Download failed. Check Drive connection.")
            else:
                # Auto-fetch only the latest photo so a map click still shows something
                if idx == 0 and (photo.file_id or ""):
                    with st.spinner("Loading latest photo…"):
                        got = ensure_local_photo(
                            photo.file_id or "",
                            photo.file_name or "",
                            photo.local_path,
                            download=True,
                        )
                    if got and got.exists():
                        ok = show_fast_image(
                            got, caption=photo.file_name or got.name, max_side=420
                        )
                        if ok:
                            shown += 1
                            continue
                st.info("Preview not cached yet.")
                load_key = "load_photo_%s" % file_key
                if st.button("Load photo from Drive", key=load_key, type="primary"):
                    with st.spinner("Downloading from Drive…"):
                        got = ensure_local_photo(
                            photo.file_id or "",
                            photo.file_name or "",
                            photo.local_path,
                            download=True,
                        )
                    if got and got.exists():
                        st.rerun()
                    else:
                        st.error("Could not download. Connect Google Drive and try again.")
                if photo.photo_url:
                    st.markdown("[Open in Google Drive](%s)" % photo.photo_url)

        if total > show_n:
            if st.button(
                "Show more photos (%d remaining)" % (total - show_n),
                key="more_photos_%s" % plant_key,
            ):
                st.session_state["photo_page_size"] = show_n + 1
                st.rerun()
        elif total > 1 and max_show > 1:
            if st.button("Show fewer photos", key="fewer_photos_%s" % plant_key):
                st.session_state["photo_page_size"] = 1
                st.rerun()

        if shown == 0 and total:
            st.caption("Tip: connect Google Drive in the sidebar if previews stay empty.")


def handle_google_auth(connect_clicked: bool, disconnect_clicked: bool) -> None:
    if disconnect_clicked and TOKEN_FILE.exists():
        try:
            TOKEN_FILE.unlink()
        except Exception as exc:
            st.error("Could not disconnect: %s" % exc)
        else:
            cached_subfolders.clear()
            for key in ("drive_folders", "folders_loaded", "selected_folder_paths"):
                st.session_state.pop(key, None)
            st.success("Disconnected from Google Drive.")
            st.rerun()

    if connect_clicked:
        status = setup_ok()
        if not status["credentials"]:
            st.error("Add credentials/credentials.json first.")
            return
        with st.spinner(
            "Opening your browser for Google sign-in… Complete login there, then return here."
        ):
            try:
                from services.drive import get_credentials

                get_credentials(interactive=True)
                cached_subfolders.clear()
                st.session_state["folders_loaded"] = True
                st.success("Google Drive connected.")
                st.rerun()
            except Exception as exc:
                st.error("Google login failed: %s" % exc)
                st.info(
                    "If the browser did not open, run once in a terminal:\n\n"
                    "`python auth_drive.py`"
                )


def page_map_view() -> None:
    st.title("Farm map")
    st.caption("Click a plant marker to preview photos. Use **Plant Mapping** in the sidebar to sync new Drive folders.")

    clusters = load_all_clusters()
    health_filter = st.multiselect(
        "Filter by health",
        options=["green", "amber", "red", "white"],
        default=["green", "amber", "red", "white"],
        key="map_health_filter",
    )
    if health_filter:
        clusters = [c for c in clusters if c.representative.health in health_filter]

    counts = {"green": 0, "amber": 0, "red": 0, "white": 0}
    for c in clusters:
        h = c.representative.health if c.representative.health in counts else "white"
        counts[h] += 1

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Plants on map", len(clusters))
    m2.metric("Green", counts["green"])
    m3.metric("Amber", counts["amber"])
    m4.metric("Red", counts["red"])
    m5.metric("White", counts["white"])

    left, right = st.columns([1.55, 1])
    with left:
        if clusters:
            fmap = build_map(clusters)
            if fmap:
                map_state = st_folium(
                    fmap,
                    height=620,
                    width=None,
                    use_container_width=True,
                    returned_objects=["last_object_clicked"],
                    key="palm_map_main",
                )
                clicked = (map_state or {}).get("last_object_clicked")
                if clicked and clicked.get("lat") is not None:
                    sig = (
                        round(float(clicked["lat"]), 6),
                        round(float(clicked["lng"]), 6),
                    )
                    # Only react to a new click — st_folium keeps returning the last click
                    if st.session_state.get("_map_click_sig") != sig:
                        idx = nearest_cluster_index(
                            clusters, float(clicked["lat"]), float(clicked["lng"])
                        )
                        st.session_state["_map_click_sig"] = sig
                        st.session_state["selected_cluster_idx"] = idx
                        # Selectbox with a key ignores index= — sync state explicitly
                        st.session_state["plant_select_main"] = idx
                        st.session_state["photo_page_size"] = 1
                        st.rerun()
        else:
            st.info(
                "No mapped plants yet. Open **Plant Mapping** in the sidebar to connect Drive and run analysis."
            )

    with right:
        st.subheader("Photos within %.0f m" % DEFAULT_PHOTO_RADIUS_M)
        if not clusters:
            st.write("No plants yet.")
            return

        labels = []
        for i, c in enumerate(clusters):
            p = c.representative
            labels.append(
                "%s | %s | %d photo(s)"
                % (
                    p.plant_id or Path(p.file_name).stem,
                    p.health,
                    c.photo_count,
                )
            )
        default_idx = int(st.session_state.get("selected_cluster_idx") or 0)
        if default_idx >= len(clusters):
            default_idx = 0
        if "plant_select_main" not in st.session_state:
            st.session_state["plant_select_main"] = default_idx
        # Clamp if plant list shrank
        if int(st.session_state["plant_select_main"]) >= len(clusters):
            st.session_state["plant_select_main"] = 0

        prev_choice = int(st.session_state.get("selected_cluster_idx") or 0)
        choice = st.selectbox(
            "Select plant",
            options=list(range(len(clusters))),
            format_func=lambda i: labels[i],
            key="plant_select_main",
        )
        if choice != prev_choice:
            st.session_state["photo_page_size"] = 1
        st.session_state["selected_cluster_idx"] = choice
        render_photo_panel(clusters[choice])

    with st.expander("Open / download Google Earth files", expanded=False):
        consolidated_kml = OUTPUT_DIR / "palm_health_consolidated.kml"
        consolidated_kmz = OUTPUT_DIR / "palm_health_consolidated.kmz"
        earth_folder = OUTPUT_DIR / "palm_health_consolidated_earth_folder"
        earth_open = earth_folder / "doc_absolute.kml"
        if not earth_open.exists():
            earth_open = earth_folder / "OPEN_ME.kml"
        target = earth_open if earth_open.exists() else consolidated_kmz
        c1, c2 = st.columns(2)
        with c1:
            if target.exists() and st.button("Open consolidated in Google Earth", type="primary"):
                st.success(open_in_google_earth(target))
        with c2:
            if consolidated_kml.exists():
                st.download_button(
                    "Download consolidated KML",
                    data=consolidated_kml.read_bytes(),
                    file_name="palm_health_consolidated.kml",
                    mime="application/vnd.google-earth.kml+xml",
                )


def page_plant_mapping() -> None:
    st.title("Plant Mapping")
    st.caption("Connect Google Drive, choose folders, and run health + GPS/altitude analysis.")

    secret_status = reload_env() or {}
    status = setup_ok()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("OpenAI key", "Ready" if status["openai"] else "Missing")
    c2.metric("Drive credentials", "Ready" if status["credentials"] else "Missing")
    c3.metric("Drive login", "Connected" if status["token"] else "Not yet")
    c4.metric("Folder ID", "Set" if status["folder"] else "Missing")

    with st.expander("Cloud secrets status", expanded=not status["token"]):
        st.write(
            {
                "secrets_available": secret_status.get("secrets_available"),
                "openai_from_secrets": secret_status.get("openai_from_secrets"),
                "credentials_written": secret_status.get("credentials_written"),
                "token_written": secret_status.get("token_written"),
                "credentials_error": secret_status.get("credentials_error") or "(none)",
                "token_error": secret_status.get("token_error") or "(none)",
                "credentials_file_exists": CREDENTIALS_FILE.exists(),
                "token_file_exists": TOKEN_FILE.exists(),
            }
        )
        if not status["token"]:
            st.warning(
                "Drive login needs `GOOGLE_TOKEN_B64` (recommended) or `GOOGLE_TOKEN_JSON`. "
                "Locally run `python make_cloud_secrets.py` and paste the printed lines "
                "into Cloud Secrets. Remove any old invalid GOOGLE_*_JSON lines first."
            )

    st.subheader("Connect to Google Drive")
    gc1, gc2, gc3 = st.columns([1.2, 1, 2])
    with gc1:
        main_connect = st.button(
            "Connect to Google Drive",
            type="primary",
            use_container_width=True,
            disabled=not status["credentials"],
            key="main_connect_google",
        )
    with gc2:
        main_disconnect = st.button(
            "Disconnect",
            use_container_width=True,
            disabled=not status["token"],
            key="main_disconnect_google",
        )
    with gc3:
        if not status["credentials"]:
            st.error("Missing `credentials/credentials.json`.")
        elif status["token"]:
            st.success("Google Drive is connected.")
        else:
            st.warning("Not connected — click **Connect to Google Drive**.")

    handle_google_auth(bool(main_connect), bool(main_disconnect))
    status = setup_ok()

    st.subheader("1. Select folders")
    root_folder_id = st.text_input(
        "Root Google Drive folder ID",
        value=DRIVE_FOLDER_ID,
        help="Top-level palm photos folder.",
    )
    refresh = st.button(
        "Refresh folder list",
        use_container_width=True,
        disabled=not status["token"],
    )
    if refresh:
        cached_subfolders.clear()
        st.session_state["folders_loaded"] = True

    folders = []
    folder_error = None
    if status["token"] and (
        refresh
        or st.session_state.get("folders_loaded")
        or st.session_state.get("drive_folders")
    ):
        try:
            token_mtime = TOKEN_FILE.stat().st_mtime if TOKEN_FILE.exists() else 0.0
            folders = cached_subfolders(root_folder_id, token_mtime)
            st.session_state["drive_folders"] = folders
            st.session_state["folders_loaded"] = True
        except DriveAuthRequired as exc:
            folder_error = str(exc)
        except Exception as exc:
            folder_error = str(exc)
    elif st.session_state.get("drive_folders"):
        folders = st.session_state["drive_folders"]

    if folder_error:
        st.error(folder_error)
    elif not status["token"]:
        st.info("Connect to Google Drive, then refresh the folder list.")
    elif not folders and not st.session_state.get("folders_loaded"):
        st.info("Click **Refresh folder list**.")
    elif not folders:
        st.warning("No subfolders found under this root.")
    else:
        path_options = [f["path"] for f in folders]
        default_paths = [
            p for p in st.session_state.get("selected_folder_paths", [])
            if p in path_options
        ]
        selected_paths = st.multiselect(
            "Folders to process",
            options=path_options,
            default=default_paths,
        )
        st.session_state["selected_folder_paths"] = selected_paths
        st.caption("%d of %d folder(s) selected" % (len(selected_paths), len(path_options)))

    with st.expander("Advanced options", expanded=False):
        process_entire_root = st.checkbox(
            "Process entire farm root (all nested photos)",
            value=False,
            key="opt_entire_root",
        )
        start_fresh = st.checkbox(
            "Start fresh (clear previous analysis + exports)",
            value=False,
            key="opt_fresh",
        )
        reanalyze = st.checkbox(
            "Re-analyze photos already cached",
            value=False,
            key="opt_reanalyze",
        )
        force_dl = st.checkbox("Re-download all photos from Drive", value=False, key="opt_force_dl")
        st.caption("Cache: `%s`" % CACHE_DIR)

    process_entire_root = st.session_state.get("opt_entire_root", False)
    start_fresh = st.session_state.get("opt_fresh", False)
    reanalyze = st.session_state.get("opt_reanalyze", False)
    force_dl = st.session_state.get("opt_force_dl", False)

    selected_paths = st.session_state.get("selected_folder_paths") or []
    selected_folders = []
    if st.session_state.get("drive_folders"):
        by_path = {f["path"]: f for f in st.session_state["drive_folders"]}
        selected_folders = [by_path[p] for p in selected_paths if p in by_path]

    can_run = status["token"] and (process_entire_root or bool(selected_folders))

    st.subheader("2. Run analysis")
    run = st.button(
        "Sync & analyze (from scratch)" if start_fresh else "Sync & analyze",
        type="primary",
        use_container_width=True,
        disabled=not can_run,
    )

    if run:
        if not status["openai"]:
            st.error("Save OPENAI_API_KEY in palm_mapper/.env, then refresh.")
        elif not status["credentials"]:
            st.error("Add credentials/credentials.json first.")
        elif not process_entire_root and not selected_folders:
            st.error("Select at least one folder, or enable **Process entire farm root**.")
        else:
            from services.pipeline import reset_analysis_state

            progress = st.progress(0.0)
            status_box = st.empty()

            def on_progress(msg, pct):
                progress.progress(min(max(pct, 0.0), 1.0))
                status_box.info(msg)

            if process_entire_root:
                folder_ids = [root_folder_id]
                folder_paths = {root_folder_id: "Chinnagudipet farm (entire root)"}
            else:
                folder_ids = [f["id"] for f in selected_folders]
                folder_paths = {f["id"]: f["path"] for f in selected_folders}

            try:
                if start_fresh:
                    reset_analysis_state(clear_exports=True)
                    observations_from_state.clear()
                with st.spinner("Syncing & analyzing…"):
                    summary = run_pipeline(
                        folder_ids=folder_ids,
                        folder_paths=folder_paths,
                        force_download=force_dl,
                        reanalyze=reanalyze or start_fresh,
                        progress=on_progress,
                    )
                st.session_state["last_summary"] = summary
                observations_from_state.clear()
                load_thumbnail_bytes.clear()
                with_alt = sum(
                    1 for p in summary.get("latest") or [] if p.get("altitude") is not None
                )
                st.success(
                    "Mapped **%d** plants · analyzed **%d** · with altitude **%d** · "
                    "consolidated **%d**"
                    % (
                        summary["plants_on_map"],
                        summary["analyzed_now"],
                        with_alt,
                        summary.get("plants_consolidated") or 0,
                    )
                )
            except DriveAuthRequired as exc:
                st.error(str(exc))
            except FileNotFoundError as exc:
                st.error(str(exc))
            except Exception as exc:
                st.exception(exc)

    summary = st.session_state.get("last_summary")
    if summary:
        with_alt = sum(
            1 for p in summary.get("latest") or [] if p.get("altitude") is not None
        )
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Photos in selection", summary.get("photos_on_drive", 0))
        m2.metric("On map (this run)", summary.get("plants_on_map", 0))
        m3.metric("Analyzed now", summary.get("analyzed_now", 0))
        m4.metric("With altitude", with_alt)
        m5.metric("Consolidated plants", summary.get("plants_consolidated", 0))
        if summary.get("selected_folders"):
            st.caption("Processed: " + ", ".join(summary["selected_folders"]))

    st.subheader("Exports")
    kml_path = OUTPUT_DIR / "palm_health.kml"
    kmz_path = OUTPUT_DIR / "palm_health.kmz"
    consolidated_kml = OUTPUT_DIR / "palm_health_consolidated.kml"
    consolidated_kmz = OUTPUT_DIR / "palm_health_consolidated.kmz"
    st.caption("Output folder: `%s`" % OUTPUT_DIR)

    col_a, col_b, col_c, col_d = st.columns(4)
    if kml_path.exists():
        col_a.download_button(
            "This-run KML",
            data=kml_path.read_bytes(),
            file_name="palm_health.kml",
            mime="application/vnd.google-earth.kml+xml",
            use_container_width=True,
        )
    if kmz_path.exists():
        col_b.download_button(
            "This-run KMZ",
            data=kmz_path.read_bytes(),
            file_name="palm_health.kmz",
            mime="application/vnd.google-earth.kmz",
            use_container_width=True,
        )
    if consolidated_kml.exists():
        col_c.download_button(
            "Consolidated KML",
            data=consolidated_kml.read_bytes(),
            file_name="palm_health_consolidated.kml",
            mime="application/vnd.google-earth.kml+xml",
            use_container_width=True,
        )
    if consolidated_kmz.exists():
        col_d.download_button(
            "Consolidated KMZ",
            data=consolidated_kmz.read_bytes(),
            file_name="palm_health_consolidated.kmz",
            mime="application/vnd.google-earth.kmz",
            use_container_width=True,
        )

    if st.button("Rebuild consolidated map from all stored plants"):
        from services.pipeline import rebuild_consolidated_exports

        with st.spinner("Rebuilding consolidated KML/KMZ (may take several minutes)…"):
            try:
                rebuilt = rebuild_consolidated_exports()
                observations_from_state.clear()
                st.success(
                    "Rebuilt **%d** plants → `%s`"
                    % (rebuilt["plants_consolidated"], rebuilt["consolidated_kml_path"])
                )
            except Exception as exc:
                st.exception(exc)

    st.subheader("Plant table (full farm)")
    clusters = load_all_clusters()
    if clusters:
        rows = [
            {
                "folder": c.representative.source_folder_path,
                "plant_id": c.representative.plant_id or Path(c.representative.file_name).stem,
                "health": c.representative.health,
                "photos_within_4m": c.photo_count,
                "confidence": round(c.representative.confidence or 0, 2),
                "latitude": c.representative.latitude,
                "longitude": c.representative.longitude,
                "altitude_m": c.representative.altitude,
                "summary": c.representative.summary,
                "latest_file": c.representative.file_name,
            }
            for c in clusters
        ]
        st.dataframe(pd.DataFrame(rows), use_container_width=True)
    else:
        st.write("No observations stored yet.")


# ---- Sidebar navigation ----
st.sidebar.title("Palm Mapper")
page = st.sidebar.radio(
    "Menu",
    options=["Map view", "Plant Mapping"],
    index=0,
    key="nav_page",
)

status = setup_ok()
st.sidebar.markdown("---")
st.sidebar.caption("Drive: %s" % ("connected" if status["token"] else "not connected"))
if page == "Plant Mapping":
    side_connect = st.sidebar.button(
        "Connect Google Drive",
        key="sidebar_connect_google",
        disabled=not status["credentials"],
    )
    side_disconnect = st.sidebar.button(
        "Disconnect",
        key="sidebar_disconnect_google",
        disabled=not status["token"],
    )
    handle_google_auth(bool(side_connect), bool(side_disconnect))

st.sidebar.markdown("---")
st.sidebar.header("Legend")
for key, meta in HEALTH_COLORS.items():
    st.sidebar.markdown("**%s** — %s" % (key.capitalize(), meta["label"]))

if page == "Map view":
    page_map_view()
else:
    page_plant_mapping()
