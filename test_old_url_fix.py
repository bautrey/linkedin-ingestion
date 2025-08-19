#!/usr/bin/env python3
"""
Test script to verify that old LinkedIn URL formats now return 400 instead of 500
"""

import requests
import json
import os
from datetime import datetime

# Load API key from .env or use default
def load_api_key():
    """Load API key from .env file or use default from config"""
    try:
        with open('.env', 'r') as f:
            for line in f:
                if line.strip().startswith('API_KEY='):
                    return line.strip().split('=', 1)[1].strip('"\'')
    except FileNotFoundError:
        pass
    
    # Fallback to the default key from config.py
    return "li_HieZz-IjBp0uE7d-rZkRE0qyy12r5_ZJS_FR4jMvv0I"

def test_linkedin_url_error_handling():
    """Test both old and new LinkedIn URL formats"""
    
    # Get API key
    api_key = load_api_key()
    if not api_key:
        return {"error": "Could not load API key"}
    
    # Determine the base URL (Railway deployment - correct URL from deployment guide)
    base_url = "https://smooth-mailbox-production.up.railway.app"
    
    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json"
    }
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "base_url": base_url,
        "tests": []
    }
    
    # Test 1: Old LinkedIn URL format (should return 400)
    old_url_test = {
        "name": "Old LinkedIn URL Format Test",
        "url": "https://www.linkedin.com/pub/richard-harris/8/946/143",
        "expected_status": 400,
        "description": "Should return 400 Bad Request with helpful error message"
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/v1/profiles",
            headers=headers,
            json={
                "linkedin_url": old_url_test["url"],
                "suggested_role": "CIO",
                "include_companies": True
            },
            timeout=30
        )
        
        old_url_test["actual_status"] = response.status_code
        old_url_test["response_body"] = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
        old_url_test["success"] = response.status_code == 400
        
    except requests.exceptions.RequestException as e:
        old_url_test["actual_status"] = "ERROR"
        old_url_test["error"] = str(e)
        old_url_test["success"] = False
    
    results["tests"].append(old_url_test)
    
    # Test 2: Modern LinkedIn URL format (should work - 201)
    modern_url_test = {
        "name": "Modern LinkedIn URL Format Test",
        "url": "https://www.linkedin.com/in/richard-harris",
        "expected_status": 201,
        "description": "Should successfully process and return 201 Created"
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/v1/profiles",
            headers=headers,
            json={
                "linkedin_url": modern_url_test["url"],
                "suggested_role": "CIO", 
                "include_companies": True
            },
            timeout=30
        )
        
        modern_url_test["actual_status"] = response.status_code
        modern_url_test["response_body"] = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
        modern_url_test["success"] = response.status_code == 201
        
    except requests.exceptions.RequestException as e:
        modern_url_test["actual_status"] = "ERROR"
        modern_url_test["error"] = str(e)
        modern_url_test["success"] = False
    
    results["tests"].append(modern_url_test)
    
    # Summary
    results["summary"] = {
        "total_tests": len(results["tests"]),
        "passed": sum(1 for test in results["tests"] if test["success"]),
        "failed": sum(1 for test in results["tests"] if not test["success"]),
        "fix_working": old_url_test["success"]  # Main indicator if the fix works
    }
    
    return results

if __name__ == "__main__":
    print("Testing LinkedIn URL error handling fix...")
    results = test_linkedin_url_error_handling()
    
    # Write results to file
    with open("url_fix_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    # Check if we got an error result
    if "error" in results:
        print(f"❌ ERROR: {results['error']}")
        print(f"📝 Error details written to: url_fix_test_results.json")
    else:
        # Print summary
        print(f"\n✅ Test Results Summary:")
        print(f"   Tests run: {results['summary']['total_tests']}")
        print(f"   Passed: {results['summary']['passed']}")
        print(f"   Failed: {results['summary']['failed']}")
        print(f"   Fix working: {'YES' if results['summary']['fix_working'] else 'NO'}")
        print(f"\n📝 Full results written to: url_fix_test_results.json")
        
        if results["summary"]["fix_working"]:
            print("🎉 SUCCESS: Old LinkedIn URLs now return 400 instead of 500!")
        else:
            print("❌ ISSUE: Old LinkedIn URLs still causing problems")
            print("   Check url_fix_test_results.json for details")
