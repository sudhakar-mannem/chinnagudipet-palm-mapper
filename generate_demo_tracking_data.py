"""Generate demo GPS tracking data for testing worker tracking features."""
from __future__ import annotations

import json
import math
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import CACHE_DIR, ensure_dirs  # noqa
from services.worker_tracking import (  # noqa
    FarmGeofence,
    GPSPoint,
    RouteAnalyzer,
    Worker,
    WorkerTrackingService,
)


def generate_realistic_farm_route(
    start_lat: float,
    start_lon: float,
    farm_center_lat: float,
    farm_center_lon: float,
    farm_radius_m: float,
    start_time: datetime,
    work_duration_hours: float,
    tracking_interval_minutes: int = 3,
) -> list[GPSPoint]:
    """
    Generate a realistic worker route within farm boundaries.
    
    Simulates:
    - Walking between plant rows
    - Stopping to work on specific plants
    - Movement patterns typical of farm work
    - GPS accuracy variations
    - Battery drain over time
    """
    points = []
    current_time = start_time
    current_lat = start_lat
    current_lon = start_lon
    battery = 100.0
    
    # Constants
    meters_per_deg_lat = 111320.0
    meters_per_deg_lon = meters_per_deg_lat * math.cos(math.radians(farm_center_lat))
    walking_speed_m_per_s = 1.0  # Slow walking pace on farm
    working_stop_probability = 0.15  # 15% chance to stop at each interval
    
    end_time = start_time + timedelta(hours=work_duration_hours)
    
    while current_time < end_time:
        # Add current position
        accuracy = random.uniform(5.0, 15.0)  # GPS accuracy in meters
        
        # Add small GPS jitter
        jitter_lat = random.gauss(0, accuracy / meters_per_deg_lat)
        jitter_lon = random.gauss(0, accuracy / meters_per_deg_lon)
        
        point = GPSPoint(
            latitude=current_lat + jitter_lat,
            longitude=current_lon + jitter_lon,
            altitude=random.uniform(20.0, 30.0),  # Typical elevation
            timestamp=current_time.isoformat() + "Z",
            accuracy=accuracy,
            speed=0.0,  # Will be updated if moving
            bearing=None,
            battery_level=battery,
            gps_enabled=True,
            source="simulated",
        )
        points.append(point)
        
        # Drain battery (about 5% per hour of GPS tracking)
        battery -= (tracking_interval_minutes / 60.0) * 5.0
        battery = max(0.0, battery)
        
        # Decide if worker stops to work
        if random.random() < working_stop_probability:
            # Stop for 10-45 minutes
            stop_duration_minutes = random.randint(10, 45)
            num_stop_points = stop_duration_minutes // tracking_interval_minutes
            
            for _ in range(num_stop_points):
                current_time += timedelta(minutes=tracking_interval_minutes)
                if current_time >= end_time:
                    break
                
                # Small movement while working (within 5m)
                stop_jitter_lat = random.gauss(0, 5.0 / meters_per_deg_lat)
                stop_jitter_lon = random.gauss(0, 5.0 / meters_per_deg_lon)
                
                stop_point = GPSPoint(
                    latitude=current_lat + stop_jitter_lat,
                    longitude=current_lon + stop_jitter_lon,
                    altitude=random.uniform(20.0, 30.0),
                    timestamp=current_time.isoformat() + "Z",
                    accuracy=random.uniform(5.0, 15.0),
                    speed=0.0,
                    bearing=None,
                    battery_level=battery,
                    gps_enabled=True,
                    source="simulated",
                )
                points.append(stop_point)
                
                battery -= (tracking_interval_minutes / 60.0) * 5.0
                battery = max(0.0, battery)
        
        # Move to next location
        # Walk in a semi-random direction, biased toward staying within farm
        dx_center = farm_center_lon - current_lon
        dy_center = farm_center_lat - current_lat
        dist_to_center = math.sqrt(
            (dx_center * meters_per_deg_lon) ** 2 + (dy_center * meters_per_deg_lat) ** 2
        )
        
        # If getting close to edge, bias movement toward center
        edge_bias = 0.0
        if dist_to_center > farm_radius_m * 0.7:
            edge_bias = 0.7
        
        # Random angle with center bias
        if random.random() < edge_bias:
            # Move toward center
            angle = math.atan2(dy_center, dx_center)
            angle += random.gauss(0, 0.3)  # Add some randomness
        else:
            # Random direction
            angle = random.uniform(0, 2 * math.pi)
        
        # Distance to move in this interval
        time_delta_seconds = tracking_interval_minutes * 60
        move_distance_m = walking_speed_m_per_s * time_delta_seconds * random.uniform(0.5, 1.0)
        
        # Update position
        delta_lat = move_distance_m * math.sin(angle) / meters_per_deg_lat
        delta_lon = move_distance_m * math.cos(angle) / meters_per_deg_lon
        
        current_lat += delta_lat
        current_lon += delta_lon
        
        # Update time
        current_time += timedelta(minutes=tracking_interval_minutes)
    
    return points


def main():
    print("=" * 70)
    print("PALM FARM WORKER TRACKING - DEMO DATA GENERATOR")
    print("=" * 70)
    print()
    
    ensure_dirs()
    TRACKING_DIR = CACHE_DIR / "worker_tracking"
    tracking_service = WorkerTrackingService(TRACKING_DIR)
    
    # Check if we should generate fresh data
    response = input("Generate fresh demo data? (y/n) [y]: ").strip().lower()
    if response and response != "y":
        print("Cancelled.")
        return
    
    # Setup demo workers
    print("\n1. Creating demo workers...")
    workers = [
        Worker(
            worker_id="W001",
            name="రామయ్య (Ramayya)",
            phone="+91 9876543210",
            active=True,
            start_date="2024-01-01",
            notes="Experienced palm worker, 10 years",
        ),
        Worker(
            worker_id="W002",
            name="కృష్ణయ్య (Krishnayya)",
            phone="+91 9876543211",
            active=True,
            start_date="2024-01-15",
            notes="New worker, learning phase",
        ),
    ]
    tracking_service.save_workers(workers)
    print(f"   ✓ Created {len(workers)} demo workers")
    
    # Setup demo geofence
    print("\n2. Creating farm geofence...")
    geofence = FarmGeofence(
        name="Chinnagudipet Palm Farm - Demo",
        center_latitude=16.801234,
        center_longitude=80.501234,
        radius_m=400.0,  # 400m radius farm
    )
    tracking_service.save_geofences([geofence])
    print(f"   ✓ Created geofence: {geofence.name}")
    print(f"     Center: {geofence.center_latitude}, {geofence.center_longitude}")
    print(f"     Radius: {geofence.radius_m}m")
    
    # Generate route data for past 7 days
    print("\n3. Generating GPS route data...")
    analyzer = RouteAnalyzer(
        stop_radius_m=15.0,
        stop_min_duration_minutes=5.0,
    )
    
    today = datetime.now().date()
    
    for days_ago in range(7, 0, -1):
        route_date = today - timedelta(days=days_ago)
        date_str = route_date.strftime("%Y-%m-%d")
        
        print(f"\n   Generating data for {date_str}...")
        
        for worker in workers:
            # Random start time between 7:00 and 8:00 AM
            start_hour = random.randint(7, 8)
            start_minute = random.randint(0, 59)
            start_time = datetime.combine(route_date, datetime.min.time()).replace(
                hour=start_hour, minute=start_minute
            )
            
            # Random work duration 8-10 hours
            work_hours = random.uniform(8.0, 10.0)
            
            # Entry point near farm edge
            entry_angle = random.uniform(0, 2 * math.pi)
            entry_radius = geofence.radius_m * 0.9
            start_lat = geofence.center_latitude + (
                entry_radius * math.sin(entry_angle) / 111320.0
            )
            start_lon = geofence.center_longitude + (
                entry_radius * math.cos(entry_angle)
                / (111320.0 * math.cos(math.radians(geofence.center_latitude)))
            )
            
            # Generate route
            points = generate_realistic_farm_route(
                start_lat=start_lat,
                start_lon=start_lon,
                farm_center_lat=geofence.center_latitude,
                farm_center_lon=geofence.center_longitude,
                farm_radius_m=geofence.radius_m,
                start_time=start_time,
                work_duration_hours=work_hours,
                tracking_interval_minutes=3,
            )
            
            # Save route
            route = tracking_service.add_points_to_route(
                worker_id=worker.worker_id,
                worker_name=worker.name,
                date=date_str,
                points=points,
                analyzer=analyzer,
                geofence=geofence,
            )
            
            print(
                f"     ✓ {worker.name}: {len(route.points)} points, "
                f"{len(route.stops)} stops, "
                f"{route.total_distance_km:.2f} km, "
                f"{route.time_inside_farm_minutes:.0f} min in farm"
            )
    
    print("\n" + "=" * 70)
    print("✅ DEMO DATA GENERATION COMPLETE!")
    print("=" * 70)
    print(f"\nData saved to: {TRACKING_DIR}")
    print("\nYou can now:")
    print("1. Run the Streamlit app: streamlit run app.py")
    print("2. Go to 'Worker Tracking' page")
    print("3. Select a worker and date to view their route")
    print()
    
    # Generate a sample GPS JSON file for testing upload
    print("Generating sample GPS JSON file for upload testing...")
    sample_date = today - timedelta(days=1)
    sample_time = datetime.combine(sample_date, datetime.min.time()).replace(hour=7, minute=30)
    
    sample_points = generate_realistic_farm_route(
        start_lat=geofence.center_latitude + 0.003,
        start_lon=geofence.center_longitude - 0.003,
        farm_center_lat=geofence.center_latitude,
        farm_center_lon=geofence.center_longitude,
        farm_radius_m=geofence.radius_m,
        start_time=sample_time,
        work_duration_hours=4.0,
        tracking_interval_minutes=2,
    )
    
    sample_file = ROOT / "sample_gps_tracking.json"
    sample_data = [p.to_dict() for p in sample_points]
    sample_file.write_text(json.dumps(sample_data, indent=2), encoding="utf-8")
    print(f"✓ Sample GPS file: {sample_file}")
    print("  Use this to test the GPS upload feature")
    print()


if __name__ == "__main__":
    main()
