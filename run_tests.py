#!/usr/bin/env python3
"""
Test Runner for LinkedIn Ingestion Service

Simple script to run all tests with proper reporting.
All tests are now consolidated in app/tests/ directory.
"""

import sys
import subprocess
from pathlib import Path

def run_tests():
    """Run all tests with verbose output"""
    print("🧪 Running LinkedIn Ingestion Service Test Suite")
    print("=" * 60)
    
    # Ensure we're in the right directory
    project_root = Path(__file__).parent
    
    try:
        # Run tests with pytest
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "app/tests/",
            "-v",
            "--tb=short",
            "--durations=10"  # Show 10 slowest tests
        ], cwd=project_root, check=False)
        
        if result.returncode == 0:
            print("\n✅ All tests passed!")
            return True
        else:
            print(f"\n❌ Tests failed with return code: {result.returncode}")
            return False
            
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

def run_tests_quick():
    """Run all tests with minimal output"""
    print("🧪 Quick Test Run")
    print("-" * 30)
    
    project_root = Path(__file__).parent
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "app/tests/",
            "-q"
        ], cwd=project_root, check=False)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        success = run_tests_quick()
    else:
        success = run_tests()
    
    sys.exit(0 if success else 1)
