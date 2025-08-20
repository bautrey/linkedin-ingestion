#!/usr/bin/env python3
"""
Script to run enhanced profile ingestion tests and save results to file
"""

import subprocess
import sys
from datetime import datetime

def run_tests():
    """Run the enhanced profile ingestion tests and save results"""
    
    print("Running enhanced profile ingestion tests...")
    
    # Run just our new tests
    cmd = [
        sys.executable, "-m", "pytest", 
        "tests/test_enhanced_profile_ingestion.py",
        "-v",
        "--tb=short",
        "--no-header"
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60  # 1 minute timeout
        )
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open("test_results.txt", "w") as f:
            f.write(f"Enhanced Profile Ingestion Test Results\n")
            f.write(f"Timestamp: {timestamp}\n")
            f.write("=" * 50 + "\n\n")
            
            f.write("STDOUT:\n")
            f.write(result.stdout)
            f.write("\n" + "=" * 50 + "\n\n")
            
            if result.stderr:
                f.write("STDERR:\n")
                f.write(result.stderr)
                f.write("\n" + "=" * 50 + "\n\n")
            
            f.write(f"Exit Code: {result.returncode}\n")
            
            if result.returncode == 0:
                f.write("✅ All tests passed!\n")
            else:
                f.write("❌ Some tests failed.\n")
        
        print(f"Test results saved to test_results.txt")
        print(f"Exit code: {result.returncode}")
        
        if result.returncode == 0:
            print("✅ All enhanced profile ingestion tests passed!")
        else:
            print("❌ Some tests failed. Check test_results.txt for details.")
            
    except subprocess.TimeoutExpired:
        print("❌ Tests timed out after 60 seconds")
        with open("test_results.txt", "w") as f:
            f.write(f"Test Results - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 50 + "\n")
            f.write("❌ Tests timed out after 60 seconds\n")
    
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        with open("test_results.txt", "w") as f:
            f.write(f"Test Results - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 50 + "\n")
            f.write(f"❌ Error running tests: {e}\n")

if __name__ == "__main__":
    run_tests()
