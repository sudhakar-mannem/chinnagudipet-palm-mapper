#!/usr/bin/env python3
"""
Command-line interface for worker tracking (no Streamlit needed).
Use this for maximum stability and automation.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import CACHE_DIR, ensure_dirs  # noqa
from services.models import PlantObservation  # noqa
from services.pipeline import load_state  # noqa
from services.worker_tracking import (  # noqa
    FarmGeofence,
    GPSPoint,
    RouteAnalyzer,
    Worker,
    WorkerTrackingService,
)


def format_time(iso_time: str) -> str:
    """Format ISO timestamp to readable time."""
    try:
        dt = datetime.fromisoformat(iso_time.replace("Z", "+00:00"))
        return dt.strftime("%H:%M:%S")
    except (ValueError, AttributeError):
        return iso_time


def format_duration(minutes: float) -> str:
    """Format duration in minutes to HH:MM format."""
    hours = int(minutes // 60)
    mins = int(minutes % 60)
    return f"{hours:02d}:{mins:02d}"


def upload_gps_data(args):
    """Upload GPS tracking data from JSON file."""
    ensure_dirs()
    TRACKING_DIR = CACHE_DIR / "worker_tracking"
    tracking_service = WorkerTrackingService(TRACKING_DIR)
    
    gps_file = Path(args.file)
    if not gps_file.exists():
        print(f"❌ Error: File not found: {gps_file}")
        return 1
    
    print(f"Reading GPS data from: {gps_file}")
    
    try:
        with open(gps_file, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON file: {e}")
        return 1
    
    if not isinstance(data, list):
        print("❌ Error: JSON must be an array of GPS points")
        return 1
    
    # Parse GPS points
    points = []
    for item in data:
        try:
            point = GPSPoint(
                latitude=float(item["latitude"]),
                longitude=float(item["longitude"]),
                timestamp=item.get("timestamp", datetime.now().isoformat()),
                altitude=item.get("altitude"),
                accuracy=item.get("accuracy", 10.0),
                speed=item.get("speed"),
                bearing=item.get("bearing"),
                battery_level=item.get("battery_level"),
                gps_enabled=item.get("gps_enabled", True),
                source=item.get("source", "mobile"),
            )
            points.append(point)
        except (KeyError, ValueError) as e:
            print(f"⚠️  Skipping invalid point: {e}")
    
    if not points:
        print("❌ Error: No valid GPS points found")
        return 1
    
    print(f"✓ Parsed {len(points)} GPS points")
    
    # Get worker info
    workers = tracking_service.load_workers()
    worker = next((w for w in workers if w.worker_id == args.worker), None)
    
    if not worker:
        print(f"❌ Error: Worker '{args.worker}' not found")
        print("Available workers:")
        for w in workers:
            print(f"  - {w.worker_id}: {w.name}")
        return 1
    
    # Load geofence
    geofences = tracking_service.load_geofences()
    geofence = geofences[0] if geofences else None
    
    # Load plant data
    state = load_state()
    plant_observations = state.get("observations", [])
    plant_obs_objects = (
        [PlantObservation.from_dict(o) for o in plant_observations]
        if plant_observations
        else []
    )
    
    # Process route
    print(f"\nProcessing route for {worker.name} on {args.date}...")
    
    route = tracking_service.add_points_to_route(
        worker_id=worker.worker_id,
        worker_name=worker.name,
        date=args.date,
        points=points,
        analyzer=RouteAnalyzer(),
        geofence=geofence,
        plant_observations=plant_obs_objects,
    )
    
    # Display summary
    print("\n" + "=" * 70)
    print(f"✅ ROUTE SAVED SUCCESSFULLY")
    print("=" * 70)
    print(f"\nWorker: {worker.name} ({worker.worker_id})")
    print(f"Date: {args.date}")
    print(f"\n📊 Summary:")
    print(f"  GPS Points: {len(route.points)}")
    print(f"  Stops Detected: {len(route.stops)}")
    print(f"  Distance: {route.total_distance_km:.2f} km")
    print(f"  Total Duration: {format_duration(route.total_duration_minutes)}")
    
    if route.first_entry_time:
        print(f"  First Entry: {format_time(route.first_entry_time)}")
    if route.last_exit_time:
        print(f"  Last Exit: {format_time(route.last_exit_time)}")
    if route.time_inside_farm_minutes > 0:
        print(f"  Time in Farm: {format_duration(route.time_inside_farm_minutes)}")
    
    if route.stops:
        print(f"\n⏸️  Stops:")
        for i, stop in enumerate(route.stops[:5], 1):
            print(
                f"  {i}. {format_time(stop.start_time)} - "
                f"{format_time(stop.end_time)} "
                f"({format_duration(stop.duration_minutes)})"
            )
        if len(route.stops) > 5:
            print(f"  ... and {len(route.stops) - 5} more")
    
    if route.visited_plant_ids:
        print(f"\n🌴 Plant Coverage: {len(route.visited_plant_ids)} zones visited")
    
    if route.gps_off_periods:
        print(f"\n⚠️  GPS Gaps: {len(route.gps_off_periods)} period(s)")
    
    if route.battery_low_warnings:
        print(f"⚠️  Low Battery: {len(route.battery_low_warnings)} warning(s)")
    
    print()
    return 0


def view_route(args):
    """View route summary for a worker on a date."""
    ensure_dirs()
    TRACKING_DIR = CACHE_DIR / "worker_tracking"
    tracking_service = WorkerTrackingService(TRACKING_DIR)
    
    route = tracking_service.load_route(args.worker, args.date)
    
    if not route:
        print(f"❌ No route found for {args.worker} on {args.date}")
        return 1
    
    print("=" * 70)
    print(f"ROUTE SUMMARY")
    print("=" * 70)
    print(f"\nWorker: {route.worker_name} ({route.worker_id})")
    print(f"Date: {route.date}")
    print(f"\n📊 Summary:")
    print(f"  GPS Points: {len(route.points)}")
    print(f"  Stops: {len(route.stops)}")
    print(f"  Distance: {route.total_distance_km:.2f} km")
    print(f"  Duration: {format_duration(route.total_duration_minutes)}")
    
    if route.first_entry_time:
        print(f"\n🚪 Entry/Exit:")
        print(f"  First Entry: {format_time(route.first_entry_time)}")
        print(f"  Last Exit: {format_time(route.last_exit_time)}")
        print(f"  Time in Farm: {format_duration(route.time_inside_farm_minutes)}")
    
    if route.stops:
        print(f"\n⏸️  Stops ({len(route.stops)} total):")
        for i, stop in enumerate(route.stops[:10], 1):
            print(
                f"  {i}. {format_time(stop.start_time)} - "
                f"{format_time(stop.end_time)} "
                f"({format_duration(stop.duration_minutes)}) - "
                f"{stop.latitude:.6f}, {stop.longitude:.6f}"
            )
        if len(route.stops) > 10:
            print(f"  ... and {len(route.stops) - 10} more")
    
    if route.visited_plant_ids:
        print(f"\n🌴 Plant Coverage:")
        print(f"  Visited {len(route.visited_plant_ids)} plant zones")
        if len(route.visited_plant_ids) <= 20:
            print(f"  Zones: {', '.join(route.visited_plant_ids)}")
    
    if route.gps_off_periods:
        print(f"\n⚠️  Issues:")
        print(f"  GPS Gaps: {len(route.gps_off_periods)} period(s)")
        for start, end in route.gps_off_periods[:3]:
            print(f"    - {format_time(start)} to {format_time(end)}")
    
    if route.battery_low_warnings:
        print(f"  Low Battery: {len(route.battery_low_warnings)} warning(s)")
    
    print()
    return 0


def list_routes(args):
    """List all routes for a worker."""
    ensure_dirs()
    TRACKING_DIR = CACHE_DIR / "worker_tracking"
    tracking_service = WorkerTrackingService(TRACKING_DIR)
    
    dates = tracking_service.list_worker_routes(args.worker)
    
    if not dates:
        print(f"No routes found for worker: {args.worker}")
        return 1
    
    print(f"\nRoutes for worker: {args.worker}")
    print("=" * 70)
    
    for date in dates:
        route = tracking_service.load_route(args.worker, date)
        if route:
            print(
                f"  {date}: {len(route.points)} points, "
                f"{len(route.stops)} stops, "
                f"{route.total_distance_km:.2f} km"
            )
    
    print()
    return 0


def list_workers(args):
    """List all configured workers."""
    ensure_dirs()
    TRACKING_DIR = CACHE_DIR / "worker_tracking"
    tracking_service = WorkerTrackingService(TRACKING_DIR)
    
    workers = tracking_service.load_workers()
    
    if not workers:
        print("No workers configured")
        return 1
    
    print("\nConfigured Workers:")
    print("=" * 70)
    
    for worker in workers:
        status = "✅ Active" if worker.active else "❌ Inactive"
        print(f"  {worker.worker_id}: {worker.name} - {status}")
        if worker.phone:
            print(f"    Phone: {worker.phone}")
        
        # Count routes
        routes = tracking_service.list_worker_routes(worker.worker_id)
        print(f"    Routes: {len(routes)} day(s)")
    
    print()
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Worker GPS Tracking CLI - Stable, no Streamlit needed"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Upload command
    upload_parser = subparsers.add_parser("upload", help="Upload GPS tracking data")
    upload_parser.add_argument("worker", help="Worker ID (e.g., W001)")
    upload_parser.add_argument("date", help="Date (YYYY-MM-DD)")
    upload_parser.add_argument("file", help="GPS JSON file path")
    
    # View command
    view_parser = subparsers.add_parser("view", help="View route summary")
    view_parser.add_argument("worker", help="Worker ID")
    view_parser.add_argument("date", help="Date (YYYY-MM-DD)")
    
    # List routes command
    list_parser = subparsers.add_parser("list", help="List routes for a worker")
    list_parser.add_argument("worker", help="Worker ID")
    
    # List workers command
    subparsers.add_parser("workers", help="List all workers")
    
    args = parser.parse_args()
    
    if args.command == "upload":
        return upload_gps_data(args)
    elif args.command == "view":
        return view_route(args)
    elif args.command == "list":
        return list_routes(args)
    elif args.command == "workers":
        return list_workers(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
