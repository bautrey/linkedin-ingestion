#!/usr/bin/env python3
"""
Database Verification Script

Verifies that the local Supabase database is properly set up with all required tables,
indexes, and test data for running the LinkedIn ingestion test suite.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the project directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.database.supabase_client import SupabaseClient
from app.services.template_service import TemplateService

async def verify_database():
    """Verify database setup and return status report."""
    client = None
    try:
        print("🔍 Verifying database setup...")
        
        # Initialize client
        client = SupabaseClient()
        await client._ensure_client()
        
        # Check database connection
        print("✅ Database connection: OK")
        
        # Check required tables exist
        required_tables = [
            "linkedin_profiles",
            "prompt_templates", 
            "scoring_jobs",
            "companies"
        ]
        
        for table in required_tables:
            try:
                result = await client.client.table(table).select("*").limit(1).execute()
                print(f"✅ Table '{table}': EXISTS")
            except Exception as e:
                print(f"❌ Table '{table}': MISSING - {e}")
                return False
        
        # Check template service functionality
        template_service = TemplateService(client)
        templates = await template_service.list_templates()
        
        if len(templates) >= 3:
            categories = {t.category for t in templates}
            expected_categories = {"CTO", "CIO", "CISO"}
            
            if expected_categories.issubset(categories):
                print(f"✅ Template service: OK ({len(templates)} templates with categories: {sorted(categories)})")
            else:
                print(f"❌ Template service: Missing expected categories. Found: {categories}")
                return False
        else:
            print(f"❌ Template service: Expected >= 3 templates, found {len(templates)}")
            return False
        
        # Check if test profile exists
        try:
            test_profile_id = "435ccbf7-6c5e-4e2d-bdc3-052a244d7121"
            profile = await client.get_profile_by_id(test_profile_id)
            if profile:
                print("✅ Test profile: EXISTS (for integration tests)")
            else:
                print("⚠️  Test profile: MISSING (integration tests may fail)")
        except Exception as e:
            print(f"⚠️  Test profile check failed: {e}")
        
        print("\n🎉 Database verification successful!")
        print("\n📋 Summary:")
        print("   - All required tables exist")
        print("   - Template service is functional")
        print("   - Default templates are loaded")
        print("   - Database is ready for testing")
        
        return True
        
    except Exception as e:
        print(f"❌ Database verification failed: {e}")
        return False
    
    finally:
        # Client cleanup handled by supabase-py
        pass

async def setup_test_data():
    """Set up required test data if missing."""
    client = None
    try:
        print("\n🔧 Setting up test data...")
        
        client = SupabaseClient()
        await client._ensure_client()
        
        # Insert test profile if it doesn't exist
        test_profile_id = "435ccbf7-6c5e-4e2d-bdc3-052a244d7121"
        
        try:
            existing = await client.get_profile_by_id(test_profile_id)
            if not existing:
                test_profile_data = {
                    "id": test_profile_id,
                    "linkedin_id": "christopher-leslie", 
                    "name": "Christopher Leslie",
                    "url": "https://www.linkedin.com/in/christopher-leslie/",
                    "position": "Senior Software Engineer",
                    "about": "Experienced software engineer with expertise in Python, TypeScript, and cloud technologies.",
                    "city": "San Francisco",
                    "country_code": "US",
                    "experience": [{"title": "Senior Software Engineer", "company": "Tech Corp", "duration": "2020-present"}],
                    "education": [{"degree": "BS Computer Science", "school": "Stanford University", "year": "2018"}]
                }
                
                await client.store_profile(test_profile_data)
                print("✅ Test profile created")
            else:
                print("✅ Test profile already exists")
                
        except Exception as e:
            print(f"⚠️  Could not set up test profile: {e}")
        
    except Exception as e:
        print(f"❌ Test data setup failed: {e}")
    
    finally:
        # Client cleanup handled by supabase-py
        pass

def main():
    """Main entry point."""
    if len(sys.argv) > 1 and sys.argv[1] == "--setup":
        print("🚀 Database Setup Mode")
        asyncio.run(setup_test_data())
    
    print("🚀 Database Verification")
    success = asyncio.run(verify_database())
    
    if not success:
        print("\n💡 To fix database issues:")
        print("   1. Ensure Supabase is running: `supabase status`")
        print("   2. Reset database: `supabase db reset`") 
        print("   3. Run setup: `python scripts/verify_database.py --setup`")
        sys.exit(1)
    
    print("\n🎯 Ready to run tests:")
    print("   Unit/Integration: `pytest`")
    print("   Production tests: `RUN_PRODUCTION_TESTS=true pytest -m production`")

if __name__ == "__main__":
    main()
