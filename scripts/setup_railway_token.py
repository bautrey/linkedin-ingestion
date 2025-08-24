#!/usr/bin/env python3
"""
Railway Token Setup Helper

This script helps you set up the Railway API token needed for the log retrieval system.
"""

import os
import json
import subprocess
import sys


def get_railway_token_from_cli():
    """Try to extract Railway token from CLI config"""
    config_path = os.path.expanduser("~/.railway/config.json")
    
    if not os.path.exists(config_path):
        return None
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            return config.get('token')
    except Exception as e:
        print(f"Error reading Railway config: {e}")
        return None


def main():
    print("🚂 Railway Token Setup Helper")
    print("=" * 50)
    
    # Check if token is already set
    existing_token = os.getenv('RAILWAY_TOKEN')
    if existing_token:
        print(f"✅ RAILWAY_TOKEN environment variable is already set")
        print(f"   Token: {existing_token[:10]}...{existing_token[-10:]}")
        return
    
    # Try to get token from Railway CLI config
    token = get_railway_token_from_cli()
    if token:
        print(f"✅ Found Railway token in CLI config")
        print(f"   Token: {token[:10]}...{token[-10:]}")
        print("\nTo use this token, run:")
        print(f"   export RAILWAY_TOKEN='{token}'")
        print("\nOr add it to your shell profile (.zshrc, .bashrc, etc.):")
        print(f"   echo 'export RAILWAY_TOKEN=\"{token}\"' >> ~/.zshrc")
        return
    
    # If no token found, provide instructions
    print("❌ No Railway token found.")
    print("\n💡 To set up Railway token:")
    print("1. Log in to Railway CLI:")
    print("   railway login")
    print("\n2. Or create a project token in Railway dashboard:")
    print("   - Go to your project settings")
    print("   - Navigate to 'Tokens' tab")
    print("   - Create a new project token")
    print("   - Set it as environment variable:")
    print("     export RAILWAY_TOKEN='your_token_here'")
    
    print("\n3. Or get your personal API token:")
    print("   - Go to https://railway.app/account/tokens")
    print("   - Create a new token")
    print("   - Set it as environment variable:")
    print("     export RAILWAY_TOKEN='your_token_here'")


if __name__ == "__main__":
    main()
