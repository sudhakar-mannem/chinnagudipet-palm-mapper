# Cloud Agent Secrets Setup Guide

## Problem: Secrets Not Working in Cloud Agents

If your Cloud Agent can't access secrets even though they're configured in the Cursor Dashboard, this guide will help you fix it.

## Required Secrets for This Project

This Palm Mapper application requires the following environment variables:

| Secret Name | Required | Description |
|------------|----------|-------------|
| `OPENAI_API_KEY` | ✅ Yes | Your OpenAI API key (starts with `sk-`) |
| `GOOGLE_CREDENTIALS_B64` | ✅ Yes | Base64-encoded OAuth credentials JSON |
| `GOOGLE_TOKEN_B64` | ✅ Yes | Base64-encoded OAuth token JSON |
| `GOOGLE_DRIVE_FOLDER_ID` | Optional | Drive folder ID (defaults to `1_ZkYcDg4zu42RKNN5o4ChipG7Wlz43Gs`) |

## Why Secrets Aren't Working

### Common Causes:

1. **Public Repository Security** 🔒
   - This is a **public repository**: `github.com/sudhakar-mannem/chinnagudipet-palm-mapper`
   - Cursor may disable secret injection for public repos by default
   - You need to explicitly enable it

2. **Secrets Injected at Boot Only** ⚡
   - Secrets are injected when the Cloud Agent VM starts
   - They CANNOT be added to an already-running agent
   - Solution: Start a new Cloud Agent run

3. **Incorrect Secret Scope** 🎯
   - Secrets must be scoped to:
     - **User** (applies to all your repos), OR
     - **Repo** (specific to this repository)
   - Team secrets may not apply to personal repos

4. **Wrong Secret Names** 📝
   - Secret names are case-sensitive
   - Must use exact names listed above

## Step-by-Step Fix

### Step 1: Configure Secrets in Dashboard

1. Go to: **[Cursor Dashboard → Cloud Agents → Secrets](https://cursor.com/dashboard/cloud-agents/secrets)**

2. **Add or verify these secrets:**

   ```
   OPENAI_API_KEY = sk-proj-...your-key...
   GOOGLE_CREDENTIALS_B64 = eyJpbnN0YWxsZWQiOnsiY2xpZW50X2lkIjoi...
   GOOGLE_TOKEN_B64 = eyJ0b2tlbiI6ICJ5YTI5LmEwQWRNRDZFaEQ1...
   ```

3. **Set the correct scope:**
   - Choose **"User"** scope (recommended) OR
   - Choose **"Repo"** scope and enter: `github.com/sudhakar-mannem/chinnagudipet-palm-mapper`

### Step 2: Enable Secrets for Public Repositories

⚠️ **CRITICAL for public repos:**

1. In the Secrets dashboard, look for:
   - "Allow secrets for public repositories" checkbox
   - "Public repository access" toggle
   - Or a warning about public repo security

2. **Enable secret injection** for:
   - All public repos (if using User scope), OR
   - This specific repo: `github.com/sudhakar-mannem/chinnagudipet-palm-mapper`

### Step 3: Start a New Cloud Agent

🔄 **You MUST start a fresh Cloud Agent run:**

1. End the current agent (if running)
2. Start a new Cloud Agent for this repository
3. Secrets will be automatically injected at boot time

### Step 4: Verify Secrets Are Working

In your new Cloud Agent, run:

```bash
python3 test_secrets.py
```

**Expected output if working:**
```
✓ OPENAI_API_KEY SET (51 chars, preview: sk-proj-...)
✓ GOOGLE_CREDENTIALS_B64 SET (894 chars, preview: eyJpbnN0YW...)
✓ GOOGLE_TOKEN_B64 SET (512 chars, preview: eyJ0b2tlbi...)
✓ SUCCESS: All required secrets are properly configured!
```

**If still failing:**
```
✗ OPENAI_API_KEY MISSING (REQUIRED)
✗ GOOGLE_CREDENTIALS_B64 MISSING (REQUIRED)
✗ GOOGLE_TOKEN_B64 MISSING (REQUIRED)
```

## Troubleshooting

### Problem: Secrets still not showing up in new agent

**Check:**
- [ ] Are secrets added in Dashboard with exact names (case-sensitive)?
- [ ] Is scope set to "User" or correct "Repo" URL?
- [ ] For public repos: Is secret injection explicitly enabled?
- [ ] Did you start a **new** agent (not resume the old one)?

### Problem: "Public repository secrets disabled" error

**Solution:**
1. Dashboard → Cloud Agents → Secrets
2. Find the "Public repository" security settings
3. Enable: "Allow secrets for `github.com/sudhakar-mannem/chinnagudipet-palm-mapper`"

### Problem: How do I create the base64 secrets?

**For Google credentials:**

If you have `credentials/credentials.json` and `credentials/token.json` locally:

```bash
python3 make_cloud_secrets.py
```

This will print the base64-encoded values ready to paste into Dashboard.

Or manually:
```bash
# Linux/Mac
base64 -w 0 credentials/credentials.json
base64 -w 0 credentials/token.json

# Windows PowerShell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("credentials\credentials.json"))
[Convert]::ToBase64String([IO.File]::ReadAllBytes("credentials\token.json"))
```

## How Secrets Work in Cloud Agents

```
┌─────────────────────────────────────────────┐
│  Cursor Dashboard (Secrets Configuration)  │
│  - User secrets                             │
│  - Team secrets                             │
│  - Repo secrets                             │
│  - Public repo permissions                  │
└──────────────────┬──────────────────────────┘
                   │
                   │ (Boot Time Only)
                   ▼
┌─────────────────────────────────────────────┐
│  Cloud Agent VM Starts                      │
│  - Secrets injected as environment vars     │
│  - Available to all processes               │
│  - Cannot change after boot                 │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  Your Application                           │
│  - config.py reads secrets                  │
│  - Creates credential files                 │
│  - Application runs normally                │
└─────────────────────────────────────────────┘
```

## Security Notes

- ✅ Secret values are redacted in logs and transcripts
- ✅ Secrets are encrypted at rest in Cursor's infrastructure
- ⚠️ Public repos require explicit approval to prevent accidental exposure
- ⚠️ Never commit `.env` files or raw secrets to git
- ⚠️ Use `.gitignore` for `credentials/`, `.env`, and `secrets*.toml`

## Quick Reference

**Dashboard URL:**
https://cursor.com/dashboard/cloud-agents/secrets

**This Repository:**
`github.com/sudhakar-mannem/chinnagudipet-palm-mapper`

**Test Command:**
```bash
python3 test_secrets.py
```

**Expected Secret Names (case-sensitive):**
- `OPENAI_API_KEY`
- `GOOGLE_CREDENTIALS_B64`
- `GOOGLE_TOKEN_B64`
- `GOOGLE_DRIVE_FOLDER_ID` (optional)

---

**Still having issues?** Check:
1. Cursor Dashboard shows secrets are saved
2. Secrets are scoped to "User" or this repo URL
3. Public repo secret injection is enabled
4. You started a **NEW** Cloud Agent run
5. Run `python3 test_secrets.py` to verify
