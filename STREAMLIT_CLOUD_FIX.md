# Streamlit Cloud - Google Drive Images Fix / Streamlit Cloud లో ఫోటోల సమస్య పరిష్కారం

## సమస్య / Problem
Images are not loading in Streamlit Cloud because Google Drive credentials are not configured in Streamlit Cloud Secrets.

**Streamlit Cloud‌లో ఫోటోలు లోడ్ అవ్వడం లేదు** ఎందుకంటే Google Drive credentials Streamlit Cloud Secrets‌లో లేవు.

---

## పరిష్కారం / Solution (3 Steps)

### Step 1: Google OAuth Credentials పొందండి / Get Google OAuth Credentials

#### Option A: If you already have `credentials.json` and `token.json`
మీ దగ్గర ఇప్పటికే `credentials.json` మరియు `token.json` ఫైల్స్ ఉంటే:

1. Copy them to the `credentials/` folder in this repository
2. Go to Step 2

#### Option B: Generate new credentials (మొదటిసారి / First time)

1. **Google Cloud Console**కి వెళ్ళండి:
   - https://console.cloud.google.com
   
2. **Create a new project** లేదా existing project select చేయండి

3. **Enable Google Drive API:**
   - Search "Google Drive API"
   - Click "Enable"

4. **Create OAuth 2.0 Credentials:**
   - APIs & Services → Credentials
   - Click "Create Credentials" → "OAuth client ID"
   - Application type: "Desktop app"
   - Name: "Palm Mapper"
   - Download JSON file → Rename to `credentials.json`

5. **Place credentials in repository:**
   ```bash
   # Copy your downloaded credentials.json to:
   cp ~/Downloads/credentials.json credentials/credentials.json
   ```

6. **Authenticate and generate token:**
   ```bash
   python auth_drive.py
   ```
   - This opens browser for Google account authorization
   - After authorization, creates `token.json` automatically
   - Both files should now be in `credentials/` folder

---

### Step 2: Generate Base64 Secrets for Streamlit Cloud

రిపోజిటరీ‌లో ఈ కమాండ్ రన్ చేయండి:

```bash
python make_cloud_secrets.py
```

**Output example:**
```toml
# Paste into Streamlit Community Cloud Secrets (TOML-safe)

GOOGLE_CREDENTIALS_B64 = "eyJpbnN0YWxsZWQiOnsiY2xpZW50X2lkI..."

GOOGLE_TOKEN_B64 = "eyJ0b2tlbiI6InlhMjkuYTBBZjB2c..."

Also wrote: .streamlit/secrets_cloud_snippet.toml
```

**ఈ output కాపీ చేసుకోండి** - మనకు Step 3 లో కావాలి!

---

### Step 3: Streamlit Cloud Secrets Configure చేయండి

1. **Streamlit Cloud Dashboard**కి వెళ్ళండి:
   - https://share.streamlit.io/
   - Your app → **⋮ (menu)** → **Settings**

2. **Secrets tab** select చేయండి

3. **Paste these secrets** (Step 2 output + OpenAI key):

```toml
# ============================================
# Required Secrets for Palm Mapper
# ============================================

# OpenAI API key (for image analysis)
OPENAI_API_KEY = "sk-proj-your-actual-openai-key-here"
OPENAI_VISION_MODEL = "gpt-4o"

# Google Drive folder ID (your palm photos folder)
GOOGLE_DRIVE_FOLDER_ID = "1_ZkYcDg4zu42RKNN5o4ChipG7Wlz43Gs"

# Google OAuth credentials (paste from make_cloud_secrets.py output)
GOOGLE_CREDENTIALS_B64 = "eyJpbnN0YWxsZWQiOnsiY2xpZW50X2lkI..."

# Google OAuth token (paste from make_cloud_secrets.py output)
GOOGLE_TOKEN_B64 = "eyJ0b2tlbiI6InlhMjkuYTBBZjB2c..."
```

**Important notes:**
- Replace `"sk-proj-your-actual-openai-key-here"` with your real OpenAI API key
- Use the exact base64 strings from `make_cloud_secrets.py` output
- Update `GOOGLE_DRIVE_FOLDER_ID` if you're using a different folder

4. **Save** secrets

5. **Reboot app**:
   - Click "Reboot app" button
   - Or: **⋮ → Reboot**

---

## Verification / పరీక్ష

After reboot, the app should:
- ✅ Connect to Google Drive
- ✅ Download photos
- ✅ Analyze with OpenAI vision
- ✅ Display images on map

If images still don't load, check Streamlit Cloud logs:
- App menu → **Manage app** → **Logs**

---

## Common Issues / సాధారణ సమస్యలు

### Issue 1: "Invalid TOML" error
**Solution:** Make sure all values are in quotes `"..."` and there are no special characters unescaped

### Issue 2: "Google API error" 
**Solution:** 
- Check if Google Drive API is enabled in Google Cloud Console
- Verify `GOOGLE_DRIVE_FOLDER_ID` is correct
- Make sure folder is shared with the Google account used for authentication

### Issue 3: "OpenAI API error"
**Solution:**
- Verify API key is valid (starts with `sk-`)
- Check OpenAI account has credits
- Make sure `gpt-4o` model is available

### Issue 4: Token expired
Google OAuth tokens expire after ~7 days of inactivity.

**Solution:**
1. Run `python auth_drive.py` locally to refresh token
2. Run `python make_cloud_secrets.py` to regenerate base64
3. Update `GOOGLE_TOKEN_B64` in Streamlit Cloud Secrets
4. Reboot app

---

## Alternative: Using Environment Variables in Code

If you prefer not to use Streamlit Cloud Secrets UI, you can use `st.secrets` in code:

```python
import streamlit as st

# Access secrets in code
openai_key = st.secrets["OPENAI_API_KEY"]
drive_token = st.secrets["GOOGLE_TOKEN_B64"]
```

But the recommended approach is to configure everything in Settings → Secrets tab.

---

## Quick Reference Commands

```bash
# Step 1: Authenticate with Google Drive
python auth_drive.py

# Step 2: Generate base64 secrets for Cloud
python make_cloud_secrets.py

# Step 3: Test locally before deploying
streamlit run app.py

# Test secrets configuration
python test_secrets.py
```

---

## Related Files

- `.streamlit/secrets.toml.example` - Local secrets template
- `make_cloud_secrets.py` - Generate base64 for Cloud
- `auth_drive.py` - Authenticate with Google Drive
- `test_secrets.py` - Verify all secrets are configured
- `config.py` - Secrets loading logic

---

## Support Resources

- **Streamlit Cloud Secrets:** https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app/secrets-management
- **Google Drive API Setup:** https://developers.google.com/drive/api/quickstart/python
- **OpenAI API Keys:** https://platform.openai.com/api-keys

---

**తర్వాత సహాయం కావాలంటే అడగండి! / For more help, please ask!** 🌴
