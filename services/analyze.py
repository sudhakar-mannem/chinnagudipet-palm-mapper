"""Extract GPS from EXIF and from stamped text overlays via AI vision."""
from __future__ import annotations

import base64
import json
import re
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import exifread
from openai import OpenAI
from PIL import Image

from config import OPENAI_API_KEY, OPENAI_VISION_MODEL

# Common stamped GPS patterns on field camera overlays
COORD_PATTERNS = [
    # Lat 5.123456 Lon 100.123456  /  Latitude: ... Longitude: ...
    re.compile(
        r"(?i)(?:lat(?:itude)?)\s*[:=]?\s*([+-]?\d{1,3}(?:\.\d+)?)\s*[,\s]+"
        r"(?:lon(?:g(?:itude)?)?)\s*[:=]?\s*([+-]?\d{1,3}(?:\.\d+)?)"
    ),
    # 5.123456, 100.123456 or 5.123456 N, 100.123456 E
    re.compile(
        r"([+-]?\d{1,2}\.\d{3,8})\s*([NnSs])?\s*[,/\s]+\s*"
        r"([+-]?\d{1,3}\.\d{3,8})\s*([EeWw])?"
    ),
    # N 5°12'34.5" E 100°12'34.5"
    re.compile(
        r"(?i)([NnSs])\s*(\d{1,2})[°\s]+(\d{1,2})[\'′\s]+(\d{1,2}(?:\.\d+)?)"
        r"[\"″]?\s+([EeWw])\s*(\d{1,3})[°\s]+(\d{1,2})[\'′\s]+(\d{1,2}(?:\.\d+)?)[\"″]?"
    ),
]


def _dms_to_decimal(deg: float, minutes: float, seconds: float, hemi: str) -> float:
    value = abs(deg) + minutes / 60.0 + seconds / 3600.0
    if hemi.upper() in ("S", "W"):
        value = -value
    return value


def _ratio_to_float(ratio) -> float:
    try:
        return float(ratio.num) / float(ratio.den)
    except Exception:
        return float(ratio)


def read_exif_gps(image_path: Path) -> Optional[Tuple[float, float, Optional[float]]]:
    """Return (lat, lon, alt) from EXIF if present."""
    try:
        with open(image_path, "rb") as fh:
            tags = exifread.process_file(fh, details=False)
    except Exception:
        return None

    lat_tag = tags.get("GPS GPSLatitude")
    lon_tag = tags.get("GPS GPSLongitude")
    lat_ref = tags.get("GPS GPSLatitudeRef")
    lon_ref = tags.get("GPS GPSLongitudeRef")
    if not (lat_tag and lon_tag and lat_ref and lon_ref):
        return None

    try:
        lat_vals = [_ratio_to_float(v) for v in lat_tag.values]
        lon_vals = [_ratio_to_float(v) for v in lon_tag.values]
        lat = _dms_to_decimal(lat_vals[0], lat_vals[1], lat_vals[2], str(lat_ref.values))
        lon = _dms_to_decimal(lon_vals[0], lon_vals[1], lon_vals[2], str(lon_ref.values))
    except Exception:
        return None

    alt = None
    alt_tag = tags.get("GPS GPSAltitude")
    if alt_tag is not None:
        try:
            alt = _ratio_to_float(alt_tag.values[0])
        except Exception:
            alt = None
    return lat, lon, alt


ALTITUDE_PATTERN = re.compile(
    r"(?i)(?:altitude|alt|elevation|elev)\s*[:=]?\s*([+-]?\d+(?:\.\d+)?)\s*(m|meters?|metres?|ft|feet)?"
)


def parse_coords_from_text(text: str) -> Optional[Tuple[float, float]]:
    """Parse latitude/longitude from OCR or AI-extracted stamp text."""
    if not text:
        return None

    # DMS form first
    m = COORD_PATTERNS[2].search(text)
    if m:
        lat = _dms_to_decimal(float(m.group(2)), float(m.group(3)), float(m.group(4)), m.group(1))
        lon = _dms_to_decimal(float(m.group(6)), float(m.group(7)), float(m.group(8)), m.group(5))
        return _validate(lat, lon)

    m = COORD_PATTERNS[0].search(text)
    if m:
        return _validate(float(m.group(1)), float(m.group(2)))

    m = COORD_PATTERNS[1].search(text)
    if m:
        lat = float(m.group(1))
        lon = float(m.group(3))
        if m.group(2) and m.group(2).upper() == "S":
            lat = -abs(lat)
        if m.group(4) and m.group(4).upper() == "W":
            lon = -abs(lon)
        # Heuristic: if first number looks like longitude for Malaysia/Indonesia region
        if abs(lat) > 90 and abs(lon) <= 90:
            lat, lon = lon, lat
        return _validate(lat, lon)

    return None


def parse_altitude_from_text(text: str) -> Optional[float]:
    """Parse altitude in meters from stamp text like 'Altitude: 172 meters'."""
    if not text:
        return None
    m = ALTITUDE_PATTERN.search(text)
    if not m:
        return None
    try:
        value = float(m.group(1))
    except (TypeError, ValueError):
        return None
    unit = (m.group(2) or "m").lower()
    if unit.startswith("ft") or unit.startswith("feet"):
        value = value * 0.3048
    # Sanity: reject absurd values
    if value < -500 or value > 9000:
        return None
    return value


def _validate(lat: float, lon: float) -> Optional[Tuple[float, float]]:
    if -90 <= lat <= 90 and -180 <= lon <= 180:
        return lat, lon
    return None


def _encode_image(image_path: Path, max_side: int = 1280) -> Tuple[str, str]:
    """Return (mime, base64) for a downsized JPEG suitable for vision APIs."""
    img = Image.open(image_path)
    img = img.convert("RGB")
    w, h = img.size
    scale = min(1.0, float(max_side) / float(max(w, h)))
    if scale < 1.0:
        # BILINEAR is much faster than LANCZOS for bulk field photos
        resample = getattr(getattr(Image, "Resampling", Image), "BILINEAR", Image.BILINEAR)
        img = img.resize((int(w * scale), int(h * scale)), resample)
    import io

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return "image/jpeg", b64


ANALYSIS_PROMPT = """You are an agronomist assistant analyzing oil palm (Elaeis guineensis) plant field photos.

Tasks:
1. Read any GPS / location stamp printed ON the photo (camera overlay such as GPS Map Camera, watermark, caption).
2. Assess the visible plant health condition.

Return ONLY valid JSON with this schema:
{
  "latitude": number or null,
  "longitude": number or null,
  "altitude_m": number or null,
  "coord_text": "raw stamp text if found, else empty string",
  "health": "green" | "amber" | "red" | "white",
  "confidence": number between 0 and 1,
  "summary": "one short sentence",
  "issues": ["list", "of", "visible", "issues"],
  "plant_id_guess": "any plant/tag/ID printed on photo, else empty string"
}

Health rules:
- green: healthy canopy, good leaf color, no serious disease/pest/damage
- amber: stress, nutrient deficiency, moderate pest/disease, incomplete canopy, needs attention
- red: severe disease, heavy pest damage, dying/dead fronds dominant, critical condition
- white: cannot determine (blurry, not a palm, plant not visible, night/poor light)

Coordinates / altitude:
- Prefer decimal degrees for latitude and longitude.
- If only DMS is printed, convert to decimal.
- Read Altitude / Elevation from the stamp (e.g. "Altitude: 172 meters") into altitude_m as meters.
- If altitude is in feet, convert to meters.
- If no stamp value is readable, set the corresponding fields to null.
"""


def analyze_photo_with_ai(image_path: Path) -> Dict[str, Any]:
    """
    Use OpenAI vision to extract stamped GPS + plant health in one call.
    """
    if not OPENAI_API_KEY:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Copy .env.example to .env and add your key."
        )

    mime, b64 = _encode_image(image_path)
    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=OPENAI_VISION_MODEL,
        temperature=0.1,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": ANALYSIS_PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": "data:%s;base64,%s" % (mime, b64),
                            "detail": "high",
                        },
                    },
                ],
            }
        ],
    )
    raw = response.choices[0].message.content or "{}"
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = {
            "latitude": None,
            "longitude": None,
            "altitude_m": None,
            "health": "white",
            "confidence": 0.0,
            "summary": "AI returned unreadable response",
            "issues": [],
            "coord_text": "",
            "plant_id_guess": "",
        }

    # Normalize health
    health = str(data.get("health") or "white").lower().strip()
    if health not in ("green", "amber", "red", "white"):
        health = "white"
    data["health"] = health

    # Prefer AI coords; fall back to parsing coord_text
    lat = data.get("latitude")
    lon = data.get("longitude")
    try:
        lat = float(lat) if lat is not None else None
        lon = float(lon) if lon is not None else None
    except (TypeError, ValueError):
        lat, lon = None, None

    coord_text = str(data.get("coord_text") or "")
    if lat is None or lon is None:
        parsed = parse_coords_from_text(coord_text)
        if parsed:
            lat, lon = parsed
    if lat is not None and lon is not None:
        validated = _validate(lat, lon)
        if validated:
            data["latitude"], data["longitude"] = validated
        else:
            data["latitude"], data["longitude"] = None, None
    else:
        data["latitude"], data["longitude"] = None, None

    alt = data.get("altitude_m")
    try:
        alt = float(alt) if alt is not None else None
    except (TypeError, ValueError):
        alt = None
    if alt is None:
        alt = parse_altitude_from_text(coord_text)
    if alt is not None and (alt < -500 or alt > 9000):
        alt = None
    data["altitude_m"] = alt

    conf = data.get("confidence", 0.0)
    try:
        data["confidence"] = max(0.0, min(1.0, float(conf)))
    except (TypeError, ValueError):
        data["confidence"] = 0.0

    if not isinstance(data.get("issues"), list):
        data["issues"] = []
    data["summary"] = str(data.get("summary") or "")
    data["plant_id_guess"] = str(data.get("plant_id_guess") or "")
    return data


def resolve_coordinates(
    image_path: Path, ai_result: Dict[str, Any]
) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    """
    Resolve lat/lon/altitude_m from EXIF, on-photo stamp (OCR), then AI vision.

    Field photos often strip EXIF (WhatsApp / Drive exports) but keep GPS Map Camera
    overlays — OCR of that printed stamp is the primary source for those files.
    """
    lat = lon = alt = None

    exif = read_exif_gps(image_path)
    if exif:
        lat, lon, alt = exif

    # Always attempt stamp OCR when EXIF is incomplete — stamps are on every photo.
    stamp_lat = stamp_lon = stamp_alt = None
    if lat is None or lon is None or alt is None:
        try:
            from services.stamp_ocr import read_stamp_gps

            stamp_lat, stamp_lon, stamp_alt, _ = read_stamp_gps(image_path)
        except Exception:
            stamp_lat = stamp_lon = stamp_alt = None

    if lat is None and stamp_lat is not None:
        lat = stamp_lat
    if lon is None and stamp_lon is not None:
        lon = stamp_lon
    if alt is None and stamp_alt is not None:
        alt = stamp_alt

    ai_lat = ai_result.get("latitude") if ai_result else None
    ai_lon = ai_result.get("longitude") if ai_result else None
    ai_alt = ai_result.get("altitude_m") if ai_result else None

    if lat is None and ai_lat is not None:
        try:
            lat = float(ai_lat)
        except (TypeError, ValueError):
            lat = None
    if lon is None and ai_lon is not None:
        try:
            lon = float(ai_lon)
        except (TypeError, ValueError):
            lon = None
    if alt is None and ai_alt is not None:
        try:
            alt = float(ai_alt)
        except (TypeError, ValueError):
            alt = None

    # Prefer stamp altitude when EXIF has coords but no altitude (common).
    if alt is None and stamp_alt is not None:
        alt = stamp_alt

    if lat is not None and lon is not None:
        validated = _validate(lat, lon)
        if not validated:
            return None, None, alt
        lat, lon = validated
        return lat, lon, alt
    return None, None, alt
