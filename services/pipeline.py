"""End-to-end pipeline: sync Drive → analyze → save state → export KML/KMZ."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from config import EXCLUDED_OUTLIER_FILE_IDS, OUTPUT_DIR, STATE_PATH, ensure_dirs
from services.analyze import analyze_photo_with_ai, resolve_coordinates
from services.drive import sync_photos
from services.kml_builder import write_kml, write_kmz
from services.models import (
    DEFAULT_PHOTO_RADIUS_M,
    DEFAULT_PLANT_SPACING_M,
    PlantObservation,
    apply_lattice_to_clusters,
    cluster_by_radius,
    filter_map_observations,
)


ProgressCb = Optional[Callable[[str, float], None]]


def load_state() -> Dict[str, Any]:
    ensure_dirs()
    if not STATE_PATH.exists():
        return {"observations": []}
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"observations": []}


def save_state(state: Dict[str, Any]) -> None:
    ensure_dirs()
    STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")


def reset_analysis_state(clear_exports: bool = True) -> None:
    """Clear stored plant analysis so the next run is truly from scratch."""
    ensure_dirs()
    save_state({"observations": [], "reset_at": datetime.now(timezone.utc).isoformat()})
    if not clear_exports:
        return
    for name in (
        "palm_health.kml",
        "palm_health.kmz",
        "palm_health.json",
        "palm_health_consolidated.kml",
        "palm_health_consolidated.kmz",
        "palm_health_consolidated.json",
    ):
        path = OUTPUT_DIR / name
        if path.exists():
            path.unlink()


def _obs_index(state: Dict[str, Any]) -> Dict[str, PlantObservation]:
    out: Dict[str, PlantObservation] = {}
    for raw in state.get("observations", []):
        obs = PlantObservation.from_dict(raw)
        out[obs.file_id] = obs
    return out


def run_pipeline(
    folder_id: Optional[str] = None,
    folder_ids: Optional[List[str]] = None,
    folder_paths: Optional[Dict[str, str]] = None,
    force_download: bool = False,
    reanalyze: bool = False,
    progress: ProgressCb = None,
) -> Dict[str, Any]:
    """
    Sync selected folders, analyze new photos, export KML/KMZ for this run.

    folder_ids: selected Drive subfolder IDs (preferred).
    folder_paths: optional map of folder_id -> display path.
    """
    def report(msg: str, pct: float) -> None:
        if progress:
            progress(msg, pct)

    folder_paths = folder_paths or {}
    ensure_dirs()
    report("Connecting to Google Drive…", 0.02)
    files = sync_photos(
        folder_id=folder_id,
        folder_ids=folder_ids,
        force=force_download,
    )
    report("Synced %d photos from selected folders" % len(files), 0.15)

    state = load_state()
    existing = _obs_index(state)
    analyzed_now = 0
    skipped_cached = 0
    run_file_ids = set()
    ai_quota_exhausted = False

    total = max(len(files), 1)
    for i, meta in enumerate(files):
        file_id = meta["id"]
        run_file_ids.add(file_id)
        local_path = Path(meta["local_path"])
        pct = 0.15 + 0.7 * (float(i) / float(total))
        src_folder = meta.get("source_folder_id") or ""
        src_path = folder_paths.get(src_folder, src_folder)

        cached = existing.get(file_id)
        # Re-read when GPS/altitude missing or prior AI call failed (e.g. API quota)
        prior_failed = bool(cached and (cached.summary or "").startswith("Analysis failed"))
        needs_gps = (
            cached is None
            or cached.latitude is None
            or cached.longitude is None
            or cached.altitude is None
            or prior_failed
        )
        same_version = (
            cached
            and cached.modified_time == meta.get("modifiedTime")
            and cached.local_path == str(local_path)
            and cached.health in ("green", "amber", "red", "white")
            and not needs_gps
        )
        if same_version and not reanalyze:
            # Keep folder metadata fresh for filtering
            cached.source_folder_id = src_folder or cached.source_folder_id
            cached.source_folder_path = src_path or cached.source_folder_path
            existing[file_id] = cached
            skipped_cached += 1
            report("Cached: %s" % meta["name"], pct)
            continue

        report("Analyzing: %s" % meta["name"], pct)
        ai: Dict[str, Any] = {}
        ai_error = ""
        # If we only need stamp GPS (or OpenAI quota is gone), skip the vision API.
        stamp_only = ai_quota_exhausted or (
            needs_gps
            and cached is not None
            and prior_failed
            and not reanalyze
        )
        if stamp_only:
            ai = {
                "health": (cached.health if cached and cached.health in ("green", "amber", "red", "white") else "white"),
                "confidence": float(cached.confidence) if cached else 0.0,
                "summary": "",
                "issues": list(cached.issues) if cached else [],
                "plant_id_guess": (cached.plant_id if cached else "") or "",
                "latitude": None,
                "longitude": None,
                "altitude_m": None,
            }
        else:
            try:
                ai = analyze_photo_with_ai(local_path)
            except Exception as exc:
                ai_error = str(exc)
                if "insufficient_quota" in ai_error or "credit_balance_exhausted" in ai_error or "429" in ai_error:
                    ai_quota_exhausted = True
                ai = {
                    "health": "white",
                    "confidence": 0.0,
                    "summary": "",
                    "issues": [],
                    "plant_id_guess": "",
                    "latitude": None,
                    "longitude": None,
                    "altitude_m": None,
                }

        # Stamp OCR fills lat/lon/altitude even when OpenAI is down / out of credits
        lat, lon, alt = resolve_coordinates(local_path, ai)
        health = ai.get("health", "white")
        summary = ai.get("summary") or ""
        if stamp_only and lat is not None:
            summary = summary or "Mapped from photo stamp (Lat/Long/Altitude overlay)."
        if ai_error and not summary:
            summary = "Health AI unavailable (%s); coords from photo stamp." % (
                ai_error.split("\n")[0][:120]
            )
        elif ai_error and lat is not None:
            summary = (summary + " [stamp GPS used after AI error]").strip()

        obs = PlantObservation(
            file_id=file_id,
            file_name=meta["name"],
            local_path=str(local_path),
            modified_time=meta.get("modifiedTime") or "",
            latitude=lat,
            longitude=lon,
            altitude=alt,
            health=health if health in ("green", "amber", "red", "white") else "white",
            confidence=float(ai.get("confidence") or 0),
            summary=summary or ("Mapped from photo stamp" if lat is not None else "No GPS stamp readable"),
            issues=list(ai.get("issues") or []),
            photo_url=meta.get("photo_url") or "",
            plant_id=ai.get("plant_id_guess") or "",
            analyzed_at=datetime.now(timezone.utc).isoformat(),
            source_folder_id=src_folder,
            source_folder_path=src_path,
        )
        existing[file_id] = obs
        analyzed_now += 1

    observations = list(existing.values())
    # Preserve prior map-outlier flags across re-analysis of the same file_id.
    for obs in observations:
        if obs.file_id in EXCLUDED_OUTLIER_FILE_IDS:
            obs.excluded_from_map = True
    # Cluster on original GPS (excluding map outliers), then ~9 m lattice.
    all_geo = filter_map_observations(
        [
            o
            for o in observations
            if o.latitude is not None and o.longitude is not None
        ],
        excluded_file_ids=EXCLUDED_OUTLIER_FILE_IDS,
    )
    consolidated_clusters = cluster_by_radius(all_geo)
    plants_realigned = apply_lattice_to_clusters(
        consolidated_clusters, spacing_m=DEFAULT_PLANT_SPACING_M
    )
    state["observations"] = [o.to_dict() for o in observations]
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    state["last_selected_folder_ids"] = list(folder_ids or [])
    state["plant_spacing_m"] = DEFAULT_PLANT_SPACING_M
    state["plants_realigned"] = plants_realigned
    save_state(state)

    # Map/export this run — cluster so each icon shows all photos within 4 m
    run_obs = [existing[fid] for fid in run_file_ids if fid in existing]
    run_geo = filter_map_observations(
        [
            o
            for o in run_obs
            if o.latitude is not None and o.longitude is not None
        ],
        excluded_file_ids=EXCLUDED_OUTLIER_FILE_IDS,
    )
    run_clusters = cluster_by_radius(run_geo)
    # Display coords already set on shared observation objects via consolidated pass.
    mapped = [c.representative for c in run_clusters]
    consolidated = [c.representative for c in consolidated_clusters]

    report(
        "Writing KML / KMZ (4 m galleries, %.0f m plant spacing)…"
        % DEFAULT_PLANT_SPACING_M,
        0.92,
    )
    title = "Palm Plant Health"
    if folder_paths:
        title = "Palm Plant Health (%s)" % ", ".join(
            sorted(set(folder_paths.values()))[:5]
        )
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    runs_dir = OUTPUT_DIR / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)

    kml_path = write_kml(run_geo, out_path=OUTPUT_DIR / "palm_health.kml", title=title)
    kmz_path = write_kmz(run_geo, out_path=OUTPUT_DIR / "palm_health.kmz", title=title)
    json_path = OUTPUT_DIR / "palm_health.json"
    json_path.write_text(
        json.dumps(
            [
                {
                    "representative": c.representative.to_dict(),
                    "photo_count": c.photo_count,
                    "radius_m": c.radius_m,
                    "photos": [m.to_dict() for m in c.members],
                }
                for c in run_clusters
            ],
            indent=2,
        ),
        encoding="utf-8",
    )

    run_kml = write_kml(
        run_geo,
        out_path=runs_dir / ("run_%s.kml" % stamp),
        title=title,
    )
    run_json = runs_dir / ("run_%s.json" % stamp)
    run_json.write_text(
        json.dumps(
            {
                "run_at": datetime.now(timezone.utc).isoformat(),
                "selected_folders": sorted(set(folder_paths.values())) if folder_paths else [],
                "radius_m": DEFAULT_PHOTO_RADIUS_M,
                "plant_spacing_m": DEFAULT_PLANT_SPACING_M,
                "plants": [
                    {
                        "representative": c.representative.to_dict(),
                        "photo_count": c.photo_count,
                        "photos": [m.to_dict() for m in c.members],
                    }
                    for c in run_clusters
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    consolidated_title = "Palm Plant Health (consolidated — all runs)"
    consolidated_kml = write_kml(
        all_geo,
        out_path=OUTPUT_DIR / "palm_health_consolidated.kml",
        title=consolidated_title,
    )
    consolidated_kmz = write_kmz(
        all_geo,
        out_path=OUTPUT_DIR / "palm_health_consolidated.kmz",
        title=consolidated_title,
    )
    consolidated_json = OUTPUT_DIR / "palm_health_consolidated.json"
    consolidated_json.write_text(
        json.dumps(
            [
                {
                    "representative": c.representative.to_dict(),
                    "photo_count": c.photo_count,
                    "radius_m": c.radius_m,
                    "photos": [m.to_dict() for m in c.members],
                }
                for c in consolidated_clusters
            ],
            indent=2,
        ),
        encoding="utf-8",
    )

    log_path = OUTPUT_DIR / "runs_log.jsonl"
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(
            json.dumps(
                {
                    "run_at": datetime.now(timezone.utc).isoformat(),
                    "selected_folders": sorted(set(folder_paths.values())) if folder_paths else [],
                    "plants_this_run": len(mapped),
                    "photos_this_run": len(run_geo),
                    "plants_consolidated": len(consolidated),
                    "radius_m": DEFAULT_PHOTO_RADIUS_M,
                    "plant_spacing_m": DEFAULT_PLANT_SPACING_M,
                    "plants_realigned": plants_realigned,
                    "run_kml": str(run_kml),
                    "consolidated_kml": str(consolidated_kml),
                }
            )
            + "\n"
        )

    summary = {
        "photos_on_drive": len(files),
        "analyzed_now": analyzed_now,
        "skipped_cached": skipped_cached,
        "total_observations": len(observations),
        "plants_on_map": len(mapped),
        "plants_consolidated": len(consolidated),
        "plants_realigned": plants_realigned,
        "missing_coordinates": len(run_obs) - len(run_geo),
        "selected_folders": sorted(set(folder_paths.values())) if folder_paths else [],
        "kml_path": str(kml_path),
        "kmz_path": str(kmz_path),
        "json_path": str(json_path),
        "consolidated_kml_path": str(consolidated_kml),
        "consolidated_kmz_path": str(consolidated_kmz),
        "consolidated_json_path": str(consolidated_json),
        "run_kml_path": str(run_kml),
        "health_counts": _health_counts(mapped),
        "consolidated_health_counts": _health_counts(consolidated),
        "latest": [o.to_dict() for o in mapped],
        "clusters": [
            {
                "representative": c.representative.to_dict(),
                "photo_count": c.photo_count,
                "photos": [m.to_dict() for m in c.members],
            }
            for c in run_clusters
        ],
        "radius_m": DEFAULT_PHOTO_RADIUS_M,
        "plant_spacing_m": DEFAULT_PLANT_SPACING_M,
        "run_file_ids": list(run_file_ids),
    }
    report("Done", 1.0)
    return summary


def rebuild_consolidated_exports(
    spacing_m: float = DEFAULT_PLANT_SPACING_M,
) -> Dict[str, Any]:
    """Rebuild consolidated KML/KMZ/JSON from all stored observations."""
    ensure_dirs()
    state = load_state()
    observations = [PlantObservation.from_dict(x) for x in state.get("observations", [])]
    for obs in observations:
        if obs.file_id in EXCLUDED_OUTLIER_FILE_IDS:
            obs.excluded_from_map = True
    all_geo = filter_map_observations(
        [
            o
            for o in observations
            if o.latitude is not None and o.longitude is not None
        ],
        excluded_file_ids=EXCLUDED_OUTLIER_FILE_IDS,
    )
    clusters = cluster_by_radius(all_geo)
    plants_realigned = apply_lattice_to_clusters(clusters, spacing_m=spacing_m)
    state["observations"] = [o.to_dict() for o in observations]
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    state["plant_spacing_m"] = spacing_m
    state["plants_realigned"] = plants_realigned
    save_state(state)

    title = "Palm Plant Health (consolidated — all runs)"
    kml = write_kml(clusters, out_path=OUTPUT_DIR / "palm_health_consolidated.kml", title=title)
    kmz = write_kmz(clusters, out_path=OUTPUT_DIR / "palm_health_consolidated.kmz", title=title)
    json_path = OUTPUT_DIR / "palm_health_consolidated.json"
    json_path.write_text(
        json.dumps(
            [
                {
                    "representative": c.representative.to_dict(),
                    "photo_count": c.photo_count,
                    "radius_m": c.radius_m,
                    "plant_spacing_m": spacing_m,
                    "photos": [m.to_dict() for m in c.members],
                }
                for c in clusters
            ],
            indent=2,
        ),
        encoding="utf-8",
    )
    return {
        "plants_consolidated": len(clusters),
        "photos_consolidated": len(all_geo),
        "plants_realigned": plants_realigned,
        "consolidated_kml_path": str(kml),
        "consolidated_kmz_path": str(kmz),
        "consolidated_json_path": str(json_path),
        "health_counts": _health_counts([c.representative for c in clusters]),
        "radius_m": DEFAULT_PHOTO_RADIUS_M,
        "plant_spacing_m": spacing_m,
    }

def _health_counts(observations: List[PlantObservation]) -> Dict[str, int]:
    counts = {"green": 0, "amber": 0, "red": 0, "white": 0}
    for obs in observations:
        key = obs.health if obs.health in counts else "white"
        counts[key] += 1
    return counts
