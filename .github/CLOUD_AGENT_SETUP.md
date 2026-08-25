# Cloud Agent Setup for Palm Mapper

This document explains how to run this Palm Mapper application in Cursor Cloud Agents.

## Prerequisites

Before starting a Cloud Agent, configure secrets in the [Cursor Dashboard](https://cursor.com/dashboard/cloud-agents/secrets).

## Required Secrets

Add these secrets with **User** or **Repo** scope:

```
OPENAI_API_KEY = sk-proj-...
GOOGLE_CREDENTIALS_B64 = eyJpbnN0YWxsZWQi...
GOOGLE_TOKEN_B64 = eyJ0b2tlbiI6...
```

### Getting the Base64 Values

Run locally:
```bash
python3 make_cloud_secrets.py
```

Or manually encode:
```bash
base64 -w 0 credentials/credentials.json  # Linux/Mac
base64 -w 0 credentials/token.json
```

## ⚠️ Public Repository Notice

This is a **public repository**. You must:

1. Go to [Dashboard → Secrets](https://cursor.com/dashboard/cloud-agents/secrets)
2. Enable secret injection for public repositories
3. Explicitly allow secrets for: `github.com/sudhakar-mannem/chinnagudipet-palm-mapper`

Without this, secrets will NOT be injected into Cloud Agents.

## Verifying Setup

In your Cloud Agent, run:

```bash
python3 test_secrets.py
```

This will confirm all secrets are properly configured.

## Running the Application

Once secrets are verified:

```bash
# CLI mode
python3 cli.py

# Web UI (Streamlit)
streamlit run app.py
```

## Troubleshooting

**Secrets not working?**
- Secrets are injected at VM boot - start a NEW Cloud Agent
- Check secret names are exact (case-sensitive)
- Verify public repo permissions are enabled
- See [SECRETS_SETUP_GUIDE.md](../SECRETS_SETUP_GUIDE.md) for detailed help

**Dependencies missing?**
```bash
pip install -r requirements.txt
```

**Application errors?**
Check that credential files were created:
```bash
ls -la ~/.palm_mapper/credentials/
```
