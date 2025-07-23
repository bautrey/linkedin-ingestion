#!/usr/bin/env python3
"""
Simple database setup using HTTP requests to Supabase
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

def setup_database():
    url = os.getenv('SUPABASE_URL')
    service_key = os.getenv('SUPABASE_SERVICE_KEY')
    
    if not url or not service_key:
        print("❌ Missing Supabase credentials")
        return False
    
    # Use the Supabase REST API to create tables
    headers = {
        'apikey': service_key,
        'Authorization': f'Bearer {service_key}',
        'Content-Type': 'application/json'
    }
    
    # Try to query existing tables first
    try:
        print("🔍 Checking existing tables...")
        response = requests.get(f"{url}/rest/v1/linkedin_profiles?limit=1", headers=headers)
        
        if response.status_code == 200:
            print("✅ Tables already exist!")
            return True
        elif "relation" in response.text and "does not exist" in response.text:
            print("📋 Tables don't exist, need to create them")
        else:
            print(f"⚠️  Unexpected response: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Error checking tables: {e}")
        return False
    
    print("❌ Cannot create tables via REST API - tables need to be created via Supabase dashboard")
    print("\nPlease:")
    print("1. Go to https://supabase.com/dashboard/projects")
    print("2. Select your project") 
    print("3. Go to SQL Editor")
    print("4. Run the schema from app/database/schema.sql")
    print("\nOr I can show you exactly what to paste...")
    
    return False

if __name__ == "__main__":
    setup_database()
