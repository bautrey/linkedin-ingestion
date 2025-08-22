#!/usr/bin/env python3
"""
Apply profile_companies junction table migration to production Supabase database
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def apply_profile_companies_migration():
    """Apply the profile_companies junction table migration to production Supabase"""
    
    # Read the migration file
    migration_file = 'supabase/migrations/20250822180300_add_profile_company_junction.sql'
    with open(migration_file, 'r') as f:
        migration_sql = f.read()
    
    # Remove transaction statements and clean up the SQL
    statements = migration_sql.replace('BEGIN;', '').replace('COMMIT;', '').strip()
    
    # Split into individual SQL statements
    sql_statements = []
    current_statement = []
    
    for line in statements.split('\n'):
        line = line.strip()
        # Skip comments and empty lines
        if line.startswith('--') or not line:
            continue
            
        current_statement.append(line)
        
        # End statement on semicolon (but be careful about semicolons in strings/comments)
        if line.endswith(';'):
            full_statement = ' '.join(current_statement).strip()
            if full_statement:
                sql_statements.append(full_statement)
            current_statement = []
    
    # Add any remaining statement
    if current_statement:
        full_statement = ' '.join(current_statement).strip()
        if full_statement:
            sql_statements.append(full_statement)
    
    print(f"Found {len(sql_statements)} SQL statements to execute")
    for i, stmt in enumerate(sql_statements, 1):
        print(f"{i}. {stmt[:100]}{'...' if len(stmt) > 100 else ''}")
    
    # Supabase connection details
    supabase_url = os.getenv('SUPABASE_URL')
    service_key = os.getenv('SUPABASE_SERVICE_KEY')
    
    if not supabase_url or not service_key:
        print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_KEY environment variables")
        return False
    
    headers = {
        'apikey': service_key,
        'Authorization': f'Bearer {service_key}',
        'Content-Type': 'application/json',
        'Prefer': 'return=minimal'
    }
    
    # Execute each statement via Supabase REST API
    success_count = 0
    
    for i, statement in enumerate(sql_statements, 1):
        print(f"\n{i}. Executing: {statement[:80]}{'...' if len(statement) > 80 else ''}")
        
        try:
            response = requests.post(
                f"{supabase_url}/rest/v1/rpc/exec_sql",
                headers=headers,
                json={"query": statement}
            )
            
            if response.status_code in [200, 201]:
                print(f"   ✅ Success")
                success_count += 1
            else:
                print(f"   ❌ Failed: {response.status_code}")
                if response.text:
                    print(f"   Error: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
    
    print(f"\n📊 Migration Summary:")
    print(f"   Total statements: {len(sql_statements)}")
    print(f"   Successful: {success_count}")
    print(f"   Failed: {len(sql_statements) - success_count}")
    
    if success_count == len(sql_statements):
        print("\n🎉 Migration completed successfully!")
        return True
    else:
        print("\n⚠️  Migration partially completed. Check errors above.")
        return False

def verify_migration():
    """Verify that the profile_companies table and functions were created successfully"""
    
    supabase_url = os.getenv('SUPABASE_URL')
    service_key = os.getenv('SUPABASE_SERVICE_KEY')
    
    headers = {
        'apikey': service_key,
        'Authorization': f'Bearer {service_key}',
        'Content-Type': 'application/json'
    }
    
    # Try to query the profile_companies table
    try:
        print("\n🔍 Verifying profile_companies table...")
        response = requests.get(
            f"{supabase_url}/rest/v1/profile_companies?limit=1",
            headers=headers
        )
        
        if response.status_code == 200:
            print("✅ profile_companies table exists and is accessible")
        else:
            print(f"❌ profile_companies table check failed: {response.status_code} - {response.text}")
            return False
        
        # Test the SQL functions
        print("\n🔍 Testing get_profiles_for_company function...")
        response = requests.post(
            f"{supabase_url}/rest/v1/rpc/get_profiles_for_company",
            headers=headers,
            json={"target_company_id": "00000000-0000-0000-0000-000000000000"}  # Test with dummy UUID
        )
        
        if response.status_code == 200:
            print("✅ get_profiles_for_company function exists and works")
        else:
            print(f"❌ get_profiles_for_company function check failed: {response.status_code}")
            return False
        
        print("\n🔍 Testing get_companies_for_profile function...")
        response = requests.post(
            f"{supabase_url}/rest/v1/rpc/get_companies_for_profile",
            headers=headers,
            json={"target_profile_id": "00000000-0000-0000-0000-000000000000"}  # Test with dummy UUID
        )
        
        if response.status_code == 200:
            print("✅ get_companies_for_profile function exists and works")
            return True
        else:
            print(f"❌ get_companies_for_profile function check failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Verification exception: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Applying profile_companies migration to production...")
    print("=" * 60)
    
    migration_success = apply_profile_companies_migration()
    
    if migration_success:
        print("\n🔍 Verifying migration...")
        verification_success = verify_migration()
        
        if verification_success:
            print("\n🎉 Migration and verification completed successfully!")
            print("The profile_companies junction table is now ready for use.")
        else:
            print("\n⚠️  Migration completed but verification failed.")
    else:
        print("\n❌ Migration failed. Please check errors above.")
    
    print("\n" + "=" * 60)
    print("Migration process complete!")
