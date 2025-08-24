#!/usr/bin/env python3
"""
Production Database Cleanup: Remove Orphaned Profile-Company Relationships

This script connects directly to the production Supabase database and removes
profile-company relationship records where the referenced profile no longer exists.

Uses Railway environment variables for production database access.
"""

import asyncio
import os
import sys
from datetime import datetime
from typing import List, Dict, Any

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


async def find_orphaned_relationships() -> List[Dict[str, Any]]:
    """
    Find profile-company relationships where the profile doesn't exist in production
    
    Returns:
        List of orphaned relationship records
    """
    db_client = SupabaseClient()
    await db_client._ensure_client()
    
    print("🔍 Searching for orphaned relationships in PRODUCTION database...")
    print(f"🌐 Database URL: {PRODUCTION_SUPABASE_URL}")
    
    try:
        # Get all profile-company relationships with more detailed logging
        pc_table = db_client.client.table("profile_companies")
        relationships_result = await pc_table.select("*").execute()
        
        print(f"🔍 Relationships query result: {relationships_result}")
        
        if not relationships_result.data:
            print("✅ No profile-company relationships found")
            return []
        
        relationships = relationships_result.data
        print(f"📊 Found {len(relationships)} total profile-company relationships")
        
        # Show sample relationships for debugging
        print("\n📋 Sample relationships:")
        for i, rel in enumerate(relationships[:3]):
            print(f"  {i+1}. ID: {rel.get('id', 'N/A')}")
            print(f"     Profile: {rel.get('profile_id', 'N/A')}")
            print(f"     Company: {rel.get('company_id', 'N/A')}")
            print(f"     Position: {rel.get('job_title', 'N/A')}")
        
        # Get all existing profile IDs with more detailed logging
        profiles_table = db_client.client.table("linkedin_profiles")
        profiles_result = await profiles_table.select("id").execute()
        
        print(f"\n🔍 Profiles query result: {profiles_result}")
        
        existing_profile_ids = set()
        if profiles_result.data:
            existing_profile_ids = {p["id"] for p in profiles_result.data}
        
        print(f"📊 Found {len(existing_profile_ids)} existing profiles")
        
        # Show sample profile IDs for debugging
        print("\n📋 Sample profile IDs:")
        sample_ids = list(existing_profile_ids)[:3]
        for i, pid in enumerate(sample_ids):
            print(f"  {i+1}. {pid}")
        
        # Find orphaned relationships with detailed checking
        orphaned = []
        print("\n🔍 Checking each relationship for orphaned status...")
        
        for i, relationship in enumerate(relationships):
            profile_id = relationship["profile_id"]
            is_orphaned = profile_id not in existing_profile_ids
            
            if is_orphaned:
                orphaned.append(relationship)
                print(f"🚨 ORPHANED: Relationship {i+1} - Profile {profile_id} not found")
                print(f"    Company: {relationship['company_id']}")
                print(f"    Position: {relationship.get('job_title', 'N/A')}")
                print(f"    Relationship ID: {relationship['id']}")
            elif i < 5:  # Show first few valid ones for reference
                print(f"✅ VALID: Relationship {i+1} - Profile {profile_id} exists")
        
        print(f"\n🚨 Found {len(orphaned)} orphaned relationships")
        
        if orphaned:
            print("\n🔍 Orphaned relationships details:")
            for i, rel in enumerate(orphaned):
                print(f"  {i+1}. Relationship ID: {rel['id']}")
                print(f"      Profile ID: {rel['profile_id']} (MISSING)")
                print(f"      Company ID: {rel['company_id']}")
                print(f"      Position: {rel.get('job_title', 'N/A')}")
                print(f"      Created: {rel.get('created_at', 'N/A')}")
                print()
        
        return orphaned
        
    except Exception as e:
        print(f"❌ Error finding orphaned relationships: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


async def cleanup_orphaned_relationships(orphaned_relationships: List[Dict[str, Any]], confirm: bool = False) -> int:
    """
    Remove orphaned profile-company relationships from production
    
    Args:
        orphaned_relationships: List of orphaned relationship records
        confirm: If True, actually delete the records
        
    Returns:
        Number of relationships deleted
    """
    if not orphaned_relationships:
        print("✅ No orphaned relationships to clean up")
        return 0
    
    db_client = SupabaseClient()
    await db_client._ensure_client()
    
    if not confirm:
        print(f"🧪 DRY RUN: Would delete {len(orphaned_relationships)} orphaned relationships")
        print("   (Use confirm=True to actually delete)")
        return 0
    
    print(f"🧹 PRODUCTION CLEANUP: Deleting {len(orphaned_relationships)} orphaned relationships...")
    
    deleted_count = 0
    pc_table = db_client.client.table("profile_companies")
    
    for relationship in orphaned_relationships:
        try:
            # Delete by ID to be precise
            result = await pc_table.delete().eq("id", relationship["id"]).execute()
            
            if result.data and len(result.data) > 0:
                deleted_count += 1
                print(f"✅ Deleted orphaned relationship {relationship['id']}")
                print(f"    (Profile: {relationship['profile_id']}, Company: {relationship['company_id']})")
            else:
                print(f"⚠️ Relationship {relationship['id']} not found or already deleted")
                
        except Exception as e:
            print(f"❌ Failed to delete relationship {relationship['id']}: {str(e)}")
    
    print(f"🎉 Production cleanup complete: {deleted_count} orphaned relationships removed")
    return deleted_count


async def main():
    """Main cleanup function for production database"""
    print("🧹 PRODUCTION Orphaned Profile-Company Relationship Cleanup")
    print("=" * 60)
    print(f"⏰ Started at: {datetime.now()}")
    print(f"🌍 Environment: PRODUCTION")
    print(f"🗄️ Database: {PRODUCTION_SUPABASE_URL}")
    print()
    
    try:
        # Step 1: Find orphaned relationships in production
        orphaned = await find_orphaned_relationships()
        
        if not orphaned:
            print("✅ No cleanup needed - no orphaned relationships found in production")
            return
        
        print(f"\n⚠️ Found {len(orphaned)} orphaned profile-company relationships in PRODUCTION")
        print("These relationships reference profiles that no longer exist.")
        print("This is causing duplicate key constraint violations during profile re-ingestion.")
        print()
        
        # First show what would be deleted
        await cleanup_orphaned_relationships(orphaned, confirm=False)
        
        # Ask for confirmation
        print(f"\n❓ This will permanently delete {len(orphaned)} orphaned relationships from PRODUCTION.")
        response = input("❓ Are you sure you want to proceed? Type 'DELETE' to confirm: ").strip()
        
        if response == "DELETE":
            # Perform actual cleanup
            deleted_count = await cleanup_orphaned_relationships(orphaned, confirm=True)
            print(f"\n🎉 Production cleanup successful!")
            print(f"   Deleted: {deleted_count} orphaned relationships")
            print(f"   This should resolve duplicate key constraint violations.")
        else:
            print("❌ Cleanup cancelled - no changes made to production database")
    
    except Exception as e:
        print(f"❌ Production cleanup failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        print(f"⏰ Completed at: {datetime.now()}")


if __name__ == "__main__":
    asyncio.run(main())
