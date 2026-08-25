# 🌴 Streamlit Cloud లో Palm Mapper Setup చేయడం

## సరళమైన 3 స్టెప్స్ / Simple 3 Steps

### 📋 అవసరమైనవి / Requirements
- Google Drive folder with palm photos
- OpenAI API key (https://platform.openai.com/api-keys)
- Google Cloud Console access

---

## 🔐 Step 1: Google Drive Authentication (5 నిమిషాలు)

### 1.1 Google Cloud Console Setup

```
1. https://console.cloud.google.com కి వెళ్ళండి
2. New project create చేయండి లేదా existing project select చేయండి
3. "Google Drive API" enable చేయండి
4. OAuth 2.0 credentials create చేయండి (Desktop app type)
5. credentials.json download చేసుకోండి
```

### 1.2 Repository లో Credentials Place చేయండి

```bash
# Downloaded JSON file ను credentials folder లోకి కాపీ చేయండి
cp ~/Downloads/client_secret_*.json credentials/credentials.json
```

### 1.3 Token Generate చేయండి

```bash
# ఈ command browser open చేస్తుంది - Google account తో authorize చేయండి
python auth_drive.py
```

**Output:** `credentials/token.json` file create అవుతుంది ✅

---

## 🔑 Step 2: Base64 Secrets Generate చేయండి (1 నిమిషం)

```bash
python make_cloud_secrets.py
```

**Output చూపిస్తుంది:**
```
GOOGLE_CREDENTIALS_B64 = "eyJpbnN0YWxsZWQiOnsiY2..."
GOOGLE_TOKEN_B64 = "eyJ0b2tlbiI6InlhMjkuYTBBZ..."
```

📝 **ఈ output పూర్తిగా కాపీ చేసుకోండి!** మనకు Step 3 లో paste చేయాలి.

---

## ☁️ Step 3: Streamlit Cloud Secrets Configure చేయండి (3 నిమిషాలు)

### 3.1 Streamlit Cloud Dashboard Open చేయండి

```
1. https://share.streamlit.io/ కి వెళ్ళండి
2. మీ app select చేయండి
3. Menu (⋮) → Settings
4. "Secrets" tab click చేయండి
```

### 3.2 Secrets Paste చేయండి

**Streamlit Cloud Secrets box లో ఇలా paste చేయండి:**

```toml
# ----- OpenAI Configuration -----
OPENAI_API_KEY = "sk-proj-మీ-openai-key-ఇక్కడ-paste-చేయండి"
OPENAI_VISION_MODEL = "gpt-4o"

# ----- Google Drive Folder -----
GOOGLE_DRIVE_FOLDER_ID = "మీ-drive-folder-id-ఇక్కడ"

# ----- Google OAuth (Step 2 నుండి copy చేసిన base64 values) -----
GOOGLE_CREDENTIALS_B64 = "eyJpbnN0YWxsZWQiOnsiY2xpZW50X2lkIjoiMTIzNDU..."

GOOGLE_TOKEN_B64 = "eyJ0b2tlbiI6InlhMjkuYTBBZjB2cy1BNjVhQXk4RU..."
```

### 3.3 Save & Reboot

```
1. "Save" button click చేయండి
2. "Reboot app" button click చేయండి
3. 30 సెకన్లు wait చేయండి
```

---

## ✅ పరీక్ష / Testing

App reboot అయ్యాక:

1. **Map View** open చేయండి
2. **Images loading చూడాలి** 🎉
3. Photos clicking చేసి పెద్దవి చూడవచ్చు
4. Health status colors కనిపించాలి (green/amber/red)

---

## 🔴 సమస్యలు వస్తే / Troubleshooting

### సమస్య 1: "TOML validation error"
❌ **కారణం:** Quotes లేదా special characters wrong format లో ఉన్నాయి  
✅ **పరిష్కారం:** All values double quotes లో ఉన్నాయా check చేయండి `"..."`

### సమస్య 2: "Google API authentication failed"
❌ **కారణం:** Token expire అయ్యింది (7 రోజుల తర్వాత expire అవుతుంది)  
✅ **పరిష్కారం:**
```bash
python auth_drive.py          # Token refresh చేయండి
python make_cloud_secrets.py  # Base64 regenerate చేయండి
# Streamlit Cloud Secrets లో GOOGLE_TOKEN_B64 update చేయండి
# App reboot చేయండి
```

### సమస్య 3: "OpenAI API error" 
❌ **కారణం:** API key invalid or credits లేవు  
✅ **పరిష్కారం:** 
- https://platform.openai.com/api-keys check చేయండి
- Account balance check చేయండి

### సమస్య 4: Images still not loading
❌ **కారణం:** Drive folder ID wrong or folder not shared  
✅ **పరిష్కారం:**
1. Google Drive లో folder URL నుండి ID copy చేయండి:
   ```
   https://drive.google.com/drive/folders/1_ZkYcDg4zu42RKNN5o4ChipG7Wlz43Gs
                                           ↑
                                      ఇది ID
   ```
2. `GOOGLE_DRIVE_FOLDER_ID` value update చేయండి
3. Folder ని authenticate చేసిన Google account తో share చేసి ఉండాలి

---

## 📊 Visual Flow

```
Local Computer                    Streamlit Cloud
═════════════                     ═══════════════

credentials.json ──┐
                   │
token.json ────────┤
                   │
                   ├──> python make_cloud_secrets.py
                   │
                   ├──> GOOGLE_CREDENTIALS_B64
                   │    GOOGLE_TOKEN_B64
                   │
                   └──> Copy to Streamlit Secrets ──> App can access
                                                       Google Drive! ✅
```

---

## 🔄 Token Refresh (వారానికొకసారి)

Google tokens expire అవుతాయి. Refresh చేయడానికి:

```bash
# Local లో:
python auth_drive.py
python make_cloud_secrets.py

# Streamlit Cloud లో:
# Update GOOGLE_TOKEN_B64 only
# Save & Reboot
```

---

## 📚 Additional Resources

- **Complete English Guide:** `STREAMLIT_CLOUD_FIX.md`
- **Local Testing:** `python test_secrets.py`
- **Original Secrets Guide:** `SECRETS_SETUP_GUIDE.md`

---

## 💡 Tips

1. **Token security:** Never commit `token.json` or secrets files to GitHub
2. **API costs:** OpenAI charges per image analysis - monitor usage
3. **Drive quota:** Large folders may take time to download first time
4. **Mobile view:** App is mobile-responsive, works on phones too!

---

**ఇంకా సమస్యలు ఉంటే GitHub issues లో అడగండి!**  
**Still having issues? Ask in GitHub issues!** 🌴
