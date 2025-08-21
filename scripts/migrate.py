#!/usr/bin/env python3
"""
Simple migration check script for Railway deployment

Since we're using Supabase (not local database migrations), this script
just performs basic validation checks during deployment.

Usage:
    python scripts/migrate.py [--check-only]

The --check-only flag makes this safe to run during Railway build process.
"""

import argparse
import sys
import os
from pathlib import Path


def check_environment_variables():
    """Check that required environment variables are available"""
    required_vars = [
        'SUPABASE_URL',
        'SUPABASE_ANON_KEY', 
        'SUPABASE_SERVICE_KEY',
        'API_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️  Missing environment variables: {', '.join(missing_vars)}")
        print("💡 These should be set in Railway dashboard")
        return False
    
    print(f"✅ All required environment variables are set")
    return True


def check_project_structure():
    """Verify key project files exist"""
    required_files = [
        'main.py',
        'requirements.txt',
        'app/core/config.py',
        'app/database/supabase_client.py'
    ]
    
    project_root = Path(__file__).parent.parent
    missing_files = []
    
    for file_path in required_files:
        full_path = project_root / file_path
        if not full_path.exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing required files: {', '.join(missing_files)}")
        return False
    
    print(f"✅ All required project files exist")
    return True


def check_dependencies():
    """Basic check that key dependencies are importable"""
    try:
        import fastapi
        import uvicorn
        import pydantic
        import supabase
        print(f"✅ Key dependencies are importable")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        return False


def main():
    """Main migration check function"""
    parser = argparse.ArgumentParser(description="Migration check for Railway deployment")
    parser.add_argument("--check-only", action="store_true", 
                       help="Only perform checks, don't run actual migrations")
    
    args = parser.parse_args()
    
    print(f"🔍 Running migration checks...")
    
    checks = [
        ("Project structure", check_project_structure),
        ("Dependencies", check_dependencies),
        ("Environment variables", check_environment_variables),
    ]
    
    all_passed = True
    
    for check_name, check_func in checks:
        print(f"\n📋 Checking {check_name}...")
        try:
            if not check_func():
                all_passed = False
                print(f"❌ {check_name} check failed")
            else:
                print(f"✅ {check_name} check passed")
        except Exception as e:
            print(f"❌ {check_name} check failed with error: {e}")
            all_passed = False
    
    if args.check_only:
        print(f"\n🔍 Check-only mode completed")
        if all_passed:
            print(f"✅ All checks passed - deployment should succeed")
            sys.exit(0)
        else:
            print(f"⚠️  Some checks failed - deployment may have issues")
            sys.exit(1)
    
    # If not check-only mode, we'd run actual migrations here
    # But since we use Supabase, we don't have local migrations to run
    print(f"\n🏗️  Using Supabase - no local migrations to run")
    
    if all_passed:
        print(f"✅ Migration check completed successfully")
        sys.exit(0)
    else:
        print(f"❌ Migration check failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
