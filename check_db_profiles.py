#!/usr/bin/env python3
"""
Script to check how many profiles are in the database after testing
"""

import asyncio
from app.database import SupabaseClient
from app.core.config import settings

async def check_database():
    """Check the current state of the database"""
    
    print("🔍 Checking LinkedIn Ingestion Database")
    print("=" * 50)
    
    if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
        print("❌ No Supabase configuration found.")
        print("   Tests were likely using mock data only.")
        return
    
    print(f"📊 Database: {settings.SUPABASE_URL}")
    print()
    
    try:
        # Initialize client
        client = SupabaseClient()
        await client._ensure_client()
        
        # Count profiles
        print("📋 Counting LinkedIn profiles...")
        profile_result = await client.client.table("linkedin_profiles").select("id", count="exact").execute()
        profile_count = profile_result.count if hasattr(profile_result, 'count') else len(profile_result.data)
        
        print(f"   Total profiles in database: {profile_count}")
        
        # Count companies  
        print("🏢 Counting companies...")
        company_result = await client.client.table("companies").select("id", count="exact").execute()
        company_count = company_result.count if hasattr(company_result, 'count') else len(company_result.data)
        
        print(f"   Total companies in database: {company_count}")
        
        print()
        print("🔍 Recent test profiles (last 10):")
        
        # Get recent profiles that look like test data
        recent_profiles = await client.client.table("linkedin_profiles").select(
            "linkedin_id, name, created_at"
        ).order("created_at", desc=True).limit(10).execute()
        
        test_profile_count = 0
        for profile in recent_profiles.data:
            linkedin_id = profile.get('linkedin_id', '')
            name = profile.get('name', '')
            created_at = profile.get('created_at', '')
            
            # Check if this looks like a test profile
            is_test = any([
                'test-' in linkedin_id.lower(),
                'mock-' in linkedin_id.lower(),
                'retrieval-test' in linkedin_id.lower(),
                'test' in name.lower() and ('user' in name.lower() or 'profile' in name.lower()),
                'john doe' in name.lower(),
                'jane smith' in name.lower()
            ])
            
            if is_test:
                test_profile_count += 1
                print(f"   🧪 {name} ({linkedin_id}) - {created_at}")
            else:
                print(f"   👤 {name} ({linkedin_id}) - {created_at}")
        
        print()
        print("🔍 Recent test companies (last 10):")
        
        # Get recent companies that look like test data
        recent_companies = await client.client.table("companies").select(
            "linkedin_company_id, company_name, created_at"
        ).order("created_at", desc=True).limit(10).execute()
        
        test_company_count = 0
        for company in recent_companies.data:
            company_id = company.get('linkedin_company_id', '')
            company_name = company.get('company_name', '')
            created_at = company.get('created_at', '')
            
            # Check if this looks like a test company
            is_test = any([
                'test-' in company_id.lower(),
                'mock-' in company_id.lower(),
                'test' in company_name.lower() and 'corp' in company_name.lower(),
                'mock company' in company_name.lower(),
                'techcorp' in company_name.lower()
            ])
            
            if is_test:
                test_company_count += 1
                print(f"   🧪 {company_name} ({company_id}) - {created_at}")
            else:
                print(f"   🏢 {company_name} ({company_id}) - {created_at}")
        
        print()
        print("📊 Summary:")
        print(f"   • Total profiles in database: {profile_count}")
        print(f"   • Total companies in database: {company_count}")
        print(f"   • Test profiles identified: {test_profile_count}")
        print(f"   • Test companies identified: {test_company_count}")
        
        if test_profile_count > 0 or test_company_count > 0:
            print()
            print("💡 Test data was written to the real database during testing.")
            print("   This suggests some tests bypassed mocking and used actual Supabase.")
            print("   The test data should be safe to leave as it uses test identifiers.")
        else:
            print()
            print("✅ No obvious test data found in recent records.")
            print("   Either tests used mocks successfully or test data is older.")
        
    except Exception as e:
        print(f"❌ Error accessing database: {e}")
        print(f"   Error type: {type(e).__name__}")
        print()
        print("This could mean:")
        print("   • Database connection is not configured")
        print("   • Tests used mock data successfully")
        print("   • Database credentials are invalid")

if __name__ == "__main__":
    asyncio.run(check_database())
