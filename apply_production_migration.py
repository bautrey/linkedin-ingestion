#!/usr/bin/env python3
"""
Apply V1.85 scoring_jobs table migration to production Supabase database
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def apply_scoring_jobs_migration():
    """Apply the scoring jobs table migration to production Supabase"""
    
    # Read the migration file
    with open('app/database/migrations/v185_add_scoring_jobs_table.sql', 'r') as f:
        migration_sql = f.read()
    
    # Remove transaction statements since we'll execute each statement individually
    statements = migration_sql.replace('BEGIN;', '').replace('COMMIT;', '').strip()
    
    # Split into individual SQL statements (more carefully this time)
    sql_statements = []
    current_statement = []
    
    for line in statements.split('\n'):
        line = line.strip()
        if line.startswith('--') or not line:
            continue
            
        current_statement.append(line)
        
        # End statement on semicolon (but be careful about semicolons in strings/comments)
        if line.endswith(';'):
            full_statement = ' '.join(current_statement).strip()
            if full_statement:
                sql_statements.append(full_statement)
            current_statement = []
    
    print(f"Found {len(sql_statements)} SQL statements to execute")
    
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
    """Verify that the scoring_jobs table was created successfully"""
    
    supabase_url = os.getenv('SUPABASE_URL')
    service_key = os.getenv('SUPABASE_SERVICE_KEY')
    
    headers = {
        'apikey': service_key,
        'Authorization': f'Bearer {service_key}',
        'Content-Type': 'application/json'
    }
    
    # Try to query the scoring_jobs table
    try:
        response = requests.get(
            f"{supabase_url}/rest/v1/scoring_jobs?limit=1",
            headers=headers
        )
        
        if response.status_code == 200:
            print("✅ Verification successful: scoring_jobs table exists and is accessible")
            return True
        else:
            print(f"❌ Verification failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Verification exception: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Applying V1.85 scoring_jobs migration to production...")
    print("=" * 60)
    
    migration_success = apply_scoring_jobs_migration()
    
    if migration_success:
        print("\n🔍 Verifying migration...")
        verify_migration()
    
    print("\n" + "=" * 60)
    print("Migration process complete!")
