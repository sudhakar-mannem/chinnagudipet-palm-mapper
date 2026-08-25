"""Worker GPS tracking with geofencing, route history, and idle detection."""
from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .models import haversine_m


@dataclass
class GPSPoint:
    """Single GPS tracking point."""
    
    latitude: float
    longitude: float
    altitude: Optional[float] = None
    timestamp: str = ""  # ISO 8601
    accuracy: float = 10.0  # meters
    speed: Optional[float] = None  # m/s
    bearing: Optional[float] = None  # degrees
    battery_level: Optional[float] = None  # 0-100
    gps_enabled: bool = True
    source: str = "mobile"  # mobile | manual | synced
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GPSPoint":
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


@dataclass
class WorkerStop:
    """Detected stop or idle period."""
    
    start_time: str  # ISO 8601
    end_time: str  # ISO 8601
    latitude: float
    longitude: float
    duration_minutes: float
    radius_m: float  # Maximum distance from center during stop
    point_count: int  # Number of GPS points in this stop
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkerStop":
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


@dataclass
class FarmGeofence:
    """Farm boundary definition for automatic entry/exit detection."""
    
    name: str
    center_latitude: float
    center_longitude: float
    radius_m: float  # Circular geofence radius
    # Optional polygon vertices for more precise boundary
    polygon_vertices: List[Tuple[float, float]] = field(default_factory=list)
    
    def contains_point(self, lat: float, lon: float) -> bool:
        """Check if point is inside the geofence."""
        # If polygon vertices provided, use polygon containment
        if self.polygon_vertices and len(self.polygon_vertices) >= 3:
            return self._point_in_polygon(lat, lon)
        
        # Otherwise use circular geofence
        distance = haversine_m(lat, lon, self.center_latitude, self.center_longitude)
        return distance <= self.radius_m
    
    def _point_in_polygon(self, lat: float, lon: float) -> bool:
        """Ray casting algorithm for point-in-polygon test."""
        vertices = self.polygon_vertices
        n = len(vertices)
        inside = False
        
        p1_lat, p1_lon = vertices[0]
        for i in range(1, n + 1):
            p2_lat, p2_lon = vertices[i % n]
            
            if lon > min(p1_lon, p2_lon):
                if lon <= max(p1_lon, p2_lon):
                    if lat <= max(p1_lat, p2_lat):
                        if p1_lon != p2_lon:
                            x_intersect = (lon - p1_lon) * (p2_lat - p1_lat) / (p2_lon - p1_lon) + p1_lat
                            if p1_lat == p2_lat or lat <= x_intersect:
                                inside = not inside
            
            p1_lat, p1_lon = p2_lat, p2_lon
        
        return inside
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FarmGeofence":
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


@dataclass
class WorkerRoute:
    """Complete route for one worker on one day."""
    
    worker_id: str
    worker_name: str
    date: str  # YYYY-MM-DD
    
    # Route tracking
    points: List[GPSPoint] = field(default_factory=list)
    stops: List[WorkerStop] = field(default_factory=list)
    
    # Geofence events
    first_entry_time: Optional[str] = None
    last_exit_time: Optional[str] = None
    entry_count: int = 0
    exit_count: int = 0
    
    # Summary stats
    total_duration_minutes: float = 0.0
    time_inside_farm_minutes: float = 0.0
    time_moving_minutes: float = 0.0
    time_stopped_minutes: float = 0.0
    total_distance_km: float = 0.0
    
    # Status tracking
    gps_off_periods: List[Tuple[str, str]] = field(default_factory=list)  # (start, end)
    battery_low_warnings: List[str] = field(default_factory=list)  # timestamps
    
    # Coverage (which plant zones were visited)
    visited_plant_ids: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["points"] = [p.to_dict() for p in self.points]
        result["stops"] = [s.to_dict() for s in self.stops]
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkerRoute":
        points = [GPSPoint.from_dict(p) for p in data.pop("points", [])]
        stops = [WorkerStop.from_dict(s) for s in data.pop("stops", [])]
        route = cls(**{k: v for k, v in data.items() if k in cls.__annotations__})
        route.points = points
        route.stops = stops
        return route


@dataclass
class Worker:
    """Worker profile."""
    
    worker_id: str
    name: str
    phone: Optional[str] = None
    active: bool = True
    start_date: Optional[str] = None  # YYYY-MM-DD
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Worker":
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


class RouteAnalyzer:
    """Analyze GPS routes for stops, movement, and farm coverage."""
    
    def __init__(
        self,
        stop_radius_m: float = 15.0,
        stop_min_duration_minutes: float = 5.0,
        moving_speed_threshold_m_per_s: float = 0.3,
    ):
        self.stop_radius_m = stop_radius_m
        self.stop_min_duration_minutes = stop_min_duration_minutes
        self.moving_speed_threshold = moving_speed_threshold_m_per_s
    
    def detect_stops(self, points: List[GPSPoint]) -> List[WorkerStop]:
        """Detect periods where worker stayed in roughly the same location."""
        if len(points) < 2:
            return []
        
        stops = []
        current_stop_points = []
        
        for point in points:
            if not current_stop_points:
                current_stop_points.append(point)
                continue
            
            # Calculate center of current potential stop
            center_lat = sum(p.latitude for p in current_stop_points) / len(current_stop_points)
            center_lon = sum(p.longitude for p in current_stop_points) / len(current_stop_points)
            
            # Check if point is within stop radius
            distance = haversine_m(point.latitude, point.longitude, center_lat, center_lon)
            
            if distance <= self.stop_radius_m:
                current_stop_points.append(point)
            else:
                # End of stop - check if it meets minimum duration
                if len(current_stop_points) >= 2:
                    stop = self._create_stop_from_points(current_stop_points)
                    if stop and stop.duration_minutes >= self.stop_min_duration_minutes:
                        stops.append(stop)
                
                # Start new potential stop
                current_stop_points = [point]
        
        # Handle final stop
        if len(current_stop_points) >= 2:
            stop = self._create_stop_from_points(current_stop_points)
            if stop and stop.duration_minutes >= self.stop_min_duration_minutes:
                stops.append(stop)
        
        return stops
    
    def _create_stop_from_points(self, points: List[GPSPoint]) -> Optional[WorkerStop]:
        """Create a WorkerStop from a list of GPS points."""
        if len(points) < 2:
            return None
        
        # Calculate center
        center_lat = sum(p.latitude for p in points) / len(points)
        center_lon = sum(p.longitude for p in points) / len(points)
        
        # Calculate maximum radius
        max_radius = max(
            haversine_m(p.latitude, p.longitude, center_lat, center_lon)
            for p in points
        )
        
        # Parse timestamps
        try:
            start = datetime.fromisoformat(points[0].timestamp.replace("Z", "+00:00"))
            end = datetime.fromisoformat(points[-1].timestamp.replace("Z", "+00:00"))
            duration_minutes = (end - start).total_seconds() / 60.0
        except (ValueError, AttributeError):
            return None
        
        return WorkerStop(
            start_time=points[0].timestamp,
            end_time=points[-1].timestamp,
            latitude=center_lat,
            longitude=center_lon,
            duration_minutes=duration_minutes,
            radius_m=max_radius,
            point_count=len(points),
        )
    
    def calculate_distance(self, points: List[GPSPoint]) -> float:
        """Calculate total distance traveled in kilometers."""
        if len(points) < 2:
            return 0.0
        
        total_m = 0.0
        for i in range(len(points) - 1):
            p1, p2 = points[i], points[i + 1]
            total_m += haversine_m(p1.latitude, p1.longitude, p2.latitude, p2.longitude)
        
        return total_m / 1000.0  # Convert to km
    
    def detect_geofence_events(
        self, points: List[GPSPoint], geofence: FarmGeofence
    ) -> Tuple[Optional[str], Optional[str], int, int]:
        """
        Detect first entry, last exit, and count crossings.
        
        Returns: (first_entry_time, last_exit_time, entry_count, exit_count)
        """
        if not points:
            return None, None, 0, 0
        
        first_entry = None
        last_exit = None
        entry_count = 0
        exit_count = 0
        
        was_inside = None
        for point in points:
            inside = geofence.contains_point(point.latitude, point.longitude)
            
            if was_inside is not None:
                if not was_inside and inside:
                    # Entry event
                    entry_count += 1
                    if first_entry is None:
                        first_entry = point.timestamp
                elif was_inside and not inside:
                    # Exit event
                    exit_count += 1
                    last_exit = point.timestamp
            
            was_inside = inside
        
        return first_entry, last_exit, entry_count, exit_count
    
    def calculate_time_inside_farm(
        self, points: List[GPSPoint], geofence: FarmGeofence
    ) -> float:
        """Calculate total time spent inside farm in minutes."""
        if len(points) < 2:
            return 0.0
        
        total_minutes = 0.0
        
        for i in range(len(points) - 1):
            p1, p2 = points[i], points[i + 1]
            inside1 = geofence.contains_point(p1.latitude, p1.longitude)
            inside2 = geofence.contains_point(p2.latitude, p2.longitude)
            
            # If both points inside, add the time between them
            if inside1 and inside2:
                try:
                    t1 = datetime.fromisoformat(p1.timestamp.replace("Z", "+00:00"))
                    t2 = datetime.fromisoformat(p2.timestamp.replace("Z", "+00:00"))
                    total_minutes += (t2 - t1).total_seconds() / 60.0
                except (ValueError, AttributeError):
                    pass
        
        return total_minutes
    
    def detect_coverage(
        self,
        points: List[GPSPoint],
        plant_observations: List[Any],  # List[PlantObservation]
        coverage_radius_m: float = 10.0,
    ) -> List[str]:
        """Determine which plant zones were visited based on proximity."""
        visited_plant_ids = set()
        
        for point in points:
            for obs in plant_observations:
                if not hasattr(obs, "plant_id") or not obs.plant_id:
                    continue
                if obs.latitude is None or obs.longitude is None:
                    continue
                
                distance = haversine_m(
                    point.latitude,
                    point.longitude,
                    float(obs.latitude),
                    float(obs.longitude),
                )
                
                if distance <= coverage_radius_m:
                    visited_plant_ids.add(obs.plant_id)
        
        return sorted(visited_plant_ids)


class WorkerTrackingService:
    """Manage worker tracking data storage and retrieval."""
    
    def __init__(self, storage_dir: Path):
        self.storage_dir = Path(storage_dir)
        self.routes_dir = self.storage_dir / "routes"
        self.workers_file = self.storage_dir / "workers.json"
        self.geofences_file = self.storage_dir / "geofences.json"
        
        self._ensure_dirs()
    
    def _ensure_dirs(self):
        """Create storage directories."""
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.routes_dir.mkdir(parents=True, exist_ok=True)
    
    def save_route(self, route: WorkerRoute):
        """Save or update a worker's daily route."""
        route_file = self.routes_dir / f"{route.worker_id}_{route.date}.json"
        route_file.write_text(json.dumps(route.to_dict(), indent=2), encoding="utf-8")
    
    def load_route(self, worker_id: str, date: str) -> Optional[WorkerRoute]:
        """Load a worker's route for a specific date."""
        route_file = self.routes_dir / f"{worker_id}_{date}.json"
        if not route_file.exists():
            return None
        
        try:
            data = json.loads(route_file.read_text(encoding="utf-8"))
            return WorkerRoute.from_dict(data)
        except Exception:
            return None
    
    def list_worker_routes(self, worker_id: str) -> List[str]:
        """List all dates with routes for a worker (newest first)."""
        pattern = f"{worker_id}_*.json"
        files = sorted(self.routes_dir.glob(pattern), reverse=True)
        return [f.stem.split("_", 1)[1] for f in files]
    
    def add_points_to_route(
        self,
        worker_id: str,
        worker_name: str,
        date: str,
        points: List[GPSPoint],
        analyzer: Optional[RouteAnalyzer] = None,
        geofence: Optional[FarmGeofence] = None,
        plant_observations: Optional[List[Any]] = None,
    ):
        """Add GPS points to a route and update analytics."""
        route = self.load_route(worker_id, date)
        if route is None:
            route = WorkerRoute(worker_id=worker_id, worker_name=worker_name, date=date)
        
        # Add new points (deduplicate by timestamp)
        existing_timestamps = {p.timestamp for p in route.points}
        new_points = [p for p in points if p.timestamp not in existing_timestamps]
        route.points.extend(new_points)
        route.points.sort(key=lambda p: p.timestamp)
        
        # Re-analyze route
        if analyzer is None:
            analyzer = RouteAnalyzer()
        
        if route.points:
            # Detect stops
            route.stops = analyzer.detect_stops(route.points)
            route.time_stopped_minutes = sum(s.duration_minutes for s in route.stops)
            
            # Calculate distance
            route.total_distance_km = analyzer.calculate_distance(route.points)
            
            # Calculate total duration
            try:
                start = datetime.fromisoformat(route.points[0].timestamp.replace("Z", "+00:00"))
                end = datetime.fromisoformat(route.points[-1].timestamp.replace("Z", "+00:00"))
                route.total_duration_minutes = (end - start).total_seconds() / 60.0
            except (ValueError, AttributeError, IndexError):
                pass
            
            # Geofence analysis
            if geofence:
                first_entry, last_exit, entry_count, exit_count = analyzer.detect_geofence_events(
                    route.points, geofence
                )
                route.first_entry_time = first_entry
                route.last_exit_time = last_exit
                route.entry_count = entry_count
                route.exit_count = exit_count
                route.time_inside_farm_minutes = analyzer.calculate_time_inside_farm(
                    route.points, geofence
                )
            
            # Calculate moving time
            route.time_moving_minutes = max(
                0.0, route.total_duration_minutes - route.time_stopped_minutes
            )
            
            # Detect coverage
            if plant_observations:
                route.visited_plant_ids = analyzer.detect_coverage(
                    route.points, plant_observations
                )
            
            # Detect GPS/battery issues
            route.gps_off_periods = self._detect_gps_gaps(route.points)
            route.battery_low_warnings = self._detect_low_battery(route.points)
        
        self.save_route(route)
        return route
    
    def _detect_gps_gaps(
        self, points: List[GPSPoint], max_gap_minutes: float = 15.0
    ) -> List[Tuple[str, str]]:
        """Detect periods when GPS tracking was off."""
        gaps = []
        
        for i in range(len(points) - 1):
            p1, p2 = points[i], points[i + 1]
            try:
                t1 = datetime.fromisoformat(p1.timestamp.replace("Z", "+00:00"))
                t2 = datetime.fromisoformat(p2.timestamp.replace("Z", "+00:00"))
                gap_minutes = (t2 - t1).total_seconds() / 60.0
                
                if gap_minutes > max_gap_minutes:
                    gaps.append((p1.timestamp, p2.timestamp))
            except (ValueError, AttributeError):
                pass
        
        return gaps
    
    def _detect_low_battery(
        self, points: List[GPSPoint], threshold: float = 20.0
    ) -> List[str]:
        """Detect timestamps when battery was low."""
        warnings = []
        
        for point in points:
            if point.battery_level is not None and point.battery_level < threshold:
                warnings.append(point.timestamp)
        
        return warnings
    
    def save_workers(self, workers: List[Worker]):
        """Save worker list."""
        data = [w.to_dict() for w in workers]
        self.workers_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
    
    def load_workers(self) -> List[Worker]:
        """Load all workers."""
        if not self.workers_file.exists():
            return []
        
        try:
            data = json.loads(self.workers_file.read_text(encoding="utf-8"))
            return [Worker.from_dict(w) for w in data]
        except Exception:
            return []
    
    def save_geofences(self, geofences: List[FarmGeofence]):
        """Save geofence definitions."""
        data = [g.to_dict() for g in geofences]
        self.geofences_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
    
    def load_geofences(self) -> List[FarmGeofence]:
        """Load all geofences."""
        if not self.geofences_file.exists():
            return []
        
        try:
            data = json.loads(self.geofences_file.read_text(encoding="utf-8"))
            return [FarmGeofence.from_dict(g) for g in data]
        except Exception:
            return []
