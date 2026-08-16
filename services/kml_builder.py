"""Build KML / KMZ for Google Earth with color-coded plant icons."""
from __future__ import annotations

import io
import shutil
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Union

from PIL import Image
from xml.sax.saxutils import escape

from config import HEALTH_COLORS, ICON_URLS, OUTPUT_DIR, ensure_dirs
from services.models import (
    DEFAULT_PHOTO_RADIUS_M,
    PlantCluster,
    PlantObservation,
    cluster_by_radius,
)


def _safe_kmz_name(obs: PlantObservation) -> str:
    """Short stable JPEG name inside the KMZ."""
    fid = (obs.file_id or Path(obs.file_name).stem).replace("/", "_").replace("\\", "_")
    return "%s.jpg" % fid


def _image_href(
    obs: PlantObservation,
    image_mode: str,
    file_map: Optional[Dict[str, str]] = None,
) -> str:
    if image_mode == "files":
        name = (file_map or {}).get(obs.file_id) or _safe_kmz_name(obs)
        # Root of KMZ (not files/) — more reliable in Google Earth Pro
        return name
    return obs.photo_url or ""


def _make_thumbnail_bytes(src: Path, max_side: int = 800, quality: int = 65) -> Optional[bytes]:
    """Compress photo for Google Earth balloons."""
    try:
        img = Image.open(src).convert("RGB")
        w, h = img.size
        scale = min(1.0, float(max_side) / float(max(w, h)))
        if scale < 1.0:
            resample = getattr(getattr(Image, "Resampling", Image), "BILINEAR", Image.BILINEAR)
            img = img.resize((int(w * scale), int(h * scale)), resample)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        return buf.getvalue()
    except Exception:
        try:
            return src.read_bytes()
        except Exception:
            return None


def _balloon_html(
    cluster: PlantCluster,
    image_mode: str,
    file_map: Optional[Dict[str, str]] = None,
) -> str:
    """Minimal HTML — Google Earth only supports a tiny subset."""
    obs = cluster.representative
    color = HEALTH_COLORS.get(obs.health, HEALTH_COLORS["white"])
    name = escape(obs.plant_id or Path(obs.file_name).stem)
    summary = escape(obs.summary or "")
    label = escape(color["label"])
    radius = cluster.radius_m

    lines = [
        "<b>%s</b><br/>" % name,
        "Latest: %s (%.0f%%)<br/>" % (label, (obs.confidence or 0) * 100),
        "%s<br/>" % summary,
        "Photos within %.0f m: %d<br/><hr/>" % (radius, len(cluster.members)),
    ]
    for i, member in enumerate(cluster.members):
        href = _image_href(member, image_mode, file_map=file_map)
        alt = (
            "%.1f m" % member.altitude
            if member.altitude is not None
            else "n/a"
        )
        prefix = "LATEST " if i == 0 else ""
        lines.append(
            "<b>%s%d/%d</b> %s (alt %s)<br/>"
            % (prefix, i + 1, len(cluster.members), escape(member.file_name), alt)
        )
        if href:
            lines.append('<img src="%s" width="350"><br/><br/>' % href)
        else:
            lines.append("<i>photo missing</i><br/><br/>")
    return "".join(lines)


def _as_clusters(
    observations_or_clusters: Union[List[PlantObservation], List[PlantCluster]],
    radius_m: float,
) -> List[PlantCluster]:
    if not observations_or_clusters:
        return []
    if isinstance(observations_or_clusters[0], PlantCluster):
        return observations_or_clusters  # type: ignore
    return cluster_by_radius(observations_or_clusters, radius_m=radius_m)  # type: ignore


def build_kml(
    observations: Union[List[PlantObservation], List[PlantCluster]],
    title: str = "Palm Plant Health",
    image_mode: str = "drive",
    radius_m: float = DEFAULT_PHOTO_RADIUS_M,
    file_map: Optional[Dict[str, str]] = None,
) -> str:
    clusters = _as_clusters(observations, radius_m=radius_m)
    placemarks = []
    for cluster in clusters:
        obs = cluster.representative
        if obs.latitude is None or obs.longitude is None:
            continue
        health = obs.health if obs.health in ICON_URLS else "white"
        name = escape(obs.plant_id or Path(obs.file_name).stem)
        if cluster.photo_count > 1:
            name = "%s (%d photos)" % (name, cluster.photo_count)
        balloon = _balloon_html(cluster, image_mode=image_mode, file_map=file_map)
        alt = obs.altitude if obs.altitude is not None else 0
        # No custom BalloonStyle text — Earth Pro often shows blank balloons with $[description]
        placemarks.append(
            """
      <Placemark>
        <name>%(name)s</name>
        <Snippet maxLines="1">%(count)d photo(s) within %(radius).0f m — click for images</Snippet>
        <description><![CDATA[%(balloon)s]]></description>
        <styleUrl>#style-%(health)s</styleUrl>
        <Point>
          <coordinates>%(lon).8f,%(lat).8f,%(alt)s</coordinates>
        </Point>
      </Placemark>"""
            % {
                "name": name,
                "balloon": balloon,
                "health": health,
                "count": cluster.photo_count,
                "radius": radius_m,
                "lon": obs.longitude,
                "lat": obs.latitude,
                "alt": alt,
            }
        )

    styles = []
    for key, url in ICON_URLS.items():
        color = HEALTH_COLORS[key]["kml_aabbggrr"]
        styles.append(
            """
    <Style id="style-%(key)s">
      <IconStyle>
        <color>%(color)s</color>
        <scale>1.2</scale>
        <Icon><href>%(url)s</href></Icon>
        <hotSpot x="32" y="1" xunits="pixels" yunits="pixels"/>
      </IconStyle>
      <LabelStyle><scale>0.8</scale></LabelStyle>
    </Style>"""
            % {"key": key, "color": color, "url": url}
        )

    legend = escape(
        "Click a plant icon to open the balloon with photos within %.0f m." % radius_m
    )
    folder_name = escape("Palm plants (photos within %.0f m)" % radius_m)

    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<kml xmlns="http://www.opengis.net/kml/2.2">\n'
        "  <Document>\n"
        "    <name>%(title)s</name>\n"
        "    <description>%(legend)s</description>\n"
        "%(styles)s\n"
        "    <Folder>\n"
        "      <name>%(folder)s</name>\n"
        "      <open>1</open>\n"
        "%(placemarks)s\n"
        "    </Folder>\n"
        "  </Document>\n"
        "</kml>\n"
    ) % {
        "title": escape(title),
        "legend": legend,
        "folder": folder_name,
        "styles": "".join(styles),
        "placemarks": "".join(placemarks),
    }


def write_kml(
    observations: Union[List[PlantObservation], List[PlantCluster]],
    out_path: Optional[Path] = None,
    title: str = "Palm Plant Health",
    radius_m: float = DEFAULT_PHOTO_RADIUS_M,
) -> Path:
    ensure_dirs()
    out_path = out_path or (OUTPUT_DIR / "palm_health.kml")
    out_path.write_text(
        build_kml(observations, title=title, image_mode="drive", radius_m=radius_m),
        encoding="utf-8",
    )
    return out_path


def write_kmz(
    observations: Union[List[PlantObservation], List[PlantCluster]],
    out_path: Optional[Path] = None,
    title: str = "Palm Plant Health",
    radius_m: float = DEFAULT_PHOTO_RADIUS_M,
) -> Path:
    """
    KMZ with doc.kml + JPEG thumbnails at archive root (Earth-compatible).
    Also writes an unzipped folder package next to it for reliable Earth Pro viewing.
    """
    ensure_dirs()
    out_path = out_path or (OUTPUT_DIR / "palm_health.kmz")
    clusters = _as_clusters(observations, radius_m=radius_m)

    tmp_dir = OUTPUT_DIR / "_kmz_build"
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir)
    tmp_dir.mkdir(parents=True)

    file_map: Dict[str, str] = {}
    for cluster in clusters:
        for obs in cluster.members:
            if obs.file_id in file_map:
                continue
            src = Path(obs.local_path) if obs.local_path else None
            if not src or not src.exists():
                continue
            name = _safe_kmz_name(obs)
            data = _make_thumbnail_bytes(src)
            if not data:
                continue
            (tmp_dir / name).write_bytes(data)
            file_map[obs.file_id] = name

    kml = build_kml(
        clusters,
        title=title,
        image_mode="files",
        radius_m=radius_m,
        file_map=file_map,
    )
    (tmp_dir / "doc.kml").write_text(kml, encoding="utf-8")

    if out_path.exists():
        out_path.unlink()
    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(tmp_dir / "doc.kml", arcname="doc.kml")
        for path in tmp_dir.iterdir():
            if path.name == "doc.kml":
                continue
            zf.write(path, arcname=path.name)

    # Unzipped folder — most reliable way to open photos in Google Earth Pro
    folder_name = out_path.stem + "_earth_folder"
    folder_path = out_path.parent / folder_name
    if folder_path.exists():
        shutil.rmtree(folder_path)
    shutil.copytree(tmp_dir, folder_path)

    # Absolute file:// KML (often works when relative KMZ balloons fail on Windows)
    abs_map: Dict[str, str] = {}
    for fid, name in file_map.items():
        abs_map[fid] = (folder_path / name).resolve().as_uri()
    abs_kml = _build_kml_absolute(
        clusters, title=title, radius_m=radius_m, abs_map=abs_map
    )
    (folder_path / "doc_absolute.kml").write_text(abs_kml, encoding="utf-8")
    shutil.copy2(folder_path / "doc.kml", folder_path / "OPEN_ME.kml")

    shutil.rmtree(tmp_dir, ignore_errors=True)
    return out_path


def _build_kml_absolute(
    clusters: List[PlantCluster],
    title: str,
    radius_m: float,
    abs_map: Dict[str, str],
) -> str:
    """KML balloons + icons using absolute file:/// URLs to local thumbnails."""
    placemarks = []
    for cluster in clusters:
        obs = cluster.representative
        if obs.latitude is None or obs.longitude is None:
            continue
        label = escape(obs.plant_id or Path(obs.file_name).stem)
        lines = [
            "<b>%s</b><br/>" % label,
            "Photos within %.0f m: %d<br/><hr/>" % (radius_m, len(cluster.members)),
        ]
        for i, member in enumerate(cluster.members):
            href = abs_map.get(member.file_id) or ""
            lines.append(
                "<b>%d/%d</b> %s<br/>"
                % (i + 1, len(cluster.members), escape(member.file_name))
            )
            if href:
                lines.append('<img src="%s" width="400"><br/><br/>' % href)
        balloon = "".join(lines)
        alt = obs.altitude if obs.altitude is not None else 0
        icon_href = abs_map.get(obs.file_id) or ICON_URLS["white"]
        placemarks.append(
            """
      <Placemark>
        <name>%(name)s</name>
        <description><![CDATA[%(balloon)s]]></description>
        <Style>
          <IconStyle>
            <scale>1.6</scale>
            <Icon><href>%(icon)s</href></Icon>
          </IconStyle>
        </Style>
        <Point><coordinates>%(lon).8f,%(lat).8f,%(alt)s</coordinates></Point>
      </Placemark>"""
            % {
                "name": label,
                "balloon": balloon,
                "icon": icon_href,
                "lon": obs.longitude,
                "lat": obs.latitude,
                "alt": alt,
            }
        )

    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<kml xmlns="http://www.opengis.net/kml/2.2">\n'
        "  <Document>\n"
        "    <name>%s</name>\n"
        "    <Folder><name>Plants</name><open>1</open>\n"
        "%s\n"
        "    </Folder>\n"
        "  </Document>\n"
        "</kml>\n"
    ) % (escape(title), "".join(placemarks))
