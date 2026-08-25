"""Worker GPS Tracking - Route history and farm coverage."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

import folium
import pandas as pd
import streamlit as st
from folium import plugins
from streamlit_folium import st_folium

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import CACHE_DIR, ensure_dirs  # noqa: E402
from services.models import PlantObservation  # noqa: E402
from services.pipeline import load_state  # noqa: E402
from services.worker_tracking import (  # noqa: E402
    FarmGeofence,
    GPSPoint,
    RouteAnalyzer,
    Worker,
    WorkerRoute,
    WorkerTrackingService,
)

st.set_page_config(
    page_title="Worker Tracking - Palm Mapper",
    page_icon="👷",
    layout="wide",
)

# Telugu/English translations
TRANSLATIONS = {
    "page_title": {"en": "👷 Worker Tracking", "te": "👷 కార్మికుల ట్రాకింగ్"},
    "description": {
        "en": "Continuous GPS route tracking for farm workers with automatic geofence detection",
        "te": "ఫార్మ్ కార్మికుల కోసం ఆటోమేటిక్ జియోఫెన్స్ డిటెక్షన్‌తో నిరంతర GPS రూట్ ట్రాకింగ్",
    },
    "worker_selection": {"en": "Select Worker", "te": "కార్మికుడిని ఎంచుకోండి"},
    "date_selection": {"en": "Select Date", "te": "తేదీని ఎంచుకోండి"},
    "route_summary": {"en": "Route Summary", "te": "రూట్ సారాంశం"},
    "first_entry": {"en": "First Entry", "te": "మొదటి ప్రవేశం"},
    "last_exit": {"en": "Last Exit", "te": "చివరి నిష్క్రమణ"},
    "time_in_farm": {"en": "Time in Farm", "te": "ఫార్మ్‌లో సమయం"},
    "distance_covered": {"en": "Distance Covered", "te": "దూరం ప్రయాణించారు"},
    "stops_detected": {"en": "Stops Detected", "te": "ఆగిన చోట్లు"},
    "route_map": {"en": "Route Map", "te": "రూట్ మ్యాప్"},
    "stops_detail": {"en": "Stop Details", "te": "ఆగిన వివరాలు"},
    "gps_issues": {"en": "GPS/Battery Issues", "te": "GPS/బ్యాటరీ సమస్యలు"},
    "coverage": {"en": "Plant Coverage", "te": "మొక్కల కవరేజ్"},
    "setup_workers": {"en": "Setup Workers", "te": "కార్మికులను సెటప్ చేయండి"},
    "setup_geofence": {"en": "Setup Geofence", "te": "జియోఫెన్స్ సెటప్ చేయండి"},
    "upload_gps": {"en": "Upload GPS Data", "te": "GPS డేటా అప్‌లోడ్ చేయండి"},
}

# Language preference
LANG = "te"  # Can be made configurable


def t(key: str) -> str:
    """Translate key to current language."""
    return TRANSLATIONS.get(key, {}).get(LANG, key)


# Initialize service
ensure_dirs()
TRACKING_DIR = CACHE_DIR / "worker_tracking"
tracking_service = WorkerTrackingService(TRACKING_DIR)


def format_time(iso_time: Optional[str]) -> str:
    """Format ISO timestamp to readable time."""
    if not iso_time:
        return "—"
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


def build_route_map(
    route: WorkerRoute,
    geofence: Optional[FarmGeofence] = None,
    plant_observations: Optional[List[PlantObservation]] = None,
) -> folium.Map:
    """Build interactive map with route, stops, and geofence."""
    if not route.points:
        # Default center
        center = [16.8, 80.5]
        m = folium.Map(location=center, zoom_start=15)
        return m
    
    # Calculate center from route points
    lats = [p.latitude for p in route.points]
    lons = [p.longitude for p in route.points]
    center = [sum(lats) / len(lats), sum(lons) / len(lons)]
    
    m = folium.Map(location=center, zoom_start=15)
    
    # Draw geofence if available
    if geofence:
        if geofence.polygon_vertices:
            # Draw polygon
            folium.Polygon(
                locations=geofence.polygon_vertices,
                color="green",
                weight=2,
                fill=True,
                fillColor="green",
                fillOpacity=0.1,
                popup=f"Farm: {geofence.name}",
            ).add_to(m)
        else:
            # Draw circle
            folium.Circle(
                location=[geofence.center_latitude, geofence.center_longitude],
                radius=geofence.radius_m,
                color="green",
                weight=2,
                fill=True,
                fillColor="green",
                fillOpacity=0.1,
                popup=f"Farm: {geofence.name}",
            ).add_to(m)
    
    # Draw plant locations as background
    if plant_observations:
        for obs in plant_observations[:500]:  # Limit for performance
            if obs.latitude and obs.longitude:
                color_map = {
                    "green": "#22c55e",
                    "amber": "#f59e0b",
                    "red": "#ef4444",
                    "white": "#9ca3af",
                }
                color = color_map.get(obs.health, "#9ca3af")
                
                folium.CircleMarker(
                    location=[obs.latitude, obs.longitude],
                    radius=3,
                    color=color,
                    fill=True,
                    fillColor=color,
                    fillOpacity=0.3,
                    weight=1,
                    popup=f"Plant: {obs.plant_id}<br>Health: {obs.health}",
                ).add_to(m)
    
    # Draw route line
    if len(route.points) > 1:
        route_coords = [[p.latitude, p.longitude] for p in route.points]
        folium.PolyLine(
            route_coords,
            color="blue",
            weight=3,
            opacity=0.7,
            popup=f"{route.worker_name} - {route.date}",
        ).add_to(m)
        
        # Add route animation (if available)
        plugins.AntPath(
            route_coords,
            color="blue",
            weight=3,
            opacity=0.6,
            delay=1000,
        ).add_to(m)
    
    # Mark entry/exit points
    if route.first_entry_time and route.points:
        entry_point = next(
            (p for p in route.points if p.timestamp == route.first_entry_time), None
        )
        if entry_point:
            folium.Marker(
                location=[entry_point.latitude, entry_point.longitude],
                popup=f"Entry: {format_time(route.first_entry_time)}",
                icon=folium.Icon(color="green", icon="arrow-right", prefix="fa"),
            ).add_to(m)
    
    if route.last_exit_time and route.points:
        exit_point = next(
            (p for p in route.points if p.timestamp == route.last_exit_time), None
        )
        if exit_point:
            folium.Marker(
                location=[exit_point.latitude, exit_point.longitude],
                popup=f"Exit: {format_time(route.last_exit_time)}",
                icon=folium.Icon(color="red", icon="arrow-left", prefix="fa"),
            ).add_to(m)
    
    # Draw stops
    for i, stop in enumerate(route.stops, 1):
        folium.CircleMarker(
            location=[stop.latitude, stop.longitude],
            radius=10,
            color="orange",
            fill=True,
            fillColor="orange",
            fillOpacity=0.6,
            popup=f"Stop #{i}<br>"
            f"Duration: {format_duration(stop.duration_minutes)}<br>"
            f"Time: {format_time(stop.start_time)} - {format_time(stop.end_time)}",
        ).add_to(m)
        
        # Draw stop radius
        folium.Circle(
            location=[stop.latitude, stop.longitude],
            radius=stop.radius_m,
            color="orange",
            weight=1,
            fill=False,
            opacity=0.3,
        ).add_to(m)
    
    # Add time markers along route (every 30 minutes)
    if len(route.points) > 10:
        time_interval_minutes = 30
        last_marker_time = None
        
        for point in route.points:
            try:
                pt = datetime.fromisoformat(point.timestamp.replace("Z", "+00:00"))
                
                if last_marker_time is None or (pt - last_marker_time).total_seconds() >= time_interval_minutes * 60:
                    folium.CircleMarker(
                        location=[point.latitude, point.longitude],
                        radius=4,
                        color="white",
                        fill=True,
                        fillColor="blue",
                        fillOpacity=0.8,
                        weight=2,
                        popup=format_time(point.timestamp),
                    ).add_to(m)
                    last_marker_time = pt
            except (ValueError, AttributeError):
                pass
    
    return m


def main():
    st.title(t("page_title"))
    st.markdown(t("description"))
    
    # Load workers
    workers = tracking_service.load_workers()
    if not workers:
        st.warning("No workers configured. Please setup workers first.")
        with st.expander(t("setup_workers")):
            show_worker_setup()
        return
    
    # Load geofences
    geofences = tracking_service.load_geofences()
    default_geofence = geofences[0] if geofences else None
    
    # Worker and date selection
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        worker_options = {f"{w.name} ({w.worker_id})": w.worker_id for w in workers if w.active}
        if not worker_options:
            st.error("No active workers found")
            return
        
        selected_worker_display = st.selectbox(
            t("worker_selection"),
            options=list(worker_options.keys()),
        )
        selected_worker_id = worker_options[selected_worker_display]
    
    with col2:
        # Get available dates for this worker
        available_dates = tracking_service.list_worker_routes(selected_worker_id)
        
        if available_dates:
            selected_date = st.selectbox(
                t("date_selection"),
                options=available_dates,
                format_func=lambda d: datetime.strptime(d, "%Y-%m-%d").strftime("%d %B %Y"),
            )
        else:
            # Default to today
            selected_date = datetime.now().strftime("%Y-%m-%d")
            st.info(f"No routes found. Showing {selected_date}")
    
    with col3:
        if st.button("🔄 Refresh"):
            st.rerun()
    
    # Load route data
    route = tracking_service.load_route(selected_worker_id, selected_date)
    
    if route is None or not route.points:
        st.warning(f"No GPS data available for {selected_date}")
        
        # Show upload interface
        with st.expander(t("upload_gps"), expanded=True):
            show_gps_upload(selected_worker_id, selected_date)
        return
    
    # Display route summary
    st.subheader(t("route_summary"))
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            t("first_entry"),
            format_time(route.first_entry_time) if route.first_entry_time else "—",
        )
    
    with col2:
        st.metric(
            t("last_exit"),
            format_time(route.last_exit_time) if route.last_exit_time else "—",
        )
    
    with col3:
        st.metric(
            t("time_in_farm"),
            format_duration(route.time_inside_farm_minutes),
        )
    
    with col4:
        st.metric(
            t("distance_covered"),
            f"{route.total_distance_km:.2f} km",
        )
    
    with col5:
        st.metric(
            t("stops_detected"),
            len(route.stops),
        )
    
    # Load plant observations for overlay
    state = load_state()
    plant_observations = state.get("observations", [])
    plant_obs_objects = [PlantObservation.from_dict(o) for o in plant_observations] if plant_observations else []
    
    # Display map
    st.subheader(t("route_map"))
    route_map = build_route_map(route, default_geofence, plant_obs_objects)
    st_folium(route_map, width=1200, height=600)
    
    # Display stops details
    if route.stops:
        st.subheader(t("stops_detail"))
        
        stops_data = []
        for i, stop in enumerate(route.stops, 1):
            stops_data.append({
                "#": i,
                "Start Time / ప్రారంభ సమయం": format_time(stop.start_time),
                "End Time / ముగింపు సమయం": format_time(stop.end_time),
                "Duration / వ్యవధి": format_duration(stop.duration_minutes),
                "Location / స్థానం": f"{stop.latitude:.6f}, {stop.longitude:.6f}",
                "Radius / వ్యాసార్ధం": f"{stop.radius_m:.1f} m",
            })
        
        st.dataframe(pd.DataFrame(stops_data), use_container_width=True)
    
    # Display GPS/Battery issues
    if route.gps_off_periods or route.battery_low_warnings:
        st.subheader(t("gps_issues"))
        
        if route.gps_off_periods:
            st.warning(f"⚠️ GPS gaps detected: {len(route.gps_off_periods)} period(s)")
            for start, end in route.gps_off_periods:
                st.text(f"  • {format_time(start)} → {format_time(end)}")
        
        if route.battery_low_warnings:
            st.warning(f"🔋 Low battery warnings: {len(route.battery_low_warnings)} time(s)")
    
    # Display coverage
    if route.visited_plant_ids:
        st.subheader(t("coverage"))
        st.info(f"Visited {len(route.visited_plant_ids)} plant zones")
        if len(route.visited_plant_ids) <= 50:
            st.text(", ".join(route.visited_plant_ids))


def show_worker_setup():
    """Show worker setup interface."""
    st.markdown("### Add New Worker / కొత్త కార్మికుడిని జోడించండి")
    
    with st.form("worker_form"):
        worker_id = st.text_input("Worker ID", placeholder="W001")
        worker_name = st.text_input("Name / పేరు", placeholder="రాము")
        worker_phone = st.text_input("Phone / ఫోన్", placeholder="+91 9876543210")
        
        submitted = st.form_submit_button("Add Worker / జోడించండి")
        
        if submitted and worker_id and worker_name:
            workers = tracking_service.load_workers()
            
            # Check if worker_id already exists
            if any(w.worker_id == worker_id for w in workers):
                st.error(f"Worker ID {worker_id} already exists")
            else:
                worker = Worker(
                    worker_id=worker_id,
                    name=worker_name,
                    phone=worker_phone if worker_phone else None,
                    active=True,
                    start_date=datetime.now().strftime("%Y-%m-%d"),
                )
                workers.append(worker)
                tracking_service.save_workers(workers)
                st.success(f"Worker {worker_name} added successfully!")
                st.rerun()


def show_gps_upload(worker_id: str, date: str):
    """Show GPS data upload interface."""
    st.markdown("### Upload GPS Tracking Data")
    st.markdown("Upload a JSON file with GPS points from mobile tracking app")
    
    uploaded_file = st.file_uploader(
        "Choose GPS JSON file",
        type=["json"],
        help="Expected format: [{\"latitude\": 16.8, \"longitude\": 80.5, \"timestamp\": \"2024-01-01T10:00:00Z\", ...}]",
    )
    
    if uploaded_file:
        try:
            data = json.loads(uploaded_file.read())
            
            if not isinstance(data, list):
                st.error("Invalid format: Expected a JSON array")
                return
            
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
                    st.warning(f"Skipping invalid point: {e}")
            
            if not points:
                st.error("No valid GPS points found in file")
                return
            
            st.info(f"Found {len(points)} GPS points")
            
            # Get worker name
            workers = tracking_service.load_workers()
            worker = next((w for w in workers if w.worker_id == worker_id), None)
            worker_name = worker.name if worker else worker_id
            
            # Load geofence and plant data
            geofences = tracking_service.load_geofences()
            geofence = geofences[0] if geofences else None
            
            state = load_state()
            plant_observations = state.get("observations", [])
            plant_obs_objects = [PlantObservation.from_dict(o) for o in plant_observations] if plant_observations else []
            
            # Process and save
            if st.button("Process and Save"):
                with st.spinner("Processing route..."):
                    route = tracking_service.add_points_to_route(
                        worker_id=worker_id,
                        worker_name=worker_name,
                        date=date,
                        points=points,
                        analyzer=RouteAnalyzer(),
                        geofence=geofence,
                        plant_observations=plant_obs_objects,
                    )
                    
                    st.success(f"Route saved! {len(route.points)} points, {len(route.stops)} stops detected")
                    st.rerun()
        
        except json.JSONDecodeError:
            st.error("Invalid JSON file")
        except Exception as e:
            st.error(f"Error processing file: {e}")


if __name__ == "__main__":
    main()
