"""Palm Plant Health Mapper — Streamlit app (kept light for responsiveness)."""
from __future__ import annotations

import hashlib
import html
import io
import json
import os
import sys
from pathlib import Path
from typing import List, Optional, Tuple

import folium
import pandas as pd
import streamlit as st
from PIL import Image
from streamlit_folium import st_folium
from folium.features import DivIcon

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import (  # noqa: E402
    CACHE_DIR,
    CREDENTIALS_FILE,
    DRIVE_FOLDER_ID,
    EXCLUDED_OUTLIER_FILE_IDS,
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
    list_subfolders,
)
from services.models import (  # noqa: E402
    DEFAULT_PHOTO_RADIUS_M,
    DEFAULT_PLANT_SPACING_M,
    NEAR_PLANT_RADIUS_M,
    PlantCluster,
    PlantObservation,
    cluster_by_radius,
    filter_map_observations,
    haversine_m,
)
from services.pipeline import load_state, run_pipeline  # noqa: E402
from services.ui_te import t  # noqa: E402

st.set_page_config(
    page_title=t("app_title"),
    page_icon="🌴",
    layout="wide",
    initial_sidebar_state="auto",
)

# Mobile-responsive CSS
st.markdown("""
<style>
    /* Mobile-first responsive design */
    @media (max-width: 768px) {
        /* Adjust main content padding for mobile */
        .main .block-container {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            padding-top: 1rem !important;
            max-width: 100% !important;
        }
        
        /* Make sidebar collapsible on mobile */
        section[data-testid="stSidebar"] {
            width: 16rem !important;
        }
        
        /* Responsive buttons - larger touch targets */
        .stButton button {
            width: 100% !important;
            min-height: 44px !important;
            font-size: 16px !important;
            padding: 0.5rem 1rem !important;
        }
        
        /* Responsive text inputs */
        .stTextInput input {
            font-size: 16px !important;
            min-height: 44px !important;
        }
        
        /* Responsive selectbox */
        .stSelectbox select {
            font-size: 16px !important;
            min-height: 44px !important;
        }
        
        /* Responsive multiselect */
        .stMultiSelect {
            font-size: 16px !important;
        }
        
        /* Responsive metrics */
        [data-testid="stMetricValue"] {
            font-size: clamp(1.2rem, 5vw, 2rem) !important;
        }
        
        [data-testid="stMetricLabel"] {
            font-size: 0.85rem !important;
        }
        
        /* Images responsive */
        img {
            max-width: 100% !important;
            height: auto !important;
        }
        
        /* Responsive dataframes */
        .dataframe {
            font-size: 14px !important;
            overflow-x: auto !important;
        }
        
        /* Column adjustments for mobile */
        [data-testid="column"] {
            min-width: auto !important;
            padding: 0.25rem !important;
        }
        
        /* Expander touch-friendly */
        .streamlit-expanderHeader {
            min-height: 44px !important;
            font-size: 16px !important;
        }
        
        /* Map container responsive */
        iframe {
            width: 100% !important;
        }
        
        /* Stack columns on mobile */
        [data-testid="stHorizontalBlock"] {
            flex-direction: column !important;
        }
        
        [data-testid="stHorizontalBlock"] > [data-testid="column"] {
            width: 100% !important;
        }
        
        /* Better readability on mobile */
        .main h1 {
            font-size: 1.75rem !important;
        }
        
        .main h2 {
            font-size: 1.5rem !important;
        }
        
        .main h3 {
            font-size: 1.25rem !important;
        }
    }
    
    /* Tablet breakpoint */
    @media (min-width: 769px) and (max-width: 1024px) {
        .main .block-container {
            padding-left: 2rem !important;
            padding-right: 2rem !important;
        }
        
        [data-testid="stMetricValue"] {
            font-size: 1.5rem !important;
        }
        
        [data-testid="column"] {
            padding: 0.5rem !important;
        }
    }
    
    /* Touch-friendly elements for all devices */
    button, a, [role="button"] {
        -webkit-tap-highlight-color: rgba(0,0,0,0.1);
    }
    
    /* Prevent zoom on input focus (iOS) */
    input, select, textarea {
        font-size: 16px !important;
    }
    
    /* Responsive map container */
    .folium-map {
        width: 100% !important;
        height: auto !important;
    }
    
    /* Ensure images don't overflow */
    .stImage {
        max-width: 100%;
        height: auto;
    }
    
    /* Better spacing on mobile */
    @media (max-width: 768px) {
        [data-testid="stVerticalBlock"] > [style*="flex-direction: column"] > [data-testid="stVerticalBlock"] {
            gap: 0.5rem !important;
        }
    }
    
    /* Improve download buttons on mobile */
    @media (max-width: 768px) {
        .stDownloadButton button {
            font-size: 14px !important;
            padding: 0.5rem 0.75rem !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# Detect screen size for responsive features
st.markdown("""
<script>
// Store screen width for responsive adjustments
if (typeof window !== 'undefined') {
    const width = window.innerWidth;
    const height = window.innerHeight;
    const isMobile = width < 768;
    
    // Try to pass to Streamlit via query params (best effort)
    try {
        const url = new URL(window.parent.location.href);
        if (!url.searchParams.has('screen_width')) {
            url.searchParams.set('screen_width', width.toString());
            url.searchParams.set('is_mobile', isMobile.toString());
        }
    } catch (e) {
        // Cross-origin restriction, that's okay
    }
}
</script>
""", unsafe_allow_html=True)

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


def is_mobile():
    """Detect if user is on mobile device based on viewport width."""
    # Use session state to store mobile status if needed
    # For Streamlit, we'll use a reasonable default mobile height
    return st.session_state.get("is_mobile", False)


def get_responsive_map_height():
    """Return appropriate map height based on device."""
    # Mobile: smaller height to fit screen better
    # Desktop: larger height for better viewing
    # Check if we can detect screen size via query params or use reasonable defaults
    try:
        # Try to get from query params if set by JavaScript
        width = st.query_params.get("screen_width")
        if width and int(width) < 768:
            return 400
    except Exception:
        pass
    # Default: use a medium height that works on most screens
    return 620


def setup_ok():
    secret_status = reload_env() or {}
    return {
        "openai": openai_key_configured(),
        "credentials": CREDENTIALS_FILE.exists()
        or bool(secret_status.get("credentials_written")),
        "token": TOKEN_FILE.exists() or bool(secret_status.get("token_written")),
        "folder": bool(DRIVE_FOLDER_ID),
        "secret_status": secret_status,
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


def _plantation_map_frame(
    mapped: List[PlantCluster],
    max_radius_m: float = 2500.0,
):
    """
    Median center + inlier coords for the initial map view.

    Mean of all map coords is pulled far off-farm by corrupt GPS (e.g. lat≈lon≈79
    or photos from another region). Median + distance filter keeps the viewport
    on the main plantation without changing markers or realignment.
    """
    coords = [
        (float(c.representative.map_latitude), float(c.representative.map_longitude))
        for c in mapped
        if c.representative.map_latitude is not None
        and c.representative.map_longitude is not None
    ]
    lats = sorted(lat for lat, _ in coords)
    lons = sorted(lon for _, lon in coords)
    med_lat = lats[len(lats) // 2]
    med_lon = lons[len(lons) // 2]
    core = [
        (lat, lon)
        for lat, lon in coords
        if haversine_m(lat, lon, med_lat, med_lon) <= max_radius_m
    ]
    if len(core) < 2:
        core = coords
    core_lats = sorted(lat for lat, _ in core)
    core_lons = sorted(lon for _, lon in core)
    return (
        core_lats[len(core_lats) // 2],
        core_lons[len(core_lons) // 2],
        core,
    )


def build_map(clusters: List[PlantCluster]):
    mapped = [
        c
        for c in clusters
        if c.representative.map_latitude is not None
        and c.representative.map_longitude is not None
    ]
    if not mapped:
        return None
    center_lat, center_lon, frame_coords = _plantation_map_frame(mapped)
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

    for n, c in enumerate(mapped, start=1):
        p = c.representative
        color = HEALTH_COLORS.get(p.health, HEALTH_COLORS["white"])["hex"]
        title = p.plant_id or Path(p.file_name).stem
        # Dark text on light markers; white text on saturated health colors
        fg = "#111" if p.health in ("white", "amber") else "#fff"
        label = HEALTH_COLORS.get(p.health, HEALTH_COLORS["white"])["label"]
        gps_note = ""
        if p.latitude is not None and p.longitude is not None:
            gps_note = "<br/>GPS: %.6f, %.6f" % (float(p.latitude), float(p.longitude))
        popup = folium.Popup(
            "<b>#%d</b> %s<br/>%s<br/>%s%s"
            % (
                n,
                html.escape(title),
                label,
                t("popup_photos", c.photo_count),
                gps_note,
            ),
            max_width=260,
        )
        icon_html = (
            '<div style="background:%s;border:1px solid #111;border-radius:50%%;'
            "width:22px;height:22px;display:flex;align-items:center;"
            "justify-content:center;font-size:8px;font-weight:700;color:%s;"
            'line-height:1;font-family:Arial,sans-serif;box-sizing:border-box;">'
            "%d</div>"
        ) % (color, fg, n)
        folium.Marker(
            location=[p.map_latitude, p.map_longitude],
            popup=popup,
            tooltip="#%d · %s" % (n, t("tooltip_photos", title, c.photo_count)),
            icon=DivIcon(
                html=icon_html,
                icon_size=(22, 22),
                icon_anchor=(11, 11),
                class_name="plant-num-marker",
            ),
        ).add_to(fmap)

    if len(frame_coords) >= 2:
        frame_lats = [lat for lat, _ in frame_coords]
        frame_lons = [lon for _, lon in frame_coords]
        fmap.fit_bounds(
            [[min(frame_lats), min(frame_lons)], [max(frame_lats), max(frame_lons)]],
            padding=(24, 24),
        )

    folium.LayerControl().add_to(fmap)
    return fmap


def nearest_cluster_index(clusters, lat, lon):
    best_i = 0
    best_d = 1e18
    for i, c in enumerate(clusters):
        p = c.representative
        if p.map_latitude is None or p.map_longitude is None:
            continue
        d = haversine_m(lat, lon, float(p.map_latitude), float(p.map_longitude))
        if d < best_d:
            best_d = d
            best_i = i
    return best_i


def mapped_clusters_for_map(clusters: List[PlantCluster]) -> List[PlantCluster]:
    """Same plants Map View numbers: mapped clusters with display/map coords."""
    return [
        c
        for c in clusters
        if c.representative.map_latitude is not None
        and c.representative.map_longitude is not None
    ]


def nearest_mapped_plant(
    mapped: List[PlantCluster], lat: float, lon: float
) -> Optional[Tuple[int, PlantCluster, float]]:
    """
    Return (plant_number_1based, cluster, distance_m) for the nearest mapped plant,
    or None if the list is empty.
    """
    best = None
    best_d = 1e18
    for n, c in enumerate(mapped, start=1):
        p = c.representative
        d = haversine_m(
            lat, lon, float(p.map_latitude), float(p.map_longitude)
        )
        if d < best_d:
            best_d = d
            best = (n, c, d)
    return best


def load_all_clusters() -> List[PlantCluster]:
    state_mtime = STATE_PATH.stat().st_mtime if STATE_PATH.exists() else 0.0
    all_obs = observations_from_state(state_mtime)
    # Drop durable map outliers (photos retained in state with GPS).
    map_obs = filter_map_observations(
        [o for o in all_obs if o.latitude is not None],
        excluded_file_ids=EXCLUDED_OUTLIER_FILE_IDS,
    )
    clusters = cluster_by_radius(map_obs, radius_m=DEFAULT_PHOTO_RADIUS_M)
    # Ensure display positions exist (e.g. older state without realignment).
    if clusters and not any(
        c.representative.display_latitude is not None for c in clusters
    ):
        from services.models import apply_lattice_to_clusters

        apply_lattice_to_clusters(clusters, spacing_m=DEFAULT_PLANT_SPACING_M)
    return clusters


def render_photo_panel(cluster: PlantCluster) -> None:
    """Show plant photos as small cached thumbnails (paginated, plant-scoped keys)."""
    selected = cluster.representative
    plant_key = (
        selected.plant_id
        or selected.file_id
        or Path(selected.file_name or "plant").stem
    )
    panel = st.container()
    with panel:
        # Image first, then supporting text below (keeps map click / plant select unchanged).
        max_show = int(st.session_state.get("photo_page_size") or 1)
        members = cluster.members
        total = len(members)
        show_n = min(max_show, total)

        shown = 0
        for idx, photo in enumerate(members[:show_n]):
            file_key = photo.file_id or ("%s_%d" % (plant_key, idx))

            # Prefer local cache; otherwise download this one photo from Drive
            local = ensure_local_photo(
                photo.file_id or "",
                photo.file_name or "",
                photo.local_path,
                download=False,
            )
            if local is None or not local.exists():
                try:
                    with st.spinner(t("loading_photo")):
                        local = ensure_local_photo(
                            photo.file_id or "",
                            photo.file_name or "",
                            photo.local_path,
                            download=True,
                        )
                except DriveAuthRequired:
                    st.warning(t("drive_secrets_invalid"))
                    if photo.photo_url:
                        st.markdown("[%s](%s)" % (t("open_drive"), photo.photo_url))
                    continue

            if local and local.exists():
                ok = show_fast_image(
                    local, caption=photo.file_name or local.name, max_side=420
                )
                if ok:
                    shown += 1
                else:
                    st.warning(t("could_not_decode"))
                alt_txt = (
                    t("altitude_m", photo.altitude)
                    if photo.altitude is not None
                    else t("n_a")
                )
                st.markdown(
                    t(
                        "photo_meta",
                        t("latest") if idx == 0 else "",
                        idx + 1,
                        total,
                        photo.file_name,
                        alt_txt,
                    )
                )
                with st.expander(t("larger_preview"), expanded=False):
                    show_fast_image(local, caption="", max_side=900)
            else:
                st.error(t("could_not_download"))
                if photo.photo_url:
                    st.markdown("[%s](%s)" % (t("open_drive"), photo.photo_url))
                # Keep a manual retry with a unique key per file
                if st.button(t("retry_download"), key="retry_photo_%s" % file_key):
                    st.rerun()

        if total > show_n:
            if st.button(
                t("show_more_photos", total - show_n),
                key="more_photos_%s" % plant_key,
            ):
                st.session_state["photo_page_size"] = show_n + 1
                st.rerun()
        elif total > 1 and max_show > 1:
            if st.button(t("show_fewer_photos"), key="fewer_photos_%s" % plant_key):
                st.session_state["photo_page_size"] = 1
                st.rerun()

        if shown == 0 and total:
            st.caption(t("photos_missing_tip"))

        st.write(
            t(
                "plant_n_photos",
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
            st.caption(t("altitude", selected.altitude))
        if selected.latitude is not None and selected.longitude is not None:
            st.caption(
                t(
                    "original_gps",
                    float(selected.latitude),
                    float(selected.longitude),
                )
            )
        if selected.display_latitude is not None and selected.display_longitude is not None:
            st.caption(
                t(
                    "map_position",
                    DEFAULT_PLANT_SPACING_M,
                    float(selected.display_latitude),
                    float(selected.display_longitude),
                )
            )




def is_streamlit_cloud() -> bool:
    """True when running on Streamlit Community Cloud."""
    if os.environ.get("STREAMLIT_SHARING_MODE"):
        return True
    if Path("/mount/src").exists():
        return True
    try:
        home = str(Path.home()).replace("\\", "/")
        if home.startswith("/home/appuser"):
            return True
    except Exception:
        pass
    return False


def drive_connected() -> bool:
    """True when Secrets/token can authenticate Drive (no browser)."""
    try:
        from services.drive import get_credentials

        get_credentials(interactive=False)
        return True
    except Exception:
        return False


def handle_google_auth(connect_clicked: bool, disconnect_clicked: bool) -> None:
    """
    Streamlit never opens a browser for Google login.
    Auth comes only from Cloud/local Secrets (GOOGLE_*_B64) or an existing token file.
    """
    if disconnect_clicked:
        cached_subfolders.clear()
        for key in ("drive_folders", "folders_loaded", "selected_folder_paths", "drive_ready"):
            st.session_state.pop(key, None)
        try:
            if TOKEN_FILE.exists():
                TOKEN_FILE.unlink()
        except Exception as exc:
            st.error(t("could_not_clear_token", exc))
            return
        # Secrets will rewrite token.json on next reload — warn on Cloud
        secret_status = reload_env() or {}
        if secret_status.get("token_written") and TOKEN_FILE.exists():
            st.warning(t("secrets_still_provide"))
        else:
            st.success(t("disconnected"))
        st.rerun()

    if not connect_clicked:
        return

    with st.spinner(t("loading_drive_creds")):
        secret_status = reload_env() or {}

    if not secret_status.get("credentials_written") and not CREDENTIALS_FILE.exists():
        st.error(t("missing_creds_b64_long"))
        return
    if not secret_status.get("token_written") and not TOKEN_FILE.exists():
        st.error(t("missing_token_b64"))
        with st.expander(t("secrets_status"), expanded=True):
            st.write(secret_status)
        return

    from services.drive import get_credentials

    try:
        get_credentials(interactive=False)
    except DriveAuthRequired as exc:
        st.error(t("secrets_token_auth_failed"))
        st.caption(str(exc).replace("\n", " "))
        with st.expander(t("secrets_status"), expanded=True):
            st.write(
                {
                    "secrets_available": secret_status.get("secrets_available"),
                    "credentials_written": secret_status.get("credentials_written"),
                    "token_written": secret_status.get("token_written"),
                    "credentials_error": secret_status.get("credentials_error") or "(none)",
                    "token_error": secret_status.get("token_error") or "(none)",
                    "credentials_file_exists": CREDENTIALS_FILE.exists(),
                    "token_file_exists": TOKEN_FILE.exists(),
                }
            )
        return
    except Exception as exc:
        st.error(t("drive_auth_failed", exc))
        return

    cached_subfolders.clear()
    st.session_state["folders_loaded"] = True
    st.session_state["drive_ready"] = True
    st.success(t("connected_secrets_ok"))
    st.rerun()


def ensure_drive_from_secrets() -> bool:
    """On each run, materialize Secrets and mark Drive ready when possible."""
    if st.session_state.get("drive_ready"):
        return True
    reload_env()
    ok = drive_connected()
    st.session_state["drive_ready"] = ok
    return ok



def page_map_view() -> None:
    st.title(t("farm_map"))
    st.caption(t("farm_map_caption"))

    if not ensure_drive_from_secrets():
        st.error(t("map_photos_need_secrets"))
        with st.expander(t("how_open_secrets"), expanded=True):
            st.markdown(t("how_open_secrets_steps"))

    clusters = load_all_clusters()
    health_filter = st.multiselect(
        t("filter_health"),
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

    # Responsive metrics layout - stack on mobile
    col_metrics = st.columns([1, 1, 1, 1, 1])
    col_metrics[0].metric(t("plants_on_map"), len(clusters))
    col_metrics[1].metric(HEALTH_COLORS["green"]["label"], counts["green"])
    col_metrics[2].metric(HEALTH_COLORS["amber"]["label"], counts["amber"])
    col_metrics[3].metric(HEALTH_COLORS["red"]["label"], counts["red"])
    col_metrics[4].metric(HEALTH_COLORS["white"]["label"], counts["white"])

    # Responsive layout: stack on mobile, side-by-side on desktop
    # On mobile, show plant selector first, then map below
    left, right = st.columns([1.55, 1])
    with left:
        if clusters:
            fmap = build_map(clusters)
            if fmap:
                map_height = get_responsive_map_height()
                map_state = st_folium(
                    fmap,
                    height=map_height,
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
            st.info(t("no_mapped_plants"))

    with right:
        if not clusters:
            st.write(t("no_plants_yet"))
            return

        labels = []
        for i, c in enumerate(clusters):
            p = c.representative
            labels.append(
                t(
                    "plant_option",
                    i + 1,
                    p.plant_id or Path(p.file_name).stem,
                    HEALTH_COLORS.get(p.health, HEALTH_COLORS["white"])["label"],
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
            t("select_plant"),
            options=list(range(len(clusters))),
            format_func=lambda i: labels[i],
            key="plant_select_main",
        )
        if choice != prev_choice:
            st.session_state["photo_page_size"] = 1
        st.session_state["selected_cluster_idx"] = choice
        render_photo_panel(clusters[choice])

    with st.expander(t("open_earth"), expanded=False):
        consolidated_kml = OUTPUT_DIR / "palm_health_consolidated.kml"
        consolidated_kmz = OUTPUT_DIR / "palm_health_consolidated.kmz"
        earth_folder = OUTPUT_DIR / "palm_health_consolidated_earth_folder"
        earth_open = earth_folder / "doc_absolute.kml"
        if not earth_open.exists():
            earth_open = earth_folder / "OPEN_ME.kml"
        target = earth_open if earth_open.exists() else consolidated_kmz
        c1, c2 = st.columns(2)
        with c1:
            if target.exists() and st.button(
                t("open_consolidated_earth"), type="primary"
            ):
                st.success(open_in_google_earth(target))
        with c2:
            if consolidated_kml.exists():
                st.download_button(
                    t("download_kml"),
                    data=consolidated_kml.read_bytes(),
                    file_name="palm_health_consolidated.kml",
                    mime="application/vnd.google-earth.kml+xml",
                )


def _plantation_median_lat_lon(mapped: List[PlantCluster]) -> Optional[Tuple[float, float]]:
    lats = []
    lons = []
    for c in mapped:
        p = c.representative
        if p.map_latitude is None or p.map_longitude is None:
            continue
        lats.append(float(p.map_latitude))
        lons.append(float(p.map_longitude))
    if not lats:
        return None
    lats.sort()
    lons.sort()
    mid = len(lats) // 2
    return lats[mid], lons[mid]


def _read_device_gps():
    """
    High-accuracy browser GPS for mobile Near me.
    
    Uses localStorage as a bridge between GPS component and Python app.
    """
    import streamlit.components.v1 as components

    # First, check if GPS data is available in localStorage
    if not st.session_state.get("near_me_gps_armed"):
        # Try to read GPS data from localStorage
        gps_reader = components.html(
            """
            <script>
            (function() {
                const gpsData = localStorage.getItem('streamlit_gps_data');
                if (gpsData) {
                    // Found GPS data, clear it and pass to parent
                    localStorage.removeItem('streamlit_gps_data');
                    const data = JSON.parse(gpsData);
                    
                    // Try to update parent URL
                    try {
                        const u = new URL(window.location.href);
                        if (data.failed) {
                            u.searchParams.set("gps_fail", "1");
                            u.searchParams.set("gps_acc", data.accuracy || "9999");
                        } else {
                            u.searchParams.delete("gps_fail");
                            u.searchParams.set("gps_lat", data.latitude);
                            u.searchParams.set("gps_lon", data.longitude);
                            u.searchParams.set("gps_acc", data.accuracy);
                        }
                        window.location.href = u.toString();
                    } catch (e) {
                        console.error("Could not update URL:", e);
                    }
                }
            })();
            </script>
            """,
            height=0,
        )
    
    # Check query params for GPS data
    params = st.query_params
    fail_q = params.get("gps_fail")
    lat_q = params.get("gps_lat")
    lon_q = params.get("gps_lon")
    acc_q = params.get("gps_acc")
    
    if fail_q:
        try:
            acc_fail = float(acc_q if not isinstance(acc_q, list) else acc_q[0]) if acc_q else 0.0
        except (TypeError, ValueError):
            acc_fail = 0.0
        st.error(f"GPS failed with accuracy: ±{acc_fail}m")
        st.info("Please try outdoors with clear sky view for better GPS accuracy.")
        st.session_state["near_me_gps_armed"] = False

    st.caption(t("gps_howto"))
    if st.button(
        t("get_precise_gps"), type="primary", use_container_width=True, key="near_me_gps_btn"
    ):
        st.session_state["near_me_gps_armed"] = True
        # Clear previous GPS data
        try:
            for key in ("gps_fail", "gps_lat", "gps_lon", "gps_acc"):
                if key in st.query_params:
                    del st.query_params[key]
        except Exception:
            pass
        st.rerun()

    if st.session_state.get("near_me_gps_armed") and not fail_q:
        components.html(
            """
            <div id="gps-status" style="font-family:sans-serif;font-size:14px;padding:8px 0;">
              %s
            </div>
            <script>
            (function () {
              const status = document.getElementById("gps-status");
              const msgGood = %s;
              const msgWait = %s;
              const errPrefix = %s;
              const noGeo = %s;
              
              function fail(msg) {
                if (status) status.textContent = msg;
                console.error("GPS Error:", msg);
              }
              
              // Check if we're in a secure context (HTTPS)
              function isSecureContext() {
                return window.isSecureContext || window.location.protocol === 'https:' || 
                       window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
              }
              
              // Save GPS result to localStorage and trigger reload
              function saveAndReload(best, failed) {
                const result = {
                  failed: failed,
                  latitude: best ? best.latitude : null,
                  longitude: best ? best.longitude : null,
                  accuracy: best ? best.accuracy : null,
                  timestamp: Date.now()
                };
                
                console.log("Saving GPS result to localStorage:", result);
                
                try {
                  localStorage.setItem('streamlit_gps_data', JSON.stringify(result));
                  // Trigger page reload to pick up the data
                  window.location.reload();
                } catch (e) {
                  console.error("Failed to save GPS data:", e);
                  fail("Unable to save GPS data. Please try again.");
                }
              }
              
              // Check secure context first
              if (!isSecureContext()) {
                fail("⚠️ GPS requires HTTPS. Please access this app via https://");
                return;
              }
              
              // Get geolocation API
              const geoHost = navigator.geolocation;
              
              if (!geoHost) {
                fail(noGeo);
                return;
              }
              
              // Aggressive GPS options for maximum accuracy
              const opts = {
                enableHighAccuracy: true,  // Force GPS hardware
                maximumAge: 0,              // No cached positions
                timeout: 60000              // 60 seconds max per attempt
              };
              
              let best = null;
              let samples = 0;
              let watchId = null;
              let accepted = false;
              
              // Function to update status display
              function updateStatus() {
                if (!status || !best) return;
                const acc = Math.round(best.accuracy);
                const emoji = acc <= 10 ? "🎯" : acc <= 20 ? "✓" : "📡";
                status.textContent = emoji + " GPS ±" + acc + " m — " +
                  (acc <= 15 ? msgGood : msgWait) + " (samples: " + samples + ")";
              }
              
              // Success handler
              function onPosition(pos) {
                samples += 1;
                const c = pos.coords;
                const fix = {
                  latitude: c.latitude,
                  longitude: c.longitude,
                  accuracy: c.accuracy
                };
                
                // Keep the best (most accurate) reading
                if (!best || fix.accuracy < best.accuracy) {
                  best = fix;
                  updateStatus();
                }
                
                // Accept immediately if accuracy is excellent (≤15m)
                if (best.accuracy <= 15 && !accepted) {
                  accepted = true;
                  try { geoHost.clearWatch(watchId); } catch (e) {}
                  saveAndReload(best, false);
                }
              }
              
              // Error handler
              function onError(err) {
                console.error("GPS Error:", err);
                let msg = errPrefix;
                if (err.code === 1) msg += "Permission denied. Please allow location access in browser settings.";
                else if (err.code === 2) msg += "Position unavailable. Please check GPS/Location is enabled.";
                else if (err.code === 3) msg += "Timeout. Please try again in an area with better GPS signal.";
                else msg += (err.message || String(err));
                fail(msg);
                saveAndReload(null, true);
              }
              
              // Start continuous GPS watch
              try {
                watchId = geoHost.watchPosition(onPosition, onError, opts);
              } catch (e) {
                console.error("Failed to start GPS watch:", e);
                fail(errPrefix + "Cannot access GPS. Please ensure Location is enabled and try again.");
                return;
              }
              
              // Fallback timeout: after 45 seconds, accept best reading if reasonable
              setTimeout(function () {
                if (accepted) return;
                try { geoHost.clearWatch(watchId); } catch (e) {}
                
                if (!best) {
                  fail(errPrefix + "No GPS signal received. Please check Location Services are enabled.");
                  saveAndReload(null, true);
                  return;
                }
                
                // Only accept if accuracy is decent (≤25m)
                if (best.accuracy <= 25) {
                  accepted = true;
                  saveAndReload(best, false);
                } else {
                  fail("GPS accuracy too poor (±" + Math.round(best.accuracy) + "m). Please try outdoors with clear sky view.");
                  saveAndReload(best, true);
                }
              }, 45000);
            })();
            </script>
            """
            % (
                html.escape(t("gps_requesting_html")),
                json.dumps(t("gps_lock_good"), ensure_ascii=False),
                json.dumps(t("gps_lock_wait"), ensure_ascii=False),
                json.dumps(t("gps_error_prefix"), ensure_ascii=False),
                json.dumps(t("gps_no_geolocation"), ensure_ascii=False),
            ),
            height=100,
        )
    
    # Return GPS data from query params
    if fail_q:
        return None, None, None
    if lat_q and lon_q:
        try:
            lat = float(lat_q if not isinstance(lat_q, list) else lat_q[0])
            lon = float(lon_q if not isinstance(lon_q, list) else lon_q[0])
            acc = None
            if acc_q:
                acc = float(acc_q if not isinstance(acc_q, list) else acc_q[0])
            return lat, lon, acc
        except (TypeError, ValueError):
            return None, None, None
    
    return None, None, None


def page_near_me() -> None:
    """Mobile-first: GPS → nearest map plant number within NEAR_PLANT_RADIUS_M."""
    import streamlit.components.v1 as components
    
    st.title(t("near_me_title"))
    st.caption(t("near_me_caption"))

    mapped = mapped_clusters_for_map(load_all_clusters())
    if not mapped:
        st.info(t("near_me_no_plants"))
        return

    lat, lon, accuracy = _read_device_gps()
    if st.button(t("clear_gps"), use_container_width=True, key="near_me_clear"):
        st.session_state.pop("near_me_gps_armed", None)
        # Clear query params
        try:
            for key in ("gps_fail", "gps_lat", "gps_lon", "gps_acc"):
                if key in st.query_params:
                    del st.query_params[key]
        except Exception:
            pass
        # Clear localStorage via component
        components.html(
            "<script>localStorage.removeItem('streamlit_gps_data');</script>",
            height=0,
        )
        st.rerun()

    if lat is not None and lon is not None:
        st.session_state["near_me_lat"] = lat
        st.session_state["near_me_lon"] = lon
        st.session_state["near_me_acc"] = accuracy
        st.session_state["near_me_gps_armed"] = False
    else:
        lat = st.session_state.get("near_me_lat")
        lon = st.session_state.get("near_me_lon")
        accuracy = st.session_state.get("near_me_acc")

    if lat is None or lon is None:
        st.info(t("waiting_gps"))
        return

    acc_m = None
    try:
        if accuracy is not None:
            acc_m = float(accuracy)
    except (TypeError, ValueError):
        acc_m = None

    acc_txt = t("acc_suffix", acc_m) if acc_m is not None else ""
    
    # Visual GPS accuracy indicator
    if acc_m is not None:
        if acc_m <= 15:
            acc_emoji = "🎯"
            acc_quality = "Excellent"
            acc_color = "green"
        elif acc_m <= 25:
            acc_emoji = "✓"
            acc_quality = "Good"
            acc_color = "blue"
        elif acc_m <= 50:
            acc_emoji = "📡"
            acc_quality = "Fair"
            acc_color = "orange"
        else:
            acc_emoji = "⚠️"
            acc_quality = "Poor"
            acc_color = "red"
        
        st.markdown(
            f'<div style="text-align:center;padding:0.5rem;background:rgba(0,0,0,0.03);border-radius:8px;margin-bottom:1rem;">'
            f'<span style="font-size:1.5rem;">{acc_emoji}</span> '
            f'<span style="color:{acc_color};font-weight:600;">{acc_quality}</span> GPS accuracy: '
            f'<strong>±{acc_m:.0f}m</strong><br/>'
            f'<small style="opacity:0.7;">📍 {lat:.6f}, {lon:.6f}</small>'
            f'</div>',
            unsafe_allow_html=True
        )
    else:
        st.caption(t("your_location", lat, lon, acc_txt))

    farm = _plantation_median_lat_lon(mapped)
    if farm is not None:
        farm_dist = haversine_m(float(lat), float(lon), farm[0], farm[1])
        if farm_dist > 500:
            st.error(t("gps_far_from_farm", farm_dist))
            return

    if acc_m is not None and acc_m > 40:
        st.warning(t("gps_accuracy_poor", acc_m))
        with st.expander("📡 How to improve GPS accuracy", expanded=True):
            st.markdown("""
            **Your GPS accuracy is poor (±{:.0f}m). For better results:**
            
            🌤️ **Move to open sky** - Step away from buildings, trees, and roofs
            
            ⏱️ **Wait 30-60 seconds** - GPS needs time to lock onto satellites
            
            📱 **Check Location Settings:**
            - Ensure "High Accuracy" or "GPS Only" mode is enabled
            - Disable "Wi-Fi" or "Network" location (use GPS hardware)
            - Allow location permission for your browser
            
            🔋 **Enable airplane mode** - Then re-enable just mobile data (forces GPS)
            
            📍 **Try GPS Test apps** - Apps like "GPS Status" can show satellite lock
            
            ❌ **Avoid indoor use** - GPS rarely works indoors
            
            *GPS Map cam apps work better because they wait for true GPS satellite lock, not network location.*
            """.format(acc_m))
    elif acc_m is not None and acc_m > 20:
        st.info(f"📡 GPS accuracy: ±{acc_m:.0f}m. For better precision, move to open sky and wait longer.")

    # Effective match radius: at least 2 m, but widen slightly to GPS uncertainty (capped)
    match_r = float(NEAR_PLANT_RADIUS_M)
    if acc_m is not None and acc_m > match_r:
        match_r = min(max(acc_m, NEAR_PLANT_RADIUS_M), 25.0)

    hit = nearest_mapped_plant(mapped, float(lat), float(lon))
    if hit is None:
        st.warning(t("could_not_match"))
        return

    plant_n, cluster, dist_m = hit
    p = cluster.representative
    health = p.health if p.health in HEALTH_COLORS else "white"
    color = HEALTH_COLORS[health]["hex"]
    label = HEALTH_COLORS[health]["label"]
    title = p.plant_id or Path(p.file_name).stem

    if dist_m <= match_r:
        st.markdown(
            '<div style="text-align:center;padding:1.2rem 0 0.4rem 0;">'
            '<div style="font-size:0.95rem;opacity:0.75;margin-bottom:0.35rem;">%s</div>'
            '<div style="font-size:min(28vw,7.5rem);font-weight:800;line-height:1;'
            "letter-spacing:-0.04em;color:%s;text-shadow:0 1px 0 rgba(0,0,0,0.15);\">"
            "%d</div>"
            '<div style="margin-top:0.85rem;font-size:1.15rem;">%s</div>'
            '<div style="margin-top:0.35rem;font-size:0.95rem;opacity:0.8;">%s</div>'
            "</div>"
            % (
                html.escape(t("plant_word")),
                color,
                plant_n,
                html.escape(t("m_away_health", dist_m, label)),
                html.escape(title),
            ),
            unsafe_allow_html=True,
        )
        if match_r > NEAR_PLANT_RADIUS_M:
            st.caption(t("matched_uncertainty", acc_m or match_r))
        st.session_state["selected_cluster_idx"] = max(0, plant_n - 1)
        st.session_state["plant_select_main"] = max(0, plant_n - 1)
        st.caption(t("open_map_for_photos"))
    else:
        st.markdown(
            '<div style="text-align:center;padding:1.5rem 0 0.5rem 0;">'
            '<div style="font-size:clamp(1.6rem,7vw,2.4rem);font-weight:700;line-height:1.2;">'
            "%s</div>"
            "</div>"
            % html.escape(t("no_plant_within", match_r)),
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div style="text-align:center;opacity:0.85;">'
            "%s"
            "</div>"
            % t("nearest_plant", plant_n, dist_m, html.escape(label)),
            unsafe_allow_html=True,
        )



def page_plant_mapping() -> None:
    st.title(t("mapping_title"))
    st.caption(t("mapping_caption"))

    ensure_drive_from_secrets()
    secret_status = reload_env() or {}
    status = setup_ok()
    ready = bool(st.session_state.get("drive_ready")) or drive_connected()
    st.session_state["drive_ready"] = ready

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(t("metric_openai"), t("ready") if status["openai"] else t("missing"))
    c2.metric(
        t("metric_drive_creds"), t("ready") if status["credentials"] else t("missing")
    )
    c3.metric(
        t("metric_drive_secrets"),
        t("drive_connected") if ready else t("not_ready"),
    )
    c4.metric(t("metric_folder"), t("set") if status["folder"] else t("missing"))

    with st.expander(t("cloud_secrets_status"), expanded=not ready):
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
                "drive_ready": ready,
            }
        )
        if not ready:
            st.warning(t("secrets_help"))

    st.subheader(t("gdrive_secrets_header"))
    gc1, gc2, gc3 = st.columns([1.2, 1, 2])
    with gc1:
        main_connect = st.button(
            t("connect_from_secrets"),
            type="primary",
            use_container_width=True,
            disabled=not status["credentials"] and not secret_status.get("credentials_written"),
            key="main_connect_google",
        )
    with gc2:
        main_disconnect = st.button(
            t("disconnect"),
            use_container_width=True,
            disabled=not ready,
            key="main_disconnect_google",
        )
    with gc3:
        if not status["credentials"]:
            st.error(t("missing_creds_b64"))
        elif ready:
            st.success(t("drive_connected_secrets"))
        else:
            st.warning(t("not_ready_click_connect"))

    handle_google_auth(bool(main_connect), bool(main_disconnect))
    status = setup_ok()
    ready = bool(st.session_state.get("drive_ready")) or status["token"]

    st.subheader(t("select_folders"))
    root_folder_id = st.text_input(
        t("root_folder_id"),
        value=DRIVE_FOLDER_ID,
        help=t("root_folder_help"),
    )
    refresh = st.button(
        t("refresh_folders"),
        use_container_width=True,
        disabled=not ready,
    )
    if refresh:
        cached_subfolders.clear()
        st.session_state["folders_loaded"] = True

    folders = []
    folder_error = None
    if ready and (
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
    elif not ready:
        st.info(t("connect_then_refresh"))
    elif not folders and not st.session_state.get("folders_loaded"):
        st.info(t("click_refresh_folders"))
    elif not folders:
        st.warning(t("no_subfolders"))
    else:
        path_options = [f["path"] for f in folders]
        default_paths = [
            p for p in st.session_state.get("selected_folder_paths", [])
            if p in path_options
        ]
        selected_paths = st.multiselect(
            t("folders_to_process"),
            options=path_options,
            default=default_paths,
        )
        st.session_state["selected_folder_paths"] = selected_paths
        st.caption(t("folders_selected", len(selected_paths), len(path_options)))

    with st.expander(t("advanced"), expanded=False):
        process_entire_root = st.checkbox(
            t("process_entire_root"),
            value=False,
            key="opt_entire_root",
        )
        start_fresh = st.checkbox(
            t("start_fresh"),
            value=False,
            key="opt_fresh",
        )
        reanalyze = st.checkbox(
            t("reanalyze"),
            value=False,
            key="opt_reanalyze",
        )
        force_dl = st.checkbox(t("force_dl"), value=False, key="opt_force_dl")
        st.caption(t("cache_path", CACHE_DIR))

    process_entire_root = st.session_state.get("opt_entire_root", False)
    start_fresh = st.session_state.get("opt_fresh", False)
    reanalyze = st.session_state.get("opt_reanalyze", False)
    force_dl = st.session_state.get("opt_force_dl", False)

    selected_paths = st.session_state.get("selected_folder_paths") or []
    selected_folders = []
    if st.session_state.get("drive_folders"):
        by_path = {f["path"]: f for f in st.session_state["drive_folders"]}
        selected_folders = [by_path[p] for p in selected_paths if p in by_path]

    can_run = ready and (process_entire_root or bool(selected_folders))

    st.subheader(t("run_analysis"))
    run = st.button(
        t("sync_analyze_scratch") if start_fresh else t("sync_analyze"),
        type="primary",
        use_container_width=True,
        disabled=not can_run,
    )

    if run:
        if not status["openai"]:
            st.error(t("need_openai"))
        elif not status["credentials"]:
            st.error(t("need_creds_file"))
        elif not process_entire_root and not selected_folders:
            st.error(t("need_folder"))
        else:
            from services.pipeline import reset_analysis_state

            progress = st.progress(0.0)
            status_box = st.empty()

            def on_progress(msg, pct):
                progress.progress(min(max(pct, 0.0), 1.0))
                status_box.info(msg)

            if process_entire_root:
                folder_ids = [root_folder_id]
                folder_paths = {root_folder_id: t("farm_entire_root")}
            else:
                folder_ids = [f["id"] for f in selected_folders]
                folder_paths = {f["id"]: f["path"] for f in selected_folders}

            try:
                if start_fresh:
                    reset_analysis_state(clear_exports=True)
                    observations_from_state.clear()
                with st.spinner(t("syncing_analyzing")):
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
                    t(
                        "mapped_summary",
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
        m1.metric(t("photos_in_selection"), summary.get("photos_on_drive", 0))
        m2.metric(t("on_map_this_run"), summary.get("plants_on_map", 0))
        m3.metric(t("analyzed_now"), summary.get("analyzed_now", 0))
        m4.metric(t("with_altitude"), with_alt)
        m5.metric(t("consolidated_plants"), summary.get("plants_consolidated", 0))
        if summary.get("selected_folders"):
            st.caption(t("processed_folders", ", ".join(summary["selected_folders"])))

    st.subheader(t("exports"))
    kml_path = OUTPUT_DIR / "palm_health.kml"
    kmz_path = OUTPUT_DIR / "palm_health.kmz"
    consolidated_kml = OUTPUT_DIR / "palm_health_consolidated.kml"
    consolidated_kmz = OUTPUT_DIR / "palm_health_consolidated.kmz"
    st.caption(t("output_folder", OUTPUT_DIR))

    col_a, col_b, col_c, col_d = st.columns(4)
    if kml_path.exists():
        col_a.download_button(
            t("this_run_kml"),
            data=kml_path.read_bytes(),
            file_name="palm_health.kml",
            mime="application/vnd.google-earth.kml+xml",
            use_container_width=True,
        )
    if kmz_path.exists():
        col_b.download_button(
            t("this_run_kmz"),
            data=kmz_path.read_bytes(),
            file_name="palm_health.kmz",
            mime="application/vnd.google-earth.kmz",
            use_container_width=True,
        )
    if consolidated_kml.exists():
        col_c.download_button(
            t("consolidated_kml_btn"),
            data=consolidated_kml.read_bytes(),
            file_name="palm_health_consolidated.kml",
            mime="application/vnd.google-earth.kml+xml",
            use_container_width=True,
        )
    if consolidated_kmz.exists():
        col_d.download_button(
            t("consolidated_kmz_btn"),
            data=consolidated_kmz.read_bytes(),
            file_name="palm_health_consolidated.kmz",
            mime="application/vnd.google-earth.kmz",
            use_container_width=True,
        )

    if st.button(t("rebuild_map")):
        from services.pipeline import rebuild_consolidated_exports

        with st.spinner(t("rebuilding_exports")):
            try:
                rebuilt = rebuild_consolidated_exports()
                observations_from_state.clear()
                st.success(
                    t(
                        "rebuilt_ok",
                        rebuilt["plants_consolidated"],
                        rebuilt.get("plant_spacing_m", DEFAULT_PLANT_SPACING_M),
                        rebuilt["consolidated_kml_path"],
                    )
                )
            except Exception as exc:
                st.exception(exc)

    st.subheader(t("plant_table"))
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
                "display_latitude": c.representative.display_latitude,
                "display_longitude": c.representative.display_longitude,
                "altitude_m": c.representative.altitude,
                "summary": c.representative.summary,
                "latest_file": c.representative.file_name,
            }
            for c in clusters
        ]
        st.dataframe(pd.DataFrame(rows), use_container_width=True)
    else:
        st.write(t("no_obs"))


# ---- Sidebar navigation ----
st.sidebar.title(t("app_title"))
_PAGE_MAP = t("page_map")
_PAGE_NEAR = t("page_near")
_PAGE_MAPPING = t("page_mapping")
page = st.sidebar.radio(
    t("menu"),
    options=[_PAGE_MAP, _PAGE_NEAR, _PAGE_MAPPING],
    index=0,
    key="nav_page",
)

ensure_drive_from_secrets()
status = setup_ok()
drive_ok = bool(st.session_state.get("drive_ready"))
st.sidebar.markdown("---")
st.sidebar.caption(
    t(
        "drive_secrets_caption",
        t("drive_connected") if drive_ok else t("drive_not_connected"),
    )
)
if page == _PAGE_MAPPING:
    side_connect = st.sidebar.button(
        t("connect_from_secrets"),
        key="sidebar_connect_google",
        disabled=not status["credentials"],
    )
    side_disconnect = st.sidebar.button(
        t("disconnect"),
        key="sidebar_disconnect_google",
        disabled=not drive_ok,
    )
    handle_google_auth(bool(side_connect), bool(side_disconnect))

st.sidebar.markdown("---")
st.sidebar.header(t("legend"))
for key, meta in HEALTH_COLORS.items():
    st.sidebar.markdown("**%s**" % meta["label"])

if page == _PAGE_MAP:
    page_map_view()
elif page == _PAGE_NEAR:
    page_near_me()
else:
    page_plant_mapping()
