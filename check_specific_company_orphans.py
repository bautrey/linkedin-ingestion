#!/usr/bin/env python3
"""
Check Specific Company for Orphaned Profile Relationships

Check company ID 7340cdef-90e4-497a-893b-c9d3fd9e76af for orphaned profile relationships
"""

import asyncio
import os
import sys
from datetime import datetime

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set production environment variables from Railway
PRODUCTION_SUPABASE_URL = "https://yirtidxcgkkoizwqpdfv.supabase.co"
PRODUCTION_SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlpcnRpZHhjZ2trb2l6d3FwZGZ2Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MzIwOTQ5MSwiZXhwIjoyMDY4Nzg1NDkxfQ.LjvQohgwXbKkiRUyDlGvb4Hn4SoRCZPLjye00VIVrBg"

# Override environment to use production database
os.environ["SUPABASE_URL"] = PRODUCTION_SUPABASE_URL
os.environ["SUPABASE_SERVICE_KEY"] = PRODUCTION_SUPABASE_SERVICE_KEY
os.environ["ENVIRONMENT"] = "production"

from app.database.supabase_client import SupabaseClient

COMPANY_ID = "7340cdef-90e4-497a-893b-c9d3fd9e76af"

async def check_company_relationships():
    """Check the specific company for orphaned profile relationships"""
    
    db_client = SupabaseClient()
    await db_client._ensure_client()
    
    print(f"🔍 Checking company {COMPANY_ID} for orphaned profile relationships...")
    print(f"🌐 Database URL: {PRODUCTION_SUPABASE_URL}")
    
    # Get all relationships for this specific company
    pc_table = db_client.client.table("profile_companies")
    relationships_result = await pc_table.select("*").eq("company_id", COMPANY_ID).execute()
    
    if not relationships_result.data:
        print(f"✅ No relationships found for company {COMPANY_ID}")
        return
    
    relationships = relationships_result.data
    print(f"📊 Found {len(relationships)} relationships for this company")
    
    # Check each relationship's profile
    orphaned_count = 0
    valid_count = 0
    
    profiles_table = db_client.client.table("linkedin_profiles")
    
    for i, rel in enumerate(relationships):
        profile_id = rel["profile_id"]
        
        # Check if this profile exists
        profile_result = await profiles_table.select("id").eq("id", profile_id).execute()
        
        if profile_result.data and len(profile_result.data) > 0:
            print(f"✅ Relationship {i+1}: Profile {profile_id} EXISTS")
            print(f"    Job Title: {rel.get('job_title', 'N/A')}")
            print(f"    Created: {rel.get('created_at', 'N/A')}")
            valid_count += 1
        else:
            print(f"🚨 ORPHANED Relationship {i+1}: Profile {profile_id} MISSING")
            print(f"    Relationship ID: {rel['id']}")
            print(f"    Job Title: {rel.get('job_title', 'N/A')}")
            print(f"    Created: {rel.get('created_at', 'N/A')}")
            orphaned_count += 1
        print()
    
    print(f"📊 Summary for company {COMPANY_ID}:")
    print(f"   Valid relationships: {valid_count}")
    print(f"   Orphaned relationships: {orphaned_count}")
    
    if orphaned_count > 0:
        print(f"\n❓ Delete {orphaned_count} orphaned relationships for this company?")
        response = input("Type 'DELETE' to confirm: ").strip()
        
        if response == "DELETE":
            deleted_count = 0
            for rel in relationships:
                profile_id = rel["profile_id"]
                # Check if profile exists
                profile_result = await profiles_table.select("id").eq("id", profile_id).execute()
                
                if not profile_result.data or len(profile_result.data) == 0:
                    # This is orphaned - delete it
                    try:
                        delete_result = await pc_table.delete().eq("id", rel["id"]).execute()
                        if delete_result.data and len(delete_result.data) > 0:
                            deleted_count += 1
                            print(f"✅ Deleted orphaned relationship {rel['id']}")
                        else:
                            print(f"⚠️ Relationship {rel['id']} not found or already deleted")
                    except Exception as e:
                        print(f"❌ Failed to delete relationship {rel['id']}: {str(e)}")
            
            print(f"🎉 Deleted {deleted_count} orphaned relationships for company {COMPANY_ID}")
        else:
            print("❌ Cleanup cancelled")

async def main():
    print("🔍 Specific Company Orphan Check")
    print("=" * 40)
    print(f"⏰ Started at: {datetime.now()}")
    print(f"🏢 Company ID: {COMPANY_ID}")
    print()
    
    try:
        await check_company_relationships()
    except Exception as e:
        print(f"❌ Check failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        print(f"⏰ Completed at: {datetime.now()}")

if __name__ == "__main__":
    asyncio.run(main())
