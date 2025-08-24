#!/usr/bin/env python3
"""
Remove CASCADE Constraints from Production Database

This script removes ON DELETE CASCADE constraints from the profile_companies table
in the production database, so all deletion logic is handled in application code.
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

async def remove_cascade_constraints():
    """Remove CASCADE constraints from profile_companies table"""
    
    db_client = SupabaseClient()
    await db_client._ensure_client()
    
    print("🔧 Removing CASCADE constraints from profile_companies table...")
    print(f"🌐 Database URL: {PRODUCTION_SUPABASE_URL}")
    
    # SQL to remove CASCADE constraints
    migration_sql = """
    -- Remove CASCADE constraints from profile_companies table
    -- All deletion logic should be handled in application code for better debugging visibility

    -- Drop existing foreign key constraints
    ALTER TABLE profile_companies 
    DROP CONSTRAINT IF EXISTS profile_companies_profile_id_fkey;

    ALTER TABLE profile_companies 
    DROP CONSTRAINT IF EXISTS profile_companies_company_id_fkey;

    -- Re-add foreign key constraints WITHOUT CASCADE
    ALTER TABLE profile_companies 
    ADD CONSTRAINT profile_companies_profile_id_fkey 
    FOREIGN KEY (profile_id) REFERENCES linkedin_profiles(id);

    ALTER TABLE profile_companies 
    ADD CONSTRAINT profile_companies_company_id_fkey 
    FOREIGN KEY (company_id) REFERENCES companies(id);
    """
    
    try:
        # Execute the migration
        result = await db_client.client.rpc("execute_sql", {"sql": migration_sql}).execute()
        
        print("✅ CASCADE constraints removed successfully")
        print("   - profile_companies foreign keys no longer have ON DELETE CASCADE")
        print("   - All deletion logic will now be handled in application code")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to remove CASCADE constraints: {str(e)}")
        print("Note: This might fail if Supabase doesn't allow direct SQL execution")
        print("You may need to apply this migration manually in the Supabase dashboard")
        return False

async def main():
    print("🔧 Remove CASCADE Constraints from Production")
    print("=" * 45)
    print(f"⏰ Started at: {datetime.now()}")
    print(f"🌍 Environment: PRODUCTION")
    print()
    
    try:
        success = await remove_cascade_constraints()
        if success:
            print("\\n🎉 CASCADE constraints removed successfully!")
        else:
            print("\\n⚠️ You may need to apply the migration manually")
            
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        print(f"⏰ Completed at: {datetime.now()}")

if __name__ == "__main__":
    asyncio.run(main())
