# Palm Plant Health Mapper

Sync oil palm field photos from Google Drive, use AI to score each plant, and export a color-coded Google Earth map. Click any plant icon to see the latest photo.

## What it does

1. **Reads photos** from your Drive folder:  
   [`1_ZkYcDg4zu42RKNN5o4ChipG7Wlz43Gs`](https://drive.google.com/drive/folders/1_ZkYcDg4zu42RKNN5o4ChipG7Wlz43Gs)
2. **Extracts GPS** from EXIF when present, otherwise from the coordinate stamp printed on the photo (via vision AI).
3. **Scores plant condition** with OpenAI vision:
   - **Green** — healthy
   - **Amber** — needs attention
   - **Red** — critical / diseased
   - **White** — cannot determine
4. **Exports** `palm_health.kmz` / `.kml` for Google Earth (photos embedded in KMZ balloons).
5. **Shows an in-app map** where you can click markers to preview the latest photo.

When multiple photos exist for the same plant location, only the **newest** photo is mapped.

## One-time setup

### 1. Python packages

```powershell
cd "C:\Users\smann\OneDrive\Repo\Chinnagudipet Farm Project\palm_mapper"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. OpenAI key

```powershell
copy .env.example .env
```

Edit `.env` and set:

```
OPENAI_API_KEY=sk-...
GOOGLE_DRIVE_FOLDER_ID=1_ZkYcDg4zu42RKNN5o4ChipG7Wlz43Gs
```

### 3. Google Drive OAuth

1. Open [Google Cloud Console](https://console.cloud.google.com/)
2. Create (or select) a project
3. Enable **Google Drive API**
4. Configure OAuth consent screen (External is fine for personal use; add your Google account as a test user)
5. **Credentials → Create credentials → OAuth client ID → Desktop app**
6. Download the JSON and save it as:

```
palm_mapper/credentials/credentials.json
```

## Run the app

```powershell
cd "C:\Users\smann\OneDrive\Repo\Chinnagudipet Farm Project\palm_mapper"
.\.venv\Scripts\Activate.ps1
streamlit run app.py
```

Click **Sync Drive & analyze plants**. The first run opens a browser window to authorize Google Drive.

### Or use the CLI

```powershell
python cli.py
python cli.py --reanalyze
python cli.py --force-download
```

## Google Earth

1. Download **KMZ (photos embedded)** from the app (or open `output/palm_health.kmz`)
2. In Google Earth Pro: **File → Open** → select the KMZ
3. Click a colored paddle → balloon shows health summary + latest photo

| Icon color | Meaning |
|---|---|
| Green | Healthy |
| Yellow/Amber | Needs attention |
| Red | Critical / diseased |
| White | Unknown / AI could not determine |

## Project layout

```
palm_mapper/
  app.py                 # Streamlit UI + map
  cli.py                 # Command-line runner
  config.py
  services/
    drive.py             # Google Drive sync
    analyze.py           # GPS stamp + health AI
    kml_builder.py       # KML / KMZ export
    pipeline.py          # End-to-end run
    models.py
  credentials/           # credentials.json + token.json (local only)
  cache/photos/          # Downloaded photos
  output/                # palm_health.kml / .kmz / .json
```

## Notes

- Analysis is cached per Drive file version; only new or changed photos are re-scored unless you enable **Re-analyze**.
- Prefer **KMZ** over KML in Google Earth so photos display offline without making Drive files public.
- If a photo has no readable GPS stamp and no EXIF GPS, it is skipped on the map (counted under “No GPS”).
