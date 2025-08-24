#!/usr/bin/env python3
"""
Cleanup Orphaned Profile-Company Relationships

This script identifies and removes profile-company relationship records
where the referenced profile no longer exists in the linkedin_profiles table.

This prevents duplicate key constraint violations when re-ingesting profiles.
"""

import asyncio
import os
import sys
from datetime import datetime
from typing import List, Dict, Any

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.supabase_client import SupabaseClient
from app.core.config import settings


async def find_orphaned_relationships() -> List[Dict[str, Any]]:
    """
    Find profile-company relationships where the profile doesn't exist
    
    Returns:
        List of orphaned relationship records
    """
    db_client = SupabaseClient()
    await db_client._ensure_client()
    
    print("🔍 Searching for orphaned profile-company relationships...")
    
    # Get all profile-company relationships
    pc_table = db_client.client.table("profile_companies")
    relationships_result = await pc_table.select("*").execute()
    
    if not relationships_result.data:
        print("✅ No profile-company relationships found")
        return []
    
    relationships = relationships_result.data
    print(f"📊 Found {len(relationships)} total profile-company relationships")
    
    # Get all existing profile IDs
    profiles_table = db_client.client.table("linkedin_profiles")
    profiles_result = await profiles_table.select("id").execute()
    
    existing_profile_ids = set()
    if profiles_result.data:
        existing_profile_ids = {p["id"] for p in profiles_result.data}
    
    print(f"📊 Found {len(existing_profile_ids)} existing profiles")
    
    # Find orphaned relationships
    orphaned = []
    for relationship in relationships:
        profile_id = relationship["profile_id"]
        if profile_id not in existing_profile_ids:
            orphaned.append(relationship)
    
    print(f"🚨 Found {len(orphaned)} orphaned relationships")
    
    if orphaned:
        print("\n🔍 Orphaned relationships details:")
        for rel in orphaned[:10]:  # Show first 10
            print(f"  - Profile ID: {rel['profile_id']}")
            print(f"    Company ID: {rel['company_id']}")
            print(f"    Position: {rel.get('job_title', 'N/A')}")
            print(f"    Created: {rel.get('created_at', 'N/A')}")
            print()
        
        if len(orphaned) > 10:
            print(f"    ... and {len(orphaned) - 10} more")
    
    return orphaned


async def cleanup_orphaned_relationships(orphaned_relationships: List[Dict[str, Any]], dry_run: bool = True) -> int:
    """
    Remove orphaned profile-company relationships
    
    Args:
        orphaned_relationships: List of orphaned relationship records
        dry_run: If True, only simulate the cleanup without making changes
        
    Returns:
        Number of relationships that would be/were deleted
    """
    if not orphaned_relationships:
        print("✅ No orphaned relationships to clean up")
        return 0
    
    db_client = SupabaseClient()
    await db_client._ensure_client()
    
    if dry_run:
        print(f"🧪 DRY RUN: Would delete {len(orphaned_relationships)} orphaned relationships")
        return len(orphaned_relationships)
    
    print(f"🧹 Cleaning up {len(orphaned_relationships)} orphaned relationships...")
    
    deleted_count = 0
    pc_table = db_client.client.table("profile_companies")
    
    for relationship in orphaned_relationships:
        try:
            # Delete by ID to be precise
            result = await pc_table.delete().eq("id", relationship["id"]).execute()
            
            if result.data and len(result.data) > 0:
                deleted_count += 1
                print(f"✅ Deleted relationship {relationship['id']} (Profile: {relationship['profile_id']})")
            else:
                print(f"⚠️ Relationship {relationship['id']} not found or already deleted")
                
        except Exception as e:
            print(f"❌ Failed to delete relationship {relationship['id']}: {str(e)}")
    
    print(f"🎉 Cleanup complete: {deleted_count} orphaned relationships removed")
    return deleted_count


async def verify_cleanup() -> None:
    """
    Verify that the cleanup was successful
    """
    print("\n🔍 Verifying cleanup...")
    
    orphaned_after = await find_orphaned_relationships()
    
    if not orphaned_after:
        print("✅ Verification successful: No orphaned relationships found")
    else:
        print(f"⚠️ Warning: {len(orphaned_after)} orphaned relationships still exist")


async def main():
    """Main cleanup function"""
    print("🧹 Orphaned Profile-Company Relationship Cleanup")
    print("=" * 50)
    print(f"⏰ Started at: {datetime.now()}")
    print(f"🌍 Environment: {settings.ENVIRONMENT}")
    print()
    
    try:
        # Step 1: Find orphaned relationships
        orphaned = await find_orphaned_relationships()
        
        if not orphaned:
            print("✅ No cleanup needed - no orphaned relationships found")
            return
        
        # Step 2: Ask for confirmation if not in dry-run mode
        print(f"\n⚠️ Found {len(orphaned)} orphaned profile-company relationships")
        print("These relationships reference profiles that no longer exist.")
        print()
        
        # First do a dry run
        await cleanup_orphaned_relationships(orphaned, dry_run=True)
        
        # Ask for confirmation
        response = input("\n❓ Do you want to proceed with the cleanup? (y/N): ").strip().lower()
        
        if response in ['y', 'yes']:
            # Step 3: Perform actual cleanup
            deleted_count = await cleanup_orphaned_relationships(orphaned, dry_run=False)
            
            # Step 4: Verify cleanup
            await verify_cleanup()
            
            print(f"\n🎉 Cleanup successful: {deleted_count} orphaned relationships removed")
        else:
            print("❌ Cleanup cancelled by user")
    
    except Exception as e:
        print(f"❌ Cleanup failed: {str(e)}")
        raise
    
    finally:
        print(f"⏰ Completed at: {datetime.now()}")


if __name__ == "__main__":
    asyncio.run(main())
