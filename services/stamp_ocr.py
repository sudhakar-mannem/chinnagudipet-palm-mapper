"""Read lat/lon/altitude printed on GPS Map Camera–style photo overlays via local OCR."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional, Tuple

from PIL import Image, ImageEnhance, ImageOps

from services.analyze import parse_altitude_from_text, parse_coords_from_text

_OCR = None

# Same-line stamp forms (do not cross newlines — Map Camera often puts values below labels)
LAT_LINE = re.compile(
    r"(?i)\bLat(?:itude)?\s*[:=]\s*([+-]?\d{1,2}(?:\.\d+)?)\s*°?"
)
LON_LINE = re.compile(
    r"(?i)\bLon(?:g(?:itude)?)?\s*[:=]\s*([+-]?\d{1,3}(?:\.\d+)?)\s*°?"
)
ALT_LINE = re.compile(
    r"(?i)\b(?:Altitude|Alt|Elevation|Elev)\s*[:=]?\s*([+-]?\d+(?:\.\d+)?)\s*(m|meters?|metres?|ft|feet)?"
)


def _get_ocr():
    global _OCR
    if _OCR is None:
        from rapidocr_onnxruntime import RapidOCR

        _OCR = RapidOCR()
    return _OCR


def _stamp_crop(img: Image.Image, bottom_fraction: float = 0.32) -> Image.Image:
    """GPS Map Camera Lite puts Lat/Long/Altitude in the lower banner."""
    w, h = img.size
    top = max(0, int(h * (1.0 - bottom_fraction)))
    crop = img.crop((0, top, w, h))
    # Upscale small crops so digits stay readable for OCR
    if crop.height < 420:
        scale = 420.0 / float(crop.height)
        crop = crop.resize(
            (int(crop.width * scale), int(crop.height * scale)),
            getattr(getattr(Image, "Resampling", Image), "BICUBIC", Image.BICUBIC),
        )
    crop = ImageOps.autocontrast(crop)
    crop = ImageEnhance.Contrast(crop).enhance(1.35)
    return crop


def _ocr_text(img: Image.Image) -> str:
    import numpy as np

    engine = _get_ocr()
    arr = np.array(img.convert("RGB"))
    result, _ = engine(arr)
    if not result:
        return ""
    lines = []
    for item in result:
        # RapidOCR: [box, text, score]
        if len(item) >= 2 and item[1]:
            lines.append(str(item[1]))
    return "\n".join(lines)


# Decimal degrees that appear under Latitude / Longitude labels
_DEGREE_NUM = re.compile(r"([+-]?\d{1,3}\.\d{3,8})\s*°?")


def _parse_stamp_fields(text: str) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    """
    GPS Map Camera Lite often OCRs as:
      Latitude
      Longitude
      19.24988°
      79.62778°
      Altitude167meters
    so label and value are on separate lines.
    """
    lat = lon = alt = None
    if not text:
        return None, None, None

    # Normalize OCR junk degree glyphs
    cleaned = (
        text.replace("�", "°")
        .replace("˚", "°")
        .replace("º", "°")
    )

    m = ALT_LINE.search(cleaned.replace(" ", ""))
    if not m:
        m = ALT_LINE.search(cleaned)
    if m:
        try:
            alt = float(m.group(1))
            unit = (m.group(2) or "m").lower()
            if unit.startswith("ft") or unit.startswith("feet"):
                alt *= 0.3048
            if alt < -500 or alt > 9000:
                alt = None
        except ValueError:
            alt = None
    if alt is None:
        alt = parse_altitude_from_text(cleaned)

    # Inline "Lat 19.25 Lon 79.62"
    m = LAT_LINE.search(cleaned)
    if m:
        try:
            lat = float(m.group(1))
        except ValueError:
            lat = None
    m = LON_LINE.search(cleaned)
    if m:
        try:
            lon = float(m.group(1))
        except ValueError:
            lon = None

    # Stacked labels then two degree numbers (common OCR of Map Camera Lite)
    if lat is None or lon is None:
        lower = cleaned.lower()
        has_lat_lbl = "lat" in lower
        has_lon_lbl = "lon" in lower
        nums = []
        for m in _DEGREE_NUM.finditer(cleaned):
            try:
                val = float(m.group(1))
            except ValueError:
                continue
            # Skip altitude-like whole meters already captured, and date fragments
            if alt is not None and abs(val - alt) < 1e-6:
                continue
            if 1900 <= val <= 2100 and "." not in m.group(1)[0:5]:
                continue
            nums.append(val)
        # Prefer a lat-like then lon-like pair for this farm region
        if has_lat_lbl and has_lon_lbl and len(nums) >= 2:
            a, b = nums[0], nums[1]
            # If first looks like longitude (e.g. 79.x) and second like latitude, swap
            if abs(a) > 40 and abs(b) < 40:
                a, b = b, a
            elif abs(a) < 40 and abs(b) > 40:
                pass  # lat, lon already
            lat = lat if lat is not None else a
            lon = lon if lon is not None else b
        elif len(nums) >= 2 and (lat is None or lon is None):
            a, b = nums[0], nums[1]
            if abs(a) > 40 and abs(b) < 40:
                a, b = b, a
            lat = lat if lat is not None else a
            lon = lon if lon is not None else b

    if lat is None or lon is None:
        parsed = parse_coords_from_text(cleaned)
        if parsed:
            lat = lat if lat is not None else parsed[0]
            lon = lon if lon is not None else parsed[1]

    if lat is not None and lon is not None:
        if abs(lat) > 90 and abs(lon) <= 90:
            lat, lon = lon, lat
        # Farm is in India (~19N, ~79E): swap if clearly reversed
        if abs(lat) > 40 and abs(lon) < 40:
            lat, lon = lon, lat
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            lat, lon = None, None
    return lat, lon, alt

def read_stamp_gps(
    image_path: Path,
) -> Tuple[Optional[float], Optional[float], Optional[float], str]:
    """
    OCR the photo overlay and return (lat, lon, altitude_m, raw_text).
    Works without OpenAI — required when stamps exist but EXIF GPS was stripped.
    """
    path = Path(image_path)
    try:
        img = Image.open(path).convert("RGB")
    except Exception:
        return None, None, None, ""

    texts = []
    # Primary: bottom banner. Secondary: slightly taller crop if first pass misses.
    for frac in (0.30, 0.40):
        crop = _stamp_crop(img, bottom_fraction=frac)
        text = _ocr_text(crop)
        if text:
            texts.append(text)
        lat, lon, alt = _parse_stamp_fields(text)
        if lat is not None and lon is not None:
            return lat, lon, alt, text

    combined = "\n".join(texts)
    lat, lon, alt = _parse_stamp_fields(combined)
    return lat, lon, alt, combined
