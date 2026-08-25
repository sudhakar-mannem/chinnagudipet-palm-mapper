# 👷 Worker GPS Tracking System / కార్మికుల GPS ట్రాకింగ్ సిస్టమ్

## Overview / సంగ్రహావలోకనం

A continuous GPS tracking system designed specifically for oil-palm farm workers. Automatically detects farm entry/exit, tracks movement routes, identifies idle periods, and provides coverage analytics.

**ఆయిల్-పామ్ ఫార్మ్ కార్మికుల కోసం ప్రత్యేకంగా రూపొందించిన నిరంతర GPS ట్రాకింగ్ సిస్టమ్.** ఫార్మ్ ప్రవేశం/నిష్క్రమణను ఆటోమేటిక్‌గా గుర్తిస్తుంది, కదలిక రూట్‌లను ట్రాక్ చేస్తుంది, నిష్క్రియ కాలాలను గుర్తిస్తుంది మరియు కవరేజ్ విశ్లేషణలను అందిస్తుంది.

---

## Why This Approach? / ఈ విధానం ఎందుకు?

### Traditional Attendance Problems / సాంప్రదాయ హాజరు సమస్యలు

❌ Manual check-in/out - workers forget  
❌ No visibility into actual work coverage  
❌ Can't verify where workers spent time  
❌ No accountability for productivity  

### GPS Tracking Solution / GPS ట్రాకింగ్ పరిష్కారం

✅ **Automatic entry/exit** - no worker action needed  
✅ **Complete route history** - see where they worked  
✅ **Stop detection** - identify idle periods  
✅ **Coverage verification** - which plant zones visited  
✅ **Offline support** - works without mobile data  
✅ **Battery monitoring** - alerts when tracking stops  

---

## Key Features / ప్రధాన లక్షణాలు

### 1. Automatic Geofencing / ఆటోమేటిక్ జియోఫెన్సింగ్

- Define farm boundary (circular or polygon)
- Auto-detect when worker enters/exits
- Track first entry and last exit times
- Count entry/exit events

**ఫార్మ్ సరిహద్దును నిర్వచించండి** (వృత్తాకార లేదా బహుభుజం)  
**కార్మికుడు ప్రవేశించినప్పుడు/నిష్క్రమించినప్పుడు ఆటోమేటిక్‌గా గుర్తించండి**

### 2. Route Recording / రూట్ రికార్డింగ్

- GPS point every 1-5 minutes
- Complete movement history
- Distance covered calculation
- Time-stamped trail

**ప్రతి 1-5 నిమిషాలకు GPS పాయింట్**  
**పూర్తి కదలిక చరిత్ర**

### 3. Stop/Idle Detection / ఆగిన/నిష్క్రియ గుర్తింపు

- Automatically identify when worker stops
- Minimum duration filter (e.g., 5+ minutes)
- Location and duration of each stop
- Differentiate moving vs. idle time

**కార్మికుడు ఆగినప్పుడు ఆటోమేటిక్‌గా గుర్తించండి**  
**కనీస వ్యవధి ఫిల్టర్** (ఉదా., 5+ నిమిషాలు)

### 4. Historical Playback / చారిత్రక ప్లేబ్యాక్

- View any worker's route for any past date
- Animated route visualization
- Time markers along the path
- Entry/exit points highlighted

**ఏదైనా గత తేదీకి ఏదైనా కార్మికుడి రూట్‌ను చూడండి**  
**యానిమేటెడ్ రూట్ విజువలైజేషన్**

### 5. Plant Coverage Overlay / మొక్కల కవరేజ్ ఓవర్‌లే

- Shows palm plant locations on route map
- Color-coded by health status
- Identifies which plant zones were visited
- Verifies work coverage

**రూట్ మ్యాప్‌లో పామ్ మొక్కల స్థానాలను చూపిస్తుంది**  
**ఆరోగ్య స్థితి ద్వారా కలర్-కోడ్ చేయబడింది**

### 6. Battery & GPS Monitoring / బ్యాటరీ & GPS పర్యవేక్షణ

- Tracks phone battery level
- Detects GPS gaps (tracking stopped)
- Alerts for battery drain
- Identifies coverage issues

**ఫోన్ బ్యాటరీ స్థాయిని ట్రాక్ చేస్తుంది**  
**GPS అంతరాలను గుర్తిస్తుంది** (ట్రాకింగ్ ఆగిపోయింది)

---

## Setup Guide / సెటప్ మార్గదర్శి

### Step 1: Configure Workers / కార్మికులను కాన్ఫిగర్ చేయండి

1. Open Streamlit app: `streamlit run app.py`
2. Go to "⚙️ Tracking Setup" page
3. Click "Workers / కార్మికులు" tab
4. Add each worker:
   - **Worker ID**: W001, W002, etc.
   - **Name**: రామయ్య, కృష్ణయ్య, etc.
   - **Phone**: +91 9876543210
   - **Notes**: Experience, role, etc.

### Step 2: Define Farm Geofence / ఫార్మ్ జియోఫెన్స్‌ను నిర్వచించండి

1. Go to "Geofence / జియోఫెన్స్" tab
2. Enter farm details:
   - **Farm Name**: Your farm name
   - **Center Latitude**: e.g., 16.801234
   - **Center Longitude**: e.g., 80.501234
   - **Radius**: e.g., 400 meters

**Advanced:** For precise boundaries, provide polygon vertices:
```
16.801,80.501
16.802,80.502
16.803,80.500
16.801,80.501
```

3. Preview the geofence on map
4. Click "Save Geofence"

### Step 3: Setup Mobile GPS Tracking / మొబైల్ GPS ట్రాకింగ్ సెటప్

#### Option A: Use GPSLogger Android App (Recommended)

1. Install **GPSLogger** from Google Play Store
2. Configure settings:
   - **Logging interval**: 3 minutes
   - **Distance filter**: 5 meters
   - **File format**: JSON
   - **Auto-start**: Enabled
   - **Keep awake**: Disabled (save battery)

3. Worker workflow:
   - Open GPSLogger app
   - Press **Start** button
   - Keep phone in pocket while working
   - Press **Stop** at end of day
   - Export → Share → JSON file

#### Option B: Use Custom Web Tracker

1. Go to "📱 Mobile App" tab in Tracking Setup
2. Download "Mobile GPS Tracker (HTML)"
3. Send file to worker's phone (WhatsApp/Telegram)
4. Worker opens file in mobile browser
5. Clicks "Start Tracking"
6. At end of day: "Stop" → "Download Data"

### Step 4: Upload GPS Data / GPS డేటా అప్‌లోడ్ చేయండి

#### Daily Workflow:

1. Worker connects to WiFi at end of day
2. Exports GPS tracking file (JSON format)
3. Sends file via:
   - WhatsApp to supervisor
   - Direct upload in app
   - Telegram/Email

4. Supervisor uploads in app:
   - Go to "👷 Worker Tracking" page
   - Select worker and date
   - Click "Upload GPS Data"
   - Choose JSON file
   - Click "Process and Save"

5. View route and analytics immediately!

---

## Daily Screen View / దైనిక స్క్రీన్ వ్యూ

For each worker on each date, you see:

```
Worker: రామయ్య (Ramayya) - W001
Date: 15 January 2024

📊 Summary:
├─ First Entry: 07:42 AM
├─ Last Exit: 16:58 PM
├─ Time in Farm: 8h 32m
├─ Distance Covered: 4.2 km
└─ Stops Detected: 7

🗺️ Route Map:
[Interactive map showing:]
- Entry point (green marker)
- GPS trail (blue animated line)
- Stop locations (orange circles)
- Exit point (red marker)
- Palm plants (colored dots)
- Time markers every 30 minutes

⏸️ Stop Details:
1. 08:15 - 08:42 (27 min) - 16.8012, 80.5023
2. 09:30 - 09:48 (18 min) - 16.8015, 80.5019
3. ...

⚠️ Issues:
- GPS gap: 11:23 - 11:45 (22 min)
- Battery low warning: 15:30 (18%)

🌴 Plant Coverage:
Visited 42 plant zones
```

---

## Data Format / డేటా ఫార్మాట్

### GPS JSON Format

Workers' mobile app should export this format:

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
    "bearing": 45.0,
    "gps_enabled": true,
    "source": "mobile"
  },
  ...
]
```

**Required fields:**
- `latitude` (number)
- `longitude` (number)
- `timestamp` (ISO 8601 string)

**Optional but recommended:**
- `accuracy` - GPS accuracy in meters
- `battery_level` - Battery percentage (0-100)
- `altitude` - Elevation in meters
- `speed` - Movement speed in m/s
- `bearing` - Direction in degrees

---

## Offline Support / ఆఫ్‌లైన్ మద్దతు

### Why Offline Matters

Farm areas often have poor mobile coverage. Workers can't rely on real-time cloud sync.

### How It Works

1. **Mobile app stores GPS data locally** on phone
   - No internet required during tracking
   - Data saved in phone storage

2. **At end of day**, worker:
   - Connects to WiFi (home/farm office)
   - Exports GPS file
   - Sends to supervisor

3. **Supervisor uploads** to Palm Mapper app
   - Processes route analysis
   - Stores permanently
   - Available for historical viewing

### Battery Optimization

- Track every 2-5 minutes (not continuous)
- Disable during lunch break
- Use power bank if needed
- Typical battery usage: ~10-15% for 8-hour day

---

## Analytics & Reports / విశ్లేషణలు & నివేదికలు

### Available Metrics

**Time Tracking:**
- First entry time
- Last exit time  
- Total time in farm
- Time moving vs. stopped
- Break durations

**Movement:**
- Total distance covered
- Average speed
- Route efficiency
- Stop locations and durations

**Coverage:**
- Plant zones visited
- Work area coverage
- Revisited locations

**Reliability:**
- GPS gap detection
- Battery drain patterns
- Tracking consistency

---

## Troubleshooting / సమస్యా పరిష్కారం

### Problem: No GPS data uploading

**Causes:**
- GPS not enabled on phone
- App permission denied
- Phone in airplane mode

**Solution:**
- Enable Location Services
- Grant GPS permission to app
- Ensure mobile data/WiFi on (for initial GPS lock)

### Problem: GPS gaps in route

**Causes:**
- Phone went to sleep
- App closed by system
- Battery saver killed app

**Solution:**
- Disable battery optimization for GPS app
- Keep app in foreground
- Use "Keep awake" setting

### Problem: Inaccurate entry/exit times

**Causes:**
- Geofence radius too small/large
- GPS accuracy issues
- Worker lingering near boundary

**Solution:**
- Adjust geofence radius
- Use polygon geofence for precision
- Filter entry/exit events (min 2-minute inside)

### Problem: Too many stops detected

**Causes:**
- Stop detection too sensitive
- Worker taking frequent short breaks

**Solution:**
- Increase minimum stop duration (e.g., 5 → 10 minutes)
- Increase stop radius (e.g., 15 → 25 meters)
- Adjust in Tracking Setup page

---

## Technical Details / సాంకేతిక వివరాలు

### Architecture

```
Mobile Phone (Worker)
    ↓ GPS Tracking App
    ↓ Local Storage (JSON)
    ↓ Export at End of Day
    ↓
Supervisor Upload
    ↓ Palm Mapper App
    ↓ Route Analysis Engine
    ↓ Geofence Detection
    ↓ Stop/Idle Detection
    ↓ Coverage Calculation
    ↓
Storage & Visualization
    ↓ JSON Files (per worker per day)
    ↓ Interactive Map Display
```

### Data Storage

```
cache/worker_tracking/
├── workers.json              # Worker profiles
├── geofences.json            # Farm boundaries
└── routes/
    ├── W001_2024-01-15.json  # Worker 1, Jan 15
    ├── W001_2024-01-16.json
    ├── W002_2024-01-15.json  # Worker 2, Jan 15
    └── ...
```

### Algorithms

**Stop Detection:**
1. Group consecutive GPS points
2. Calculate centroid of group
3. Check if all points within radius (default 15m)
4. Check if duration exceeds minimum (default 5 min)
5. Mark as stop if both conditions met

**Geofence Detection:**
1. Check each GPS point against boundary
2. Detect state changes (inside → outside, vice versa)
3. Record entry/exit timestamps
4. Calculate time spent inside

**Coverage Calculation:**
1. For each GPS point
2. Find palm plants within proximity (default 10m)
3. Mark plant zone as "visited"
4. Generate coverage report

---

## Demo & Testing / డెమో & పరీక్ష

### Generate Sample Data

```bash
python generate_demo_tracking_data.py
```

This creates:
- 2 demo workers (రామయ్య, కృష్ణయ్య)
- Farm geofence (400m radius)
- 7 days of realistic route data
- Sample GPS JSON file for testing

### View Demo Data

1. Run: `streamlit run app.py`
2. Go to "👷 Worker Tracking" page
3. Select worker and date
4. Explore route visualization

---

## Best Practices / ఉత్తమ పద్ధతులు

### For Workers / కార్మికుల కోసం

✅ Start GPS tracking when entering farm  
✅ Keep phone in pocket (don't need to look at it)  
✅ Charge phone overnight  
✅ Stop tracking when leaving farm  
✅ Export and send data daily  

### For Supervisors / సూపర్‌వైజర్ల కోసం

✅ Review routes daily  
✅ Identify coverage gaps  
✅ Recognize efficient workers  
✅ Address tracking issues promptly  
✅ Maintain worker privacy (don't share unnecessarily)  

### Privacy Considerations

- GPS tracking only during work hours
- Data used for farm management, not surveillance
- Workers aware of tracking system
- Access limited to farm management
- Historical data retained for work records

---

## FAQ / తరచుగా అడిగే ప్రశ్నలు

**Q: Does this drain phone battery quickly?**  
A: No. With 3-5 minute tracking intervals, typical usage is 10-15% battery for 8 hours.

**Q: What if there's no mobile signal?**  
A: GPS works without mobile data. Data is stored locally and uploaded later via WiFi.

**Q: Can workers fake their location?**  
A: Technical users could, but:
- GPS accuracy patterns are hard to fake
- Movement speed/patterns look unnatural
- Battery drain inconsistent with fake apps
- Trust-based system works best for small teams

**Q: How much storage does tracking data use?**  
A: About 200-500 KB per worker per day. Very minimal.

**Q: Can I export routes to Google Earth?**  
A: Feature planned for future. Currently view in web app only.

**Q: What about multiple farms?**  
A: Define separate geofences for each farm. Routes auto-detect which farm.

---

## Future Enhancements / భవిష్యత్ మెరుగుదలలు

Planned features:

- [ ] KML/KMZ export for Google Earth
- [ ] WhatsApp bot for GPS data submission
- [ ] Weekly/monthly summary reports
- [ ] Worker productivity scoring
- [ ] Real-time tracking dashboard
- [ ] Mobile app (native Android/iOS)
- [ ] Voice notes at stop locations
- [ ] Photo capture integration
- [ ] Offline-first mobile PWA

---

## Support / మద్దతు

For questions or issues:

- **Documentation**: This file
- **Demo data**: Run `generate_demo_tracking_data.py`
- **Setup guide**: See "⚙️ Tracking Setup" page in app
- **Issues**: Report on GitHub

---

**Built with ❤️ for oil-palm farm management**  
**ఆయిల్-పామ్ ఫార్మ్ నిర్వహణ కోసం ❤️తో నిర్మించబడింది**
