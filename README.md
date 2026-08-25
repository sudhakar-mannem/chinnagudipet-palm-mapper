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

## Deploy on Cursor Cloud Agents

To run this application in Cursor Cloud Agents, see **[Cloud Agent Setup Guide](.github/CLOUD_AGENT_SETUP.md)**.

**Quick start:**
1. Configure secrets in [Cursor Dashboard](https://cursor.com/dashboard/cloud-agents/secrets)
2. Enable secret injection for this public repository
3. Start a new Cloud Agent
4. Run `python3 test_secrets.py` to verify setup
5. Run `python3 cli.py` or `streamlit run app.py`

See **[SECRETS_SETUP_GUIDE.md](SECRETS_SETUP_GUIDE.md)** if secrets aren't working.

## Deploy on Streamlit Community Cloud

**📖 Complete Setup Guide:** See **[STREAMLIT_CLOUD_FIX.md](STREAMLIT_CLOUD_FIX.md)** (English) or **[STREAMLIT_CLOUD_SETUP_TELUGU.md](STREAMLIT_CLOUD_SETUP_TELUGU.md)** (తెలుగు)

**Quick steps:**

1. **Authenticate with Google Drive locally:**
   ```bash
   python auth_drive.py  # Opens browser for Google OAuth
   ```

2. **Generate base64 secrets for Cloud:**
   ```bash
   python make_cloud_secrets.py
   ```
   Copy the output (GOOGLE_CREDENTIALS_B64 and GOOGLE_TOKEN_B64)

3. **Deploy to Streamlit Cloud:**
   - Open [share.streamlit.io](https://share.streamlit.io/)
   - Create app from `sudhakar-mannem/chinnagudipet-palm-mapper`
   - Main file: `app.py`, Python: 3.12

4. **Configure Secrets** (Settings → Secrets):
   ```toml
   OPENAI_API_KEY = "sk-your-key-here"
   OPENAI_VISION_MODEL = "gpt-4o"
   GOOGLE_DRIVE_FOLDER_ID = "1_ZkYcDg4zu42RKNN5o4ChipG7Wlz43Gs"
   GOOGLE_CREDENTIALS_B64 = "eyJpbnN0YWxsZWQiOnt..."  # from make_cloud_secrets.py
   GOOGLE_TOKEN_B64 = "eyJ0b2tlbiI6InlhMjku..."      # from make_cloud_secrets.py
   ```

5. **Save & Deploy**

**Note:** Use base64-encoded credentials (`*_B64`) instead of raw JSON to avoid TOML validation errors.

**Troubleshooting:** If images don't load, see the detailed guides above.

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
- **Map outliers:** `config.EXCLUDED_OUTLIER_MAP_NUMBERS` / `EXCLUDED_OUTLIER_FILE_IDS` hide selected plants from Map View and consolidated KML while keeping photos + original GPS in `data/plant_state.json` (`excluded_from_map` + `meta.outlier_exclusions`). Remaining plants are renumbered 1..N.
