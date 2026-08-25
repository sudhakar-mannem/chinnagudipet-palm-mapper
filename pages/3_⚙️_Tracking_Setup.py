"""Setup page for worker tracking - configure workers, geofences, and GPS settings."""
from __future__ import annotations

import sys
from pathlib import Path

import folium
import streamlit as st
from streamlit_folium import st_folium

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import CACHE_DIR, ensure_dirs  # noqa: E402
from services.worker_tracking import FarmGeofence, Worker, WorkerTrackingService  # noqa: E402

st.set_page_config(
    page_title="Tracking Setup - Palm Mapper",
    page_icon="⚙️",
    layout="wide",
)

# Initialize service
ensure_dirs()
TRACKING_DIR = CACHE_DIR / "worker_tracking"
tracking_service = WorkerTrackingService(TRACKING_DIR)


def main():
    st.title("⚙️ Worker Tracking Setup / కార్మికుల ట్రాకింగ్ సెటప్")
    
    tabs = st.tabs(["👷 Workers / కార్మికులు", "🗺️ Geofence / జియోఫెన్స్", "📱 Mobile App"])
    
    with tabs[0]:
        show_workers_tab()
    
    with tabs[1]:
        show_geofence_tab()
    
    with tabs[2]:
        show_mobile_app_tab()


def show_workers_tab():
    """Manage workers."""
    st.subheader("Worker Management / కార్మికుల నిర్వహణ")
    
    workers = tracking_service.load_workers()
    
    # Add new worker
    st.markdown("### Add New Worker / కొత్త కార్మికుడిని జోడించండి")
    
    with st.form("add_worker"):
        col1, col2 = st.columns(2)
        
        with col1:
            worker_id = st.text_input(
                "Worker ID *",
                placeholder="W001",
                help="Unique identifier for worker",
            )
            worker_name = st.text_input(
                "Name / పేరు *",
                placeholder="రాము",
            )
        
        with col2:
            worker_phone = st.text_input(
                "Phone / ఫోన్",
                placeholder="+91 9876543210",
            )
            worker_notes = st.text_area(
                "Notes / గమనికలు",
                placeholder="Any additional information",
            )
        
        submitted = st.form_submit_button("➕ Add Worker / జోడించండి")
        
        if submitted:
            if not worker_id or not worker_name:
                st.error("Worker ID and Name are required")
            elif any(w.worker_id == worker_id for w in workers):
                st.error(f"Worker ID '{worker_id}' already exists")
            else:
                from datetime import datetime
                
                worker = Worker(
                    worker_id=worker_id,
                    name=worker_name,
                    phone=worker_phone if worker_phone else None,
                    active=True,
                    start_date=datetime.now().strftime("%Y-%m-%d"),
                    notes=worker_notes,
                )
                workers.append(worker)
                tracking_service.save_workers(workers)
                st.success(f"✅ Worker '{worker_name}' added successfully!")
                st.rerun()
    
    # Display existing workers
    if workers:
        st.markdown("### Existing Workers / ఉన్న కార్మికులు")
        
        for worker in workers:
            with st.expander(f"{'✅' if worker.active else '❌'} {worker.name} ({worker.worker_id})"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**Phone / ఫోన్:** {worker.phone or '—'}")
                    st.write(f"**Start Date:** {worker.start_date or '—'}")
                    st.write(f"**Status:** {'Active / సక్రియం' if worker.active else 'Inactive / క్రియారహితం'}")
                    if worker.notes:
                        st.write(f"**Notes:** {worker.notes}")
                
                with col2:
                    if worker.active:
                        if st.button("Deactivate", key=f"deactivate_{worker.worker_id}"):
                            worker.active = False
                            tracking_service.save_workers(workers)
                            st.rerun()
                    else:
                        if st.button("Activate", key=f"activate_{worker.worker_id}"):
                            worker.active = True
                            tracking_service.save_workers(workers)
                            st.rerun()
                    
                    if st.button("🗑️ Delete", key=f"delete_{worker.worker_id}"):
                        workers = [w for w in workers if w.worker_id != worker.worker_id]
                        tracking_service.save_workers(workers)
                        st.success(f"Worker {worker.name} deleted")
                        st.rerun()
    else:
        st.info("No workers configured yet. Add your first worker above.")


def show_geofence_tab():
    """Configure farm geofence."""
    st.subheader("Farm Geofence Configuration / ఫార్మ్ జియోఫెన్స్ కాన్ఫిగరేషన్")
    
    st.markdown("""
    The geofence defines the farm boundary for automatic worker entry/exit detection.
    
    **జియోఫెన్స్ ఫార్మ్ సరిహద్దును నిర్వచిస్తుంది, ఆటోమేటిక్ కార్మికుల ప్రవేశం/నిష్క్రమణ గుర్తింపు కోసం.**
    """)
    
    geofences = tracking_service.load_geofences()
    default_geofence = geofences[0] if geofences else None
    
    # Configure geofence
    st.markdown("### Configure Farm Boundary / ఫార్మ్ సరిహద్దును కాన్ఫిగర్ చేయండి")
    
    with st.form("geofence_form"):
        farm_name = st.text_input(
            "Farm Name / ఫార్మ్ పేరు",
            value=default_geofence.name if default_geofence else "Chinnagudipet Palm Farm",
        )
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            center_lat = st.number_input(
                "Center Latitude / కేంద్ర అక్షాంశం",
                value=float(default_geofence.center_latitude) if default_geofence else 16.8,
                format="%.6f",
                help="Farm center latitude coordinate",
            )
        
        with col2:
            center_lon = st.number_input(
                "Center Longitude / కేంద్ర రేఖాంశం",
                value=float(default_geofence.center_longitude) if default_geofence else 80.5,
                format="%.6f",
                help="Farm center longitude coordinate",
            )
        
        with col3:
            radius_m = st.number_input(
                "Radius (meters) / వ్యాసార్ధం (మీటర్లు)",
                value=float(default_geofence.radius_m) if default_geofence else 500.0,
                min_value=50.0,
                max_value=5000.0,
                step=50.0,
                help="Farm boundary radius in meters",
            )
        
        st.markdown("**Advanced: Polygon Vertices (optional)**")
        st.markdown("For precise boundaries, provide polygon coordinates (latitude, longitude pairs)")
        
        polygon_input = st.text_area(
            "Polygon Vertices / బహుభుజ శీర్షాలు",
            value="",
            placeholder="16.801,80.501\n16.802,80.502\n16.803,80.503\n...",
            help="One coordinate pair per line: latitude,longitude",
        )
        
        submitted = st.form_submit_button("💾 Save Geofence / జియోఫెన్స్ సేవ్ చేయండి")
        
        if submitted:
            # Parse polygon vertices if provided
            polygon_vertices = []
            if polygon_input.strip():
                for line in polygon_input.strip().split("\n"):
                    try:
                        lat, lon = map(float, line.strip().split(","))
                        polygon_vertices.append((lat, lon))
                    except ValueError:
                        st.warning(f"Invalid coordinate: {line}")
            
            geofence = FarmGeofence(
                name=farm_name,
                center_latitude=center_lat,
                center_longitude=center_lon,
                radius_m=radius_m,
                polygon_vertices=polygon_vertices,
            )
            
            tracking_service.save_geofences([geofence])
            st.success("✅ Geofence saved successfully!")
            st.rerun()
    
    # Preview geofence on map
    if default_geofence or center_lat:
        st.markdown("### Preview / ప్రివ్యూ")
        
        preview_geofence = default_geofence or FarmGeofence(
            name=farm_name,
            center_latitude=center_lat,
            center_longitude=center_lon,
            radius_m=radius_m,
        )
        
        m = folium.Map(
            location=[preview_geofence.center_latitude, preview_geofence.center_longitude],
            zoom_start=15,
        )
        
        if preview_geofence.polygon_vertices:
            folium.Polygon(
                locations=preview_geofence.polygon_vertices,
                color="green",
                weight=3,
                fill=True,
                fillColor="green",
                fillOpacity=0.2,
                popup=preview_geofence.name,
            ).add_to(m)
        else:
            folium.Circle(
                location=[preview_geofence.center_latitude, preview_geofence.center_longitude],
                radius=preview_geofence.radius_m,
                color="green",
                weight=3,
                fill=True,
                fillColor="green",
                fillOpacity=0.2,
                popup=preview_geofence.name,
            ).add_to(m)
        
        # Add center marker
        folium.Marker(
            location=[preview_geofence.center_latitude, preview_geofence.center_longitude],
            popup=f"{preview_geofence.name}<br>Center",
            icon=folium.Icon(color="green", icon="home", prefix="fa"),
        ).add_to(m)
        
        st_folium(m, width=800, height=500)


def show_mobile_app_tab():
    """Show mobile GPS tracking app instructions."""
    st.subheader("📱 Mobile GPS Tracking Setup")
    
    st.markdown("""
    ## GPS Data Collection Methods
    
    ### Method 1: Automated Android App (Recommended)
    
    **Apps for continuous GPS tracking:**
    
    1. **GPSLogger for Android** (Free, Open Source)
       - Download: [Google Play Store](https://play.google.com/store/apps/details?id=com.mendhak.gpslogger)
       - Settings:
         - Logging interval: 1-5 minutes
         - Distance filter: 5 meters
         - Export format: JSON or GPX
         - Auto-start on boot: ✅
         - Keep screen off: ✅
    
    2. **OsmAnd** (Free, offline maps)
       - Download: [Google Play Store](https://play.google.com/store/apps/details?id=net.osmand)
       - Enable trip recording
       - Export as GPX, convert to JSON
    
    3. **Geo Tracker** (Paid, advanced features)
       - Battery optimization
       - Geofence triggers
       - Auto-sync to cloud
    
    ### Method 2: Custom Web App (For this project)
    
    Create a simple web page workers can open in their mobile browser:
    
    ```html
    <!DOCTYPE html>
    <html>
    <head>
        <title>Palm Farm GPS Tracker</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
    </head>
    <body>
        <h1>🌴 GPS Tracker</h1>
        <div id="status">Starting...</div>
        <button onclick="startTracking()">Start Tracking</button>
        <button onclick="stopTracking()">Stop</button>
        <button onclick="downloadData()">Download Data</button>
        
        <script>
            let tracking = false;
            let points = [];
            let watchId = null;
            
            function startTracking() {
                if (navigator.geolocation) {
                    tracking = true;
                    watchId = navigator.geolocation.watchPosition(
                        (position) => {
                            const point = {
                                latitude: position.coords.latitude,
                                longitude: position.coords.longitude,
                                altitude: position.coords.altitude,
                                accuracy: position.coords.accuracy,
                                timestamp: new Date().toISOString(),
                                battery_level: navigator.getBattery ? null : null
                            };
                            points.push(point);
                            document.getElementById('status').innerText = 
                                `Tracking: ${points.length} points recorded`;
                        },
                        (error) => console.error(error),
                        {
                            enableHighAccuracy: true,
                            maximumAge: 0,
                            timeout: 60000
                        }
                    );
                }
            }
            
            function stopTracking() {
                if (watchId) {
                    navigator.geolocation.clearWatch(watchId);
                    tracking = false;
                    document.getElementById('status').innerText = 'Stopped';
                }
            }
            
            function downloadData() {
                const dataStr = JSON.stringify(points, null, 2);
                const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
                const exportFileDefaultName = `gps_${new Date().toISOString().split('T')[0]}.json`;
                
                const linkElement = document.createElement('a');
                linkElement.setAttribute('href', dataUri);
                linkElement.setAttribute('download', exportFileDefaultName);
                linkElement.click();
            }
        </script>
    </body>
    </html>
    ```
    
    ### JSON Format Expected
    
    ```json
    [
      {
        "latitude": 16.801234,
        "longitude": 80.501234,
        "altitude": 25.5,
        "accuracy": 10.0,
        "timestamp": "2024-01-15T07:45:00Z",
        "battery_level": 85.0,
        "speed": 1.2,
        "bearing": 45.0
      },
      ...
    ]
    ```
    
    ### Offline Sync Strategy
    
    Since farm mobile coverage is poor:
    
    1. **App stores GPS data locally** throughout the day
    2. **At end of day**, worker connects to WiFi
    3. **Upload via:**
       - Web interface (Worker Tracking page → Upload GPS Data)
       - WhatsApp/Telegram to farm manager
       - Auto-sync if internet available
    
    ### Battery Optimization Tips
    
    - Use 2-5 minute tracking intervals (not continuous)
    - Enable "battery saver" mode in GPS app
    - Disable background app restrictions for GPS logger
    - Provide power banks to workers
    - Track only during working hours (7 AM - 6 PM)
    
    ---
    
    ## తెలుగు సూచనలు / Telugu Instructions
    
    ### GPS యాప్ ఎలా ఉపయోగించాలి:
    
    1. **GPSLogger** యాప్ డౌన్‌లోడ్ చేయండి (Google Play Store నుండి)
    2. యాప్ open చేసి **Start** button నొక్కండి
    3. ఫార్మ్‌లో పని చేస్తున్నప్పుడు ఫోన్ మీ జేబులో ఉంచండి
    4. రోజు చివరలో **Stop** button నొక్కండి
    5. **Export → JSON** select చేసి file save చేయండి
    6. WiFi వచ్చినప్పుడు Palm Mapper యాప్‌లో upload చేయండి
    
    ### బ్యాటరీ ఆదా చేయడానికి:
    - ప్రతి 3-5 నిమిషాలకొకసారి GPS location record చేస్తుంది
    - రాత్రి tracking ఆపండి
    - Power bank ఉపయోగించండి
    """)
    
    # Create download link for the HTML tracker
    html_tracker = """<!DOCTYPE html>
<html>
<head>
    <title>🌴 Palm Farm GPS Tracker</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; max-width: 500px; margin: 0 auto; }
        button { padding: 15px 30px; margin: 10px 5px; font-size: 16px; border-radius: 5px; border: none; color: white; }
        .start { background-color: #22c55e; }
        .stop { background-color: #ef4444; }
        .download { background-color: #3b82f6; }
        #status { padding: 20px; margin: 20px 0; background: #f0f0f0; border-radius: 5px; font-size: 18px; }
        #info { margin-top: 20px; font-size: 14px; color: #666; }
    </style>
</head>
<body>
    <h1>🌴 Palm Farm GPS Tracker</h1>
    <div id="status">Press Start to begin tracking</div>
    <button class="start" onclick="startTracking()">▶️ Start Tracking</button>
    <button class="stop" onclick="stopTracking()">⏹️ Stop</button>
    <button class="download" onclick="downloadData()">💾 Download Data</button>
    <div id="info"></div>
    
    <script>
        let tracking = false;
        let points = [];
        let watchId = null;
        let startTime = null;
        
        function updateStatus() {
            const duration = startTime ? Math.floor((Date.now() - startTime) / 60000) : 0;
            document.getElementById('status').innerHTML = tracking
                ? `✅ Tracking Active<br>${points.length} points recorded<br>${duration} minutes`
                : `⏸️ Tracking Stopped<br>${points.length} points saved`;
        }
        
        function getBatteryLevel() {
            return navigator.getBattery ? navigator.getBattery().then(b => b.level * 100) : Promise.resolve(null);
        }
        
        function startTracking() {
            if (!navigator.geolocation) {
                alert('GPS not supported on this device');
                return;
            }
            
            tracking = true;
            startTime = Date.now();
            
            watchId = navigator.geolocation.watchPosition(
                async (position) => {
                    const battery = await getBatteryLevel();
                    const point = {
                        latitude: position.coords.latitude,
                        longitude: position.coords.longitude,
                        altitude: position.coords.altitude,
                        accuracy: position.coords.accuracy,
                        speed: position.coords.speed,
                        bearing: position.coords.heading,
                        timestamp: new Date().toISOString(),
                        battery_level: battery,
                        gps_enabled: true,
                        source: "mobile"
                    };
                    points.push(point);
                    updateStatus();
                    
                    // Auto-save to localStorage
                    localStorage.setItem('gps_tracking_backup', JSON.stringify(points));
                },
                (error) => {
                    document.getElementById('info').innerHTML = `⚠️ GPS Error: ${error.message}`;
                },
                {
                    enableHighAccuracy: true,
                    maximumAge: 0,
                    timeout: 60000
                }
            );
            
            updateStatus();
        }
        
        function stopTracking() {
            if (watchId) {
                navigator.geolocation.clearWatch(watchId);
                tracking = false;
                updateStatus();
            }
        }
        
        function downloadData() {
            if (points.length === 0) {
                alert('No data to download');
                return;
            }
            
            const date = new Date().toISOString().split('T')[0];
            const dataStr = JSON.stringify(points, null, 2);
            const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
            const exportFileDefaultName = `gps_tracking_${date}.json`;
            
            const linkElement = document.createElement('a');
            linkElement.setAttribute('href', dataUri);
            linkElement.setAttribute('download', exportFileDefaultName);
            linkElement.click();
            
            document.getElementById('info').innerHTML = `✅ Downloaded ${points.length} points as ${exportFileDefaultName}`;
        }
        
        // Restore from backup on load
        const backup = localStorage.getItem('gps_tracking_backup');
        if (backup) {
            try {
                points = JSON.parse(backup);
                updateStatus();
            } catch (e) {}
        }
        
        // Periodic status update
        setInterval(updateStatus, 5000);
    </script>
</body>
</html>"""
    
    st.download_button(
        label="📥 Download Mobile GPS Tracker (HTML)",
        data=html_tracker,
        file_name="palm_farm_gps_tracker.html",
        mime="text/html",
        help="Download and open this file on worker's mobile phone",
    )


if __name__ == "__main__":
    main()
