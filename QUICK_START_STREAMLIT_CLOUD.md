# 🚀 Quick Start - Streamlit Cloud లో ఫోటోలు లోడ్ చేయడం

## మీ సమస్య / Your Issue
**"ఫోటోలకు Streamlit Cloud Secrets‌లో చెల్లుబాటు అయ్యే డ్రైవ్ టోకెన్ కావాలి"**

**Images are not loading in Streamlit Cloud** ❌

---

## ⚡ 3-Minute Fix

### Step 1: Generate Secrets (Local Computer లో)

```bash
# 1. Authenticate with Google Drive
python auth_drive.py

# 2. Generate base64 secrets
python make_cloud_secrets.py
```

**Output copy చేసుకోండి** - మీకు ఇలాంటి output వస్తుంది:

```toml
GOOGLE_CREDENTIALS_B64 = "eyJpbnN0YWxsZWQiOnsiY2xpZW50X2lkI..."
GOOGLE_TOKEN_B64 = "eyJ0b2tlbiI6InlhMjkuYTBBZjB2cy1BNj..."
```

---

### Step 2: Paste in Streamlit Cloud

1. Go to: https://share.streamlit.io/
2. Your app → **⋮ (menu)** → **Settings** → **Secrets**
3. Paste ఈ content:

```toml
# Required secrets
OPENAI_API_KEY = "sk-your-openai-key-here"
OPENAI_VISION_MODEL = "gpt-4o"
GOOGLE_DRIVE_FOLDER_ID = "1_ZkYcDg4zu42RKNN5o4ChipG7Wlz43Gs"

# Paste from Step 1 output:
GOOGLE_CREDENTIALS_B64 = "eyJpbnN్టాల్లెడ్..."
GOOGLE_TOKEN_B64 = "eyJ0b2tlbi..."
```

4. **Save** → **Reboot app**

---

### Step 3: Verify

App reboot అయ్యాక images load అవుతాయి! ✅

---

## 📚 Complete Guides

- **English:** [STREAMLIT_CLOUD_FIX.md](STREAMLIT_CLOUD_FIX.md)
- **తెలుగు:** [STREAMLIT_CLOUD_SETUP_TELUGU.md](STREAMLIT_CLOUD_SETUP_TELUGU.md)

---

## ❓ Common Questions

### Q: `auth_drive.py` run చేయగానే error వస్తుందా?
**A:** మొదట Google Cloud Console లో OAuth credentials create చేయాలి:
1. https://console.cloud.google.com
2. Google Drive API enable చేయండి
3. OAuth client ID (Desktop app) create చేయండి
4. Download JSON → `credentials/credentials.json` గా save చేయండి

### Q: Token expire అవుతుందా?
**A:** Yes, 7 days తర్వాత. Refresh చేయడానికి:
```bash
python auth_drive.py
python make_cloud_secrets.py
# Update GOOGLE_TOKEN_B64 in Streamlit Cloud Secrets
```

### Q: OpenAI API key ఎక్కడ పొందాలి?
**A:** https://platform.openai.com/api-keys

---

## 🆘 Still Not Working?

1. Check Streamlit Cloud logs: App menu → **Logs**
2. Verify all secrets are in quotes `"..."`
3. Make sure Drive folder is shared with authenticated Google account
4. See detailed troubleshooting in full guides above

---

**ఇప్పుడు images load అవ్వాలి!** 🎉
