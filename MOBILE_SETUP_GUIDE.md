# 📱 Mobile GPS Tracking Setup Guide for Workers
## కార్మికుల ఫోన్లలో GPS ట్రాకింగ్ సెటప్ చేయడం

Complete step-by-step guide for setting up GPS tracking on workers' Android phones.

**పూర్తి దశల వారీ మార్గదర్శి కార్మికుల Android ఫోన్లలో GPS ట్రాకింగ్ సెటప్ చేయడానికి.**

---

## Quick Summary / త్వరిత సారాంశం

**Two options:**
1. **GPSLogger App** - Install once, use daily (recommended)
2. **Web Tracker** - No installation, open HTML file (simpler)

**రెండు ఎంపికలు:**
1. **GPSLogger యాప్** - ఒకసారి ఇన్‌స్టాల్ చేయండి, రోజూ ఉపయోగించండి (సిఫార్సు)
2. **వెబ్ ట్రాకర్** - ఇన్‌స్టాలేషన్ అవసరం లేదు, HTML ఫైల్ ఓపెన్ చేయండి (సులభం)

---

## Option 1: GPSLogger App (Recommended)

### Why GPSLogger?

✅ **Free** - No cost, no ads  
✅ **Battery efficient** - 10-15% for full day  
✅ **Reliable** - Works offline  
✅ **Popular** - 500,000+ downloads  
✅ **Simple** - One button to start/stop  

### Step 1: Installation / ఇన్‌స్టాలేషన్

**On worker's Android phone / కార్మికుడి Android ఫోన్‌లో:**

```
1. Open Play Store
   Play Store ఓపెన్ చేయండి

2. Search bar: Type "GPSLogger"
   సెర్చ్ బార్‌లో: "GPSLogger" టైప్ చేయండి

3. Find app by "mendhak" (green icon with location pin)
   "mendhak" చే యాప్ కనుగొనండి (ఆకుపచ్చ ఐకాన్ లొకేషన్ పిన్‌తో)

4. Tap "Install"
   "Install" నొక్కండి

5. Wait for installation (5-10 seconds)
   ఇన్‌స్టాలేషన్ కోసం వేచి ఉండండి (5-10 సెకన్లు)

6. Tap "Open"
   "Open" నొక్కండి
```

**Play Store Link:**  
https://play.google.com/store/apps/details?id=com.mendhak.gpslogger

### Step 2: First-Time Setup / మొదటిసారి సెటప్

**When you open GPSLogger for first time / మొదటిసారి GPSLogger ఓపెన్ చేసినప్పుడు:**

```
1. App asks for Location Permission
   యాప్ లొకేషన్ అనుమతి అడుగుతుంది
   
   → Tap "Allow" or "అనుమతించు"
   
2. Choose "Allow all the time" (recommended)
   "ఎల్లప్పుడూ అనుమతించు" ఎంచుకోండి (సిఫార్సు)
   
   Or "Allow only while using the app"
   లేదా "యాప్ ఉపయోగిస్తున్నప్పుడు మాత్రమే అనుమతించు"
```

### Step 3: Configure Settings / సెట్టింగ్స్ కాన్ఫిగర్ చేయండి

**Do this ONCE per worker / ప్రతి కార్మికుడికి ఒకసారి చేయండి:**

```
1. Open GPSLogger app
   GPSLogger యాప్ ఓపెన్ చేయండి

2. Tap Menu icon (☰) at top-left
   టాప్-లెఫ్ట్‌లో మెను ఐకాన్ (☰) నొక్కండి

3. Tap "Settings" or "సెట్టింగ్స్"
   "Settings" లేదా "సెట్టింగ్స్" నొక్కండి
```

**Now configure these settings / ఇప్పుడు ఈ సెట్టింగ్స్ కాన్ఫిగర్ చేయండి:**

#### Logging details / లాగింగ్ వివరాలు

```
⚙️ Logging details
   │
   ├─ Logging interval: 3 minutes
   │  (ప్రతి 3 నిమిషాలకొకసారి GPS record చేస్తుంది)
   │  How often to record GPS point
   │
   ├─ Distance before logging: 5 meters
   │  (5 మీటర్లు కదిలితేనే record చేస్తుంది)
   │  Only record if moved 5+ meters
   │
   ├─ Keep GPS on between fixes: OFF ❌
   │  (బ్యాటరీ సేవ్ చేయడానికి OFF చేయండి)
   │  Turn OFF to save battery
   │
   └─ Start on bootup: OFF ❌
      (ఫోన్ రీస్టార్ట్ అయినప్పుడు ఆటోమేటిక్ స్టార్ట్ అవదు)
      Optional: Turn ON if you want auto-start
```

#### Auto send and upload / ఆటో పంపడం మరియు అప్‌లోడ్

```
📤 Auto send and upload
   │
   └─ All options: OFF ❌
      (మాన్యువల్‌గా WhatsApp ద్వారా పంపడం మంచిది)
      Manual sending via WhatsApp is better
```

#### Logging preferences / లాగింగ్ ప్రాధాన్యతలు

```
📁 Logging preferences
   │
   ├─ Log to JSON: ON ✅ (IMPORTANT!)
   │  (JSON format అవసరం - ఇది తప్పనిసరి!)
   │
   ├─ Log to GPX: OFF ❌ (optional)
   ├─ Log to KML: OFF ❌ (optional)
   └─ Log to NMEA: OFF ❌ (optional)
```

#### Performance / పనితీరు

```
📍 Performance
   │
   ├─ Don't log if I'm not moving: OFF ❌
   │  (మేము ఆగినప్పుడు కూడా record కావాలి)
   │  We want to record even when stopped
   │
   └─ Time before stopping: 0 minutes
      (వెంటనే record చేయడం ప్రారంభించండి)
```

#### Battery / బ్యాటరీ

```
🔋 Battery
   │
   └─ Don't log if battery below: 15%
      (బ్యాటరీ 15% కంటే తక్కువగా ఉంటే ఆపివేస్తుంది)
      Stop tracking if battery drops below 15%
```

**Settings Done! / సెట్టింగ్స్ పూర్తయ్యాయి!**

### Step 4: Daily Usage by Workers / కార్మికులు రోజువారీ వినియోగం

#### Morning - Start Tracking / ఉదయం - ట్రాకింగ్ ప్రారంభించండి

```
07:00 AM - Before entering farm / ఫార్మ్‌లోకి వెళ్ళే ముందు

1. Open GPSLogger app
   GPSLogger యాప్ ఓపెన్ చేయండి
   
2. You see a big ▶ (Play) button
   మీకు పెద్ద ▶ (ప్లే) బటన్ కనిపిస్తుంది
   
3. Tap the ▶ button
   ▶ బటన్ నొక్కండి
   
4. Button turns GREEN ✅
   బటన్ ఆకుపచ్చగా మారుతుంది ✅
   
5. Screen shows: "Recording... 0 points"
   స్క్రీన్ చూపిస్తుంది: "Recording... 0 points"
   
6. Put phone in pocket and start work
   ఫోన్ జేబులో పెట్టుకుని పని ప్రారంభించండి
   
7. Don't need to look at phone again!
   మళ్ళీ ఫోన్ చూడాల్సిన అవసరం లేదు!
```

**What worker sees on screen / కార్మికుడు స్క్రీన్‌లో ఏం చూస్తాడు:**

```
▶ Recording...
  
📍 173 points
⏱️ 2h 45m
📊 3.2 km
🔋 87%

[Map showing your trail]
```

#### During Work / పని సమయంలో

```
✅ Phone can be in pocket
   ఫోన్ జేబులో ఉండవచ్చు
   
✅ Screen can be off (saves battery)
   స్క్రీన్ ఆఫ్ అవ్వవచ్చు (బ్యాటరీ సేవ్ అవుతుంది)
   
✅ App records in background
   యాప్ బ్యాక్‌గ్రౌండ్‌లో record చేస్తుంది
   
✅ No need to open app
   యాప్ ఓపెన్ చేయాల్సిన అవసరం లేదు
   
⚠️ Don't force-close the app
   యాప్‌ను ఫోర్స్-క్లోజ్ చేయవద్దు
```

#### Evening - Stop & Send / సాయంత్రం - ఆపండి & పంపండి

```
05:00 PM - End of work day / పని రోజు ముగిసినప్పుడు

1. Open GPSLogger app
   GPSLogger యాప్ ఓపెన్ చేయండి
   
2. Tap the ■ (Stop) button (now RED)
   ■ (స్టాప్) బటన్ (ఇప్పుడు ఎరుపు) నొక్కండి
   
3. Screen shows: "Not recording"
   స్క్రీన్ చూపిస్తుంది: "Not recording"
   
4. Tap Menu (☰) → Share → File
   మెను (☰) → Share → File నొక్కండి
   
5. Choose "JSON" file type
   "JSON" ఫైల్ రకం ఎంచుకోండి
   
6. Select today's file (e.g., 20260825.json)
   నేటి ఫైల్ ఎంచుకోండి (ఉదా., 20260825.json)
   
7. Choose "WhatsApp"
   "WhatsApp" ఎంచుకోండి
   
8. Send to supervisor's number
   సూపర్‌వైజర్ నంబర్‌కు పంపండి
   
9. Done! ✅
   పూర్తయింది! ✅
```

**File name will be / ఫైల్ పేరు ఇలా ఉంటుంది:**
```
gpslogger_20260825.json  (50-200 KB)
```

### Step 5: Battery Management / బ్యాటరీ నిర్వహణ

**To prevent phone from killing GPSLogger / ఫోన్ GPSLogger ను kill చేయకుండా నిరోధించడానికి:**

```
Phone Settings → Apps → GPSLogger
   │
   ├─ Battery: "Unrestricted" or "No restrictions"
   │  బ్యాటరీ: "అపరిమిత" లేదా "పరిమితులు లేవు"
   │
   ├─ Data usage: "Background data" ON
   │  డేటా వినియోగం: "బ్యాక్‌గ్రౌండ్ డేటా" ON
   │
   └─ Permissions: Location "Allow all the time"
      అనుమతులు: లొకేషన్ "ఎల్లప్పుడూ అనుమతించు"
```

**For specific phone brands / నిర్దిష్ట ఫోన్ బ్రాండ్ల కోసం:**

#### Xiaomi / Redmi
```
Settings → Apps → Manage apps → GPSLogger
   ├─ Autostart: ON ✅
   ├─ Battery saver: No restrictions
   └─ Other permissions: Location (Always)
```

#### Samsung
```
Settings → Apps → GPSLogger
   ├─ Battery: Unrestricted
   ├─ Background usage limits: OFF
   └─ Permissions: Location (Allow all the time)
```

#### Oppo / Realme
```
Settings → Apps → App Management → GPSLogger
   ├─ App Info → Permissions → Location: Always allow
   └─ Battery → Background freeze: Don't allow
```

---

## Option 2: Web Tracker (No Installation)

### Why Web Tracker?

✅ **No installation needed**  
✅ **Works on any Android phone**  
✅ **Simple** - Just open HTML file  
✅ **Good for testing**  
✅ **Easy to update** - Just send new file  

❌ Less battery-efficient than GPSLogger  
❌ Browser must stay open  
❌ May stop if phone sleeps  

### Step 1: Get HTML File / HTML ఫైల్ పొందండి

**You (supervisor) do this once / మీరు (సూపర్‌వైజర్) ఒకసారి చేయండి:**

```
1. Open Palm Mapper app on your computer
   మీ కంప్యూటర్‌లో Palm Mapper యాప్ ఓపెన్ చేయండి
   
2. Go to "⚙️ Tracking Setup" page
   "⚙️ Tracking Setup" పేజీకి వెళ్ళండి
   
3. Click "📱 Mobile App" tab
   "📱 Mobile App" ట్యాబ్ క్లిక్ చేయండి
   
4. Scroll down to "Download Mobile GPS Tracker (HTML)"
   "Download Mobile GPS Tracker (HTML)" కి క్రిందికి స్క్రోల్ చేయండి
   
5. Click download button
   డౌన్‌లోడ్ బటన్ క్లిక్ చేయండి
   
6. File saves: palm_farm_gps_tracker.html
   ఫైల్ సేవ్ అవుతుంది: palm_farm_gps_tracker.html
```

### Step 2: Send to Workers / కార్మికులకు పంపండి

**Via WhatsApp:**
```
1. Open WhatsApp on your phone
2. Open worker's chat
3. Tap "📎" (attach) icon
4. Choose "Document" or "ఫైల్"
5. Select "palm_farm_gps_tracker.html"
6. Send
```

**Via Bluetooth:**
```
1. Turn on Bluetooth on both phones
2. Pair phones
3. Send → Bluetooth → Select file
```

### Step 3: Worker Opens File / కార్మికుడు ఫైల్ ఓపెన్ చేస్తాడు

**On worker's phone / కార్మికుడి ఫోన్‌లో:**

```
1. Open "Files" or "File Manager" app
   "Files" లేదా "File Manager" యాప్ ఓపెన్ చేయండి
   
2. Go to "Downloads" folder
   "Downloads" ఫోల్డర్‌కి వెళ్ళండి
   
3. Find "palm_farm_gps_tracker.html"
   "palm_farm_gps_tracker.html" కనుగొనండి
   
4. Tap on it
   దానిపై నొక్కండి
   
5. Choose "Chrome" or any browser
   "Chrome" లేదా ఏదైనా బ్రౌజర్ ఎంచుకోండి
   
6. Browser asks "Allow location?"
   బ్రౌజర్ అడుగుతుంది "లొకేషన్ అనుమతించాలా?"
   
7. Tap "Allow" or "అనుమతించు"
   "Allow" లేదా "అనుమతించు" నొక్కండి
```

### Step 4: Daily Usage / రోజువారీ వినియోగం

#### Morning / ఉదయం

```
1. Open Chrome
   Chrome ఓపెన్ చేయండి
   
2. Open "palm_farm_gps_tracker.html" from Downloads
   Downloads నుండి "palm_farm_gps_tracker.html" ఓపెన్ చేయండి
   
3. Tap "▶️ Start Tracking" button (green)
   "▶️ Start Tracking" బటన్ (ఆకుపచ్చ) నొక్కండి
   
4. Screen shows:
   స్క్రీన్ చూపిస్తుంది:
   
   ✅ Tracking Active
   173 points recorded
   145 minutes
   
5. Keep browser open (don't close tab)
   బ్రౌజర్ ఓపెన్‌గా ఉంచండి (ట్యాబ్ మూసివేయవద్దు)
   
6. Lock phone and put in pocket
   ఫోన్ లాక్ చేసి జేబులో పెట్టుకోండి
```

#### Evening / సాయంత్రం

```
1. Open browser tab with tracker
   ట్రాకర్‌తో బ్రౌజర్ ట్యాబ్ ఓపెన్ చేయండి
   
2. Tap "⏹️ Stop" button (red)
   "⏹️ Stop" బటన్ (ఎరుపు) నొక్కండి
   
3. Tap "💾 Download Data" button (blue)
   "💾 Download Data" బటన్ (నీలం) నొక్కండి
   
4. File downloads to Downloads folder
   ఫైల్ Downloads ఫోల్డర్‌కు డౌన్‌లోడ్ అవుతుంది
   
   File name: gps_tracking_2026-08-25.json
   
5. Open WhatsApp
   WhatsApp ఓపెన్ చేయండి
   
6. Send file to supervisor
   సూపర్‌వైజర్‌కు ఫైల్ పంపండి
```

### Limitations of Web Tracker / వెబ్ ట్రాకర్ పరిమితులు

⚠️ **Browser must stay open**  
బ్రౌజర్ ఓపెన్‌గా ఉండాలి

⚠️ **May stop if phone locks for long time**  
ఫోన్ చాలా సమయం లాక్ అయితే ఆగవచ్చు

⚠️ **Uses more battery than GPSLogger**  
GPSLogger కంటే ఎక్కువ బ్యాటరీ ఉపయోగిస్తుంది

⚠️ **Data lost if browser closes unexpectedly**  
బ్రౌజర్ అనుకోకుండా మూసివేస్తే డేటా పోవచ్చు

**Solution:** Use GPSLogger app for reliable daily use!

---

## Comparison / పోలిక

| Feature | GPSLogger App | Web Tracker |
|---------|--------------|-------------|
| **Installation** | Need to install | No installation |
| **ఇన్‌స్టాలేషన్** | ఇన్‌స్టాల్ చేయాలి | ఇన్‌స్టాలేషన్ అవసరం లేదు |
| **Reliability** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **విశ్వసనీయత** | చాలా మంచిది | మధ్యస్థం |
| **Battery** | Efficient | More drain |
| **బ్యాటరీ** | సమర్థవంతమైనది | ఎక్కువ కరుగుతుంది |
| **Background** | Works in background | Browser must stay open |
| **బ్యాక్‌గ్రౌండ్** | బ్యాక్‌గ్రౌండ్‌లో పనిచేస్తుంది | బ్రౌజర్ ఓపెన్‌గా ఉండాలి |
| **Setup** | 5 minutes once | Instant |
| **సెటప్** | ఒకసారి 5 నిమిషాలు | తక్షణమే |
| **Best for** | Daily use | Testing/backup |
| **ఉత్తమం** | రోజువారీ వినియోగం | టెస్టింగ్/బ్యాకప్ |

---

## Troubleshooting / సమస్యా పరిష్కారం

### GPSLogger Issues

#### Problem: App doesn't record in background

**Solution:**
```
1. Phone Settings → Battery
2. Find "Battery optimization" or "App battery management"
3. Find GPSLogger
4. Set to "Don't optimize" or "Unrestricted"
```

**తెలుగులో:**
```
1. ఫోన్ సెట్టింగ్స్ → బ్యాటరీ
2. "బ్యాటరీ ఆప్టిమైజేషన్" కనుగొనండి
3. GPSLogger కనుగొనండి
4. "ఆప్టిమైజ్ చేయవద్దు" సెట్ చేయండి
```

#### Problem: GPS accuracy is poor

**Solution:**
```
1. Go outside (GPS doesn't work well indoors)
2. Wait 1-2 minutes for GPS to lock
3. Check "High accuracy" mode in Location settings
```

#### Problem: File is too large to send on WhatsApp

**WhatsApp limit: 100 MB (GPS files are only 50-200 KB, so this shouldn't happen)**

If it does:
```
1. Check file size in File Manager
2. Normal size: 50-200 KB ✅
3. If larger: Settings → Logging interval → Increase to 5 minutes
```

### Web Tracker Issues

#### Problem: Tracking stops when phone locks

**Solution:**
```
1. Keep screen on (not ideal for battery)
2. Or use GPSLogger app instead (recommended)
```

#### Problem: Browser closes and data lost

**Solution:**
```
Web tracker has auto-backup to localStorage
When you reopen, it may recover data

But for reliability: Use GPSLogger app
```

---

## Data Privacy / డేటా గోప్యత

**Important information for workers / కార్మికుల కోసం ముఖ్యమైన సమాచారం:**

✅ **Tracking only during work hours**  
ట్రాకింగ్ పని గంటల్లో మాత్రమే

✅ **Worker controls start/stop**  
కార్మికుడు ప్రారంభం/ఆపు నియంత్రించగలడు

✅ **Data used for farm management only**  
డేటా ఫార్మ్ నిర్వహణ కోసం మాత్రమే ఉపయోగించబడుతుంది

✅ **GPS stays on phone until worker sends it**  
GPS కార్మికుడు పంపే వరకు ఫోన్‌లోనే ఉంటుంది

✅ **Can view own routes in app**  
యాప్‌లో స్వంత రూట్లను చూడవచ్చు

---

## FAQ / తరచుగా అడిగే ప్రశ్నలు

**Q: How much battery does it use?**  
A: GPSLogger: 10-15% for 8-hour day. Web tracker: 20-30%.

**Q: Does it work without internet?**  
A: Yes! GPS doesn't need mobile data. Only needs WiFi when sending file.

**Q: What if I forget to start tracking?**  
A: No worries! Just start when you remember. Partial data is still useful.

**Q: Can supervisor track me in real-time?**  
A: No. Data stays on your phone until you send it at end of day.

**Q: What if phone battery dies?**  
A: Data saved up to that point is safe. Send when you charge phone.

**Q: ఎంత బ్యాటరీ ఉపయోగిస్తుంది?**  
A: GPSLogger: 8-గంటల రోజుకు 10-15%. వెబ్ ట్రాకర్: 20-30%.

**Q: ఇంటర్నెట్ లేకుండా పనిచేస్తుందా?**  
A: అవును! GPS కు మొబైల్ డేటా అవసరం లేదు. ఫైల్ పంపేటప్పుడు మాత్రమే WiFi కావాలి.

**Q: ట్రాకింగ్ ప్రారంభించడం మర్చిపోతే?**  
A: ఆందోళన లేదు! మీరు గుర్తుకు వచ్చినప్పుడు ప్రారంభించండి. పాక్షిక డేటా కూడా ఉపయోగకరంగా ఉంటుంది.

**Q: సూపర్‌వైజర్ నన్ను రియల్-టైమ్‌లో ట్రాక్ చేయగలరా?**  
A: లేదు. మీరు రోజు చివరన పంపే వరకు డేటా మీ ఫోన్‌లోనే ఉంటుంది.

---

## Summary / సారాంశం

**Best for most users: GPSLogger App**

```
Install → Configure → Use Daily
   ↓         ↓           ↓
5 min    Settings    Start/Stop
once     (once)      each day
```

**For workers who can't install apps: Web Tracker**

```
Receive HTML → Open → Start/Stop
      ↓          ↓        ↓
   WhatsApp   Chrome   Each day
```

**Both methods work! Choose what's easiest for your workers.**  
**రెండు పద్ధతులు పనిచేస్తాయి! మీ కార్మికులకు సులభమైనది ఎంచుకోండి.**

---

**Need help? / సహాయం కావాలా?**  
Test with one worker first, then roll out to all!  
మొదట ఒక కార్మికుడితో పరీక్షించండి, తర్వాత అందరికీ విస్తరించండి!
