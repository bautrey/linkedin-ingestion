#!/usr/bin/env python3

import requests
import json

# API details
base_url = "https://smooth-mailbox-production.up.railway.app/api/v1"
headers = {
    "x-api-key": "li_HieZz-IjBp0uE7d-rZkRE0qyy12r5_ZJS_FR4jMvv0I",
    "Content-Type": "application/json"
}

print("🔍 Getting a test profile ID...")

try:
    response = requests.get(
        f"{base_url}/profiles?limit=1",
        headers=headers,
        timeout=30
    )
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        profiles = result.get('profiles', [])
        
        if profiles:
            profile = profiles[0]
            print("✅ Found test profile:")
            print(f"ID: {profile.get('id')}")
            print(f"Name: {profile.get('profile', {}).get('firstName', '')} {profile.get('profile', {}).get('lastName', '')}")
            print(f"Headline: {profile.get('profile', {}).get('headline', 'N/A')}")
            
        else:
            print("❌ No profiles found in database")
            
    else:
        print("❌ Failed to get profiles")
        try:
            error_data = response.json()
            print("Error Response:")
            print(json.dumps(error_data, indent=2))
        except:
            print("Raw Response:")
            print(response.text)

except requests.exceptions.RequestException as e:
    print(f"❌ Request failed: {e}")
