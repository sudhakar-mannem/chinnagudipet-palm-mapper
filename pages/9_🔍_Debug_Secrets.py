"""Debug page to verify secrets and Google Drive connectivity in Streamlit."""
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

st.set_page_config(page_title="Debug Secrets", page_icon="🔍")

st.title("🔍 Secrets & Drive Connectivity Debug")

st.info("Use this page to verify your Streamlit secrets are configured correctly.")

# Check config
try:
    import config
    
    st.subheader("📋 Configuration Status")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("OpenAI Key", "✅ Configured" if config.openai_key_configured() else "❌ Missing")
        st.metric("Drive Folder ID", config.DRIVE_FOLDER_ID[:20] + "...")
    
    with col2:
        cred_exists = config.CREDENTIALS_FILE.exists()
        token_exists = config.TOKEN_FILE.exists()
        st.metric("Credentials File", "✅ Exists" if cred_exists else "❌ Missing")
        st.metric("Token File", "✅ Exists" if token_exists else "❌ Missing")
    
    # Show credential file paths
    st.subheader("📁 File Paths")
    st.code(f"""
Credentials: {config.CREDENTIALS_FILE}
Token:       {config.TOKEN_FILE}
Cache Dir:   {config.CACHE_DIR}
Output Dir:  {config.OUTPUT_DIR}
""")
    
    # Try to reload and materialize secrets
    st.subheader("🔄 Reload Secrets")
    
    if st.button("Reload Config & Materialize Secrets"):
        with st.spinner("Reloading configuration..."):
            status = config.reload_env()
            
            st.write("**Secret Status:**")
            st.json(status)
            
            if status.get("credentials_written") and status.get("token_written"):
                st.success("✅ All credential files created successfully!")
            else:
                st.error("❌ Some credential files failed to create")
                st.write("**Credentials:**", status.get("credentials_error"))
                st.write("**Token:**", status.get("token_error"))
    
    # Test Drive Connection
    st.subheader("🔗 Test Google Drive Connection")
    
    if st.button("Test Drive Connection"):
        if not (config.CREDENTIALS_FILE.exists() and config.TOKEN_FILE.exists()):
            st.error("❌ Credential files don't exist. Click 'Reload Config' first.")
        else:
            with st.spinner("Testing Drive connection..."):
                try:
                    from services.drive import build_drive_service
                    
                    service = build_drive_service()
                    
                    # Test by listing folders
                    results = service.files().list(
                        q=f"'{config.DRIVE_FOLDER_ID}' in parents and trashed=false",
                        pageSize=5,
                        fields="files(id, name)"
                    ).execute()
                    
                    files = results.get('files', [])
                    
                    st.success(f"✅ Connected! Found {len(files)} items in Drive folder")
                    
                    if files:
                        st.write("**Sample files:**")
                        for f in files[:5]:
                            st.write(f"- {f['name']}")
                    
                except Exception as e:
                    st.error(f"❌ Drive connection failed: {e}")
                    st.exception(e)
    
    # Show environment variables (redacted)
    st.subheader("🔐 Environment Variables (Redacted)")
    
    import os
    
    secrets_check = {
        "OPENAI_API_KEY": bool(os.getenv("OPENAI_API_KEY")),
        "GOOGLE_CREDENTIALS_B64": bool(os.getenv("GOOGLE_CREDENTIALS_B64")),
        "GOOGLE_TOKEN_B64": bool(os.getenv("GOOGLE_TOKEN_B64")),
        "GOOGLE_DRIVE_FOLDER_ID": bool(os.getenv("GOOGLE_DRIVE_FOLDER_ID")),
    }
    
    for key, is_set in secrets_check.items():
        if is_set:
            value = os.getenv(key, "")
            preview = f"{value[:10]}...{value[-5:]}" if len(value) > 15 else "***"
            st.write(f"✅ `{key}`: {preview}")
        else:
            st.write(f"❌ `{key}`: NOT SET")
    
    # Streamlit secrets check
    st.subheader("📦 Streamlit Secrets")
    
    try:
        if hasattr(st, "secrets"):
            st.write("✅ Streamlit secrets available")
            
            secret_keys = list(st.secrets.keys())
            st.write(f"**Found {len(secret_keys)} secrets:**")
            for key in secret_keys:
                st.write(f"- `{key}`")
        else:
            st.write("❌ Streamlit secrets not available")
    except Exception as e:
        st.error(f"Error accessing secrets: {e}")

except Exception as e:
    st.error(f"Configuration error: {e}")
    st.exception(e)

st.divider()

st.caption("💡 **Tip:** If secrets aren't working, check that they're in TOML format in Streamlit's App Settings → Secrets")
