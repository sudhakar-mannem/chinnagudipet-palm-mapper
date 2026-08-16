"""CLI: full-farm or selected-folder palm photo analysis."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import DRIVE_FOLDER_ID  # noqa: E402
from services.drive import list_subfolders  # noqa: E402
from services.pipeline import reset_analysis_state, run_pipeline  # noqa: E402


def main():
    parser = argparse.ArgumentParser(
        description="Sync palm photos from Drive, AI-score health + altitude, export KML/KMZ."
    )
    parser.add_argument(
        "--root",
        default=DRIVE_FOLDER_ID,
        help="Root Google Drive folder ID (Chinnagudipet farm)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Process the entire root folder (all nested photos)",
    )
    parser.add_argument(
        "--folder",
        action="append",
        default=[],
        help="Specific Drive folder ID to process (repeatable)",
    )
    parser.add_argument(
        "--folder-filter",
        default="",
        help="Process subfolders whose path contains this text",
    )
    parser.add_argument(
        "--list-folders",
        action="store_true",
        help="List subfolders and exit",
    )
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="Clear previous analysis/exports before running",
    )
    parser.add_argument(
        "--reanalyze",
        action="store_true",
        help="Re-run AI on photos already in cache",
    )
    parser.add_argument(
        "--force-download",
        action="store_true",
        help="Re-download photos from Drive",
    )
    args = parser.parse_args()

    if args.list_folders:
        folders = list_subfolders(root_folder_id=args.root, recursive=True)
        for f in folders:
            print("%s\t%s" % (f["id"], f["path"]))
        return

    if args.fresh:
        print("Clearing previous analysis state and exports…")
        reset_analysis_state(clear_exports=True)
        args.reanalyze = True

    selected = []
    if args.all:
        selected = [{"id": args.root, "path": "Chinnagudipet farm (entire root)", "name": "root"}]
    elif args.folder:
        folders = list_subfolders(root_folder_id=args.root, recursive=True)
        id_set = set(args.folder)
        selected = [f for f in folders if f["id"] in id_set]
        known = {f["id"] for f in selected}
        for fid in args.folder:
            if fid not in known:
                selected.append({"id": fid, "path": fid, "name": fid})
    elif args.folder_filter:
        folders = list_subfolders(root_folder_id=args.root, recursive=True)
        needle = args.folder_filter.lower()
        selected = [f for f in folders if needle in (f.get("path") or "").lower()]
        if not selected:
            print("No folders matched filter: %s" % args.folder_filter)
            sys.exit(1)
    else:
        print("Use one of: --all | --folder-filter TEXT | --folder FOLDER_ID")
        print("For a full from-scratch farm run with altitude:")
        print("  python cli.py --all --fresh")
        sys.exit(2)

    print("Selected:")
    for f in selected:
        print("  - %s" % f["path"])
    if args.reanalyze:
        print("Mode: reanalyze (AI will re-read lat/lon/altitude stamps)")

    def progress(msg, pct):
        bar = int(pct * 30)
        sys.stdout.write(
            "\r[%s%s] %3.0f%% %s"
            % ("#" * bar, "." * (30 - bar), pct * 100, msg[:60].ljust(60))
        )
        sys.stdout.flush()
        if pct >= 1.0:
            sys.stdout.write("\n")

    summary = run_pipeline(
        folder_ids=[f["id"] for f in selected],
        folder_paths={f["id"]: f["path"] for f in selected},
        force_download=args.force_download,
        reanalyze=args.reanalyze,
        progress=progress,
    )

    with_alt = sum(
        1 for p in summary.get("latest") or [] if p.get("altitude") is not None
    )
    print("\nResults")
    print("  Folders              : %s" % summary.get("selected_folders"))
    print("  Photos               : %s" % summary["photos_on_drive"])
    print("  Analyzed now         : %s" % summary["analyzed_now"])
    print("  Plants on map        : %s" % summary["plants_on_map"])
    print("  With altitude        : %s" % with_alt)
    print("  Missing GPS          : %s" % summary["missing_coordinates"])
    print("  Consolidated plants  : %s" % summary.get("plants_consolidated"))
    print("  Health counts        : %s" % summary["health_counts"])
    print("  Run KML              : %s" % summary["kml_path"])
    print("  Consolidated KML     : %s" % summary.get("consolidated_kml_path"))


if __name__ == "__main__":
    main()
