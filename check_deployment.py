#!/usr/bin/env python3
"""
Quick check to see if the Railway deployment is accessible
"""

import requests
import json
from datetime import datetime

def check_deployment():
    """Check if deployment is accessible"""
    base_url = "https://linkedin-ingestion-production.up.railway.app"
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "base_url": base_url,
        "checks": []
    }
    
    # Test 1: Root endpoint
    root_check = {
        "name": "Root endpoint check",
        "url": f"{base_url}/",
        "description": "Basic connectivity test"
    }
    
    try:
        response = requests.get(root_check["url"], timeout=10)
        root_check["status_code"] = response.status_code
        root_check["response"] = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
        root_check["success"] = response.status_code == 200
    except requests.exceptions.RequestException as e:
        root_check["error"] = str(e)
        root_check["success"] = False
    
    results["checks"].append(root_check)
    
    # Test 2: Health endpoint
    health_check = {
        "name": "Health endpoint check", 
        "url": f"{base_url}/api/v1/health",
        "description": "Application health check"
    }
    
    try:
        response = requests.get(health_check["url"], timeout=10)
        health_check["status_code"] = response.status_code
        health_check["response"] = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
        health_check["success"] = response.status_code == 200
    except requests.exceptions.RequestException as e:
        health_check["error"] = str(e)
        health_check["success"] = False
    
    results["checks"].append(health_check)
    
    return results

if __name__ == "__main__":
    print("Checking deployment status...")
    results = check_deployment()
    
    # Write results to file
    with open("deployment_check_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    success_count = sum(1 for check in results["checks"] if check["success"])
    total_checks = len(results["checks"])
    
    print(f"\n✅ Deployment Check Results:")
    print(f"   Successful checks: {success_count}/{total_checks}")
    
    for check in results["checks"]:
        status = "✅" if check["success"] else "❌"
        print(f"   {status} {check['name']}")
        if not check["success"] and "error" in check:
            print(f"      Error: {check['error']}")
    
    print(f"\n📝 Full results written to: deployment_check_results.json")
    
    if success_count == total_checks:
        print("🎉 Deployment is accessible!")
    else:
        print("❌ Deployment has issues - check the logs or Railway dashboard")
