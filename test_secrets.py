#!/usr/bin/env python3
"""
Test script to verify all required secrets are properly configured.
Run this in a new Cloud Agent to verify secret injection is working.
"""
import os
import sys
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))


def check_env_var(name: str, required: bool = True) -> tuple[bool, str]:
    """Check if environment variable exists and return status."""
    value = os.getenv(name)
    if value:
        # Show first/last few chars for verification without exposing full secret
        if len(value) > 20:
            preview = f"{value[:10]}...{value[-10:]}"
        else:
            preview = f"{value[:5]}..." if len(value) > 5 else "***"
        return True, f"✓ SET ({len(value)} chars, preview: {preview})"
    else:
        status = "✗ MISSING (REQUIRED)" if required else "✗ NOT SET (optional)"
        return False, status


def main():
    print("=" * 70)
    print("CURSOR CLOUD AGENT - SECRET INJECTION TEST")
    print("=" * 70)
    print()
    
    # Check all required secrets
    secrets_to_check = [
        ("OPENAI_API_KEY", True),
        ("GOOGLE_CREDENTIALS_B64", True),
        ("GOOGLE_TOKEN_B64", True),
        ("GOOGLE_DRIVE_FOLDER_ID", False),
    ]
    
    results = []
    all_required_present = True
    
    print("Environment Variable Status:")
    print("-" * 70)
    for var_name, required in secrets_to_check:
        success, status = check_env_var(var_name, required)
        results.append((var_name, success, status))
        print(f"{var_name:30s} {status}")
        if required and not success:
            all_required_present = False
    
    print("-" * 70)
    print()
    
    # Try to load config
    print("Testing config.py loading...")
    print("-" * 70)
    try:
        import config
        
        print(f"✓ config.py loaded successfully")
        print(f"  - OpenAI key configured: {config.openai_key_configured()}")
        print(f"  - Credentials file: {config.CREDENTIALS_FILE}")
        print(f"  - Credentials exists: {config.CREDENTIALS_FILE.exists()}")
        print(f"  - Token file: {config.TOKEN_FILE}")
        print(f"  - Token exists: {config.TOKEN_FILE.exists()}")
        print(f"  - Drive folder ID: {config.DRIVE_FOLDER_ID}")
        
        # Try to create credential files from base64 secrets
        if not config.CREDENTIALS_FILE.exists() or not config.TOKEN_FILE.exists():
            print()
            print("Attempting to materialize credentials from secrets...")
            status = config.reload_env()
            print(f"  - Credentials written: {status.get('credentials_written', False)}")
            print(f"  - Token written: {status.get('token_written', False)}")
            if status.get('credentials_error'):
                print(f"  - Credentials status: {status['credentials_error']}")
            if status.get('token_error'):
                print(f"  - Token status: {status['token_error']}")
    except Exception as e:
        print(f"✗ Error loading config: {e}")
        all_required_present = False
    
    print("-" * 70)
    print()
    
    # Final verdict
    print("=" * 70)
    if all_required_present:
        print("✓ SUCCESS: All required secrets are properly configured!")
        print("  You can now run the application.")
        return 0
    else:
        print("✗ FAILURE: Some required secrets are missing.")
        print()
        print("Next steps:")
        print("1. Go to: https://cursor.com/dashboard/cloud-agents/secrets")
        print("2. Add the missing secrets (user or repo scope)")
        print("3. For public repos, ensure secret injection is enabled")
        print("4. Start a NEW Cloud Agent run (secrets inject at boot)")
        return 1


if __name__ == "__main__":
    sys.exit(main())
