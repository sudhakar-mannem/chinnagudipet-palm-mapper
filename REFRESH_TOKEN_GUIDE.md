# Google Drive Token Refresh Guide

## Problem
Your Google OAuth token has expired. Error:
```
Token has been expired or revoked
```

## Solution
You need to re-authenticate with Google to get a fresh token.

---

## Method 1: Using Your Local PC (Recommended)

### Prerequisites:
- Python 3.12 installed
- Google OAuth credentials file (`credentials.json`)
- Web browser

### Steps:

1. **Download/Clone this repository to your PC:**
   ```powershell
   cd "C:\Users\smann\OneDrive\Repo\Chinnagudipet Farm Project"
   git pull origin main
   ```

2. **Set up virtual environment (if not done):**
   ```powershell
   cd palm_mapper
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

3. **Make sure you have credentials.json:**
   - Location: `palm_mapper/credentials/credentials.json`
   - If missing, download from [Google Cloud Console](https://console.cloud.google.com/):
     - Go to your project
     - APIs & Services → Credentials
     - Download OAuth 2.0 Client ID (Desktop app type)
     - Save as `credentials/credentials.json`

4. **Run the authentication script:**
   ```powershell
   python auth_drive.py
   ```
   
   **This will:**
   - Delete old expired token
   - Open browser for Google login
   - Ask you to sign in and grant permissions
   - Save fresh `credentials/token.json`

5. **Generate Streamlit secrets:**
   ```powershell
   python make_cloud_secrets.py
   ```
   
   **Output will look like:**
   ```
   GOOGLE_CREDENTIALS_B64 = "eyJpbnN0YWxsZWQi..."
   
   GOOGLE_TOKEN_B64 = "eyJ0b2tlbiI6ICJ5YTI5..."
   ```

6. **Update Streamlit:**
   - Go to: https://5xrxrfp9f.streamlit.app
   - Menu → Manage app → Settings → Secrets
   - Replace the `GOOGLE_TOKEN_B64` line with the new value
   - Click Save
   - Wait 30 seconds for app to restart

7. **Test:**
   - Go to Debug page in Streamlit
   - Click "Test Drive Connection"
   - Should show: ✅ Connected!

---

## Method 2: Manual Token Refresh (If You Can't Run Scripts)

If you can't run Python scripts, you can manually refresh the token:

### Steps:

1. **Go to Google OAuth Playground:**
   - Visit: https://developers.google.com/oauthplayground/

2. **Configure:**
   - Click ⚙️ (settings) in top right
   - Check "Use your own OAuth credentials"
   - Enter your Client ID and Client Secret (from credentials.json)

3. **Select API:**
   - In left panel, find "Drive API v3"
   - Check: `https://www.googleapis.com/auth/drive.readonly`

4. **Authorize:**
   - Click "Authorize APIs"
   - Sign in with your Google account
   - Grant permissions
   - You'll get an authorization code

5. **Exchange for Token:**
   - Click "Exchange authorization code for tokens"
   - Copy the "Refresh token" and "Access token"

6. **Create Token JSON:**
   Create a file with this structure:
   ```json
   {
     "token": "ACCESS_TOKEN_HERE",
     "refresh_token": "REFRESH_TOKEN_HERE",
     "token_uri": "https://oauth2.googleapis.com/token",
     "client_id": "YOUR_CLIENT_ID",
     "client_secret": "YOUR_CLIENT_SECRET",
     "scopes": ["https://www.googleapis.com/auth/drive.readonly"],
     "expiry": "2026-08-28T12:00:00Z"
   }
   ```

7. **Base64 Encode:**
   - In PowerShell:
     ```powershell
     $json = Get-Content -Raw token.json
     [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($json))
     ```
   - Or use: https://www.base64encode.org/

8. **Update Streamlit:**
   - Paste the base64 string as `GOOGLE_TOKEN_B64` value in Streamlit secrets

---

## Troubleshooting

### "Missing credentials.json"
- Download OAuth client from Google Cloud Console
- Make sure it's "Desktop app" type (not Web application)
- Place in `credentials/` folder

### "Port already in use"
- The script tries multiple ports automatically
- If all fail, use manual mode (it will prompt you)

### "Access blocked: App not verified"
- During testing, add your Google account as a test user in OAuth consent screen
- Or publish the app (not recommended for personal use)

### Token still expires quickly
- Make sure `access_type="offline"` is set (already in auth_drive.py)
- Make sure you get a refresh_token (should be in token.json)

---

## How Often Do I Need to Refresh?

- **Google tokens typically last 6 months**
- You'll need to refresh when you see "token expired" errors
- Consider setting a calendar reminder to refresh every 5 months

---

## Security Notes

- ✅ Never commit `credentials.json` or `token.json` to git (they're gitignored)
- ✅ Keep base64 secrets private
- ✅ Use `.env` for local development (also gitignored)
- ⚠️ This is a personal app - keep OAuth in "Testing" mode in Google Cloud Console

---

## Need Help?

If you're stuck, let me know at which step and I'll help troubleshoot!
