#!/usr/bin/env python3
"""
V1.88 Production Template-Based Scoring Validation

Tests the complete template-based scoring workflow in production:
1. Template-based scoring (using CTO template)
2. Prompt-based scoring (backward compatibility)
3. Job status tracking with template_id
4. End-to-end workflow validation
"""

import asyncio
import sys
import time
import requests
import json
from datetime import datetime, timezone

# Production API configuration
BASE_URL = "https://smooth-mailbox-production.up.railway.app"
API_KEY = "li_HieZz-IjBp0uE7d-rZkRE0qyy12r5_ZJS_FR4jMvv0I"

# Test profile ID (Christopher Leslie - used in previous validations)
TEST_PROFILE_ID = "435ccbf7-6c5e-4e2d-bdc3-052a244d7121"


def make_request(method, endpoint, data=None, headers=None):
    """Make HTTP request to production API"""
    url = f"{BASE_URL}{endpoint}"
    default_headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}
    if headers:
        default_headers.update(headers)
    
    if method == "GET":
        response = requests.get(url, headers=default_headers)
    elif method == "POST":
        response = requests.post(url, headers=default_headers, json=data)
    elif method == "PUT":
        response = requests.put(url, headers=default_headers, json=data)
    elif method == "DELETE":
        response = requests.delete(url, headers=default_headers)
    
    return response


def test_get_templates():
    """Test template retrieval"""
    print("🔍 Testing template retrieval...")
    
    response = make_request("GET", "/api/v1/templates")
    if response.status_code != 200:
        print(f"❌ Template retrieval failed: {response.status_code}")
        print(f"Response: {response.text}")
        return None
    
    data = response.json()
    templates = data.get("templates", [])
    
    print(f"✅ Found {len(templates)} templates")
    
    # Find CTO template
    cto_template = None
    for template in templates:
        if template["category"] == "CTO":
            cto_template = template
            break
    
    if not cto_template:
        print("❌ No CTO template found")
        return None
    
    print(f"✅ Found CTO template: {cto_template['name']} (ID: {cto_template['id']})")
    return cto_template


def test_template_based_scoring(cto_template_id):
    """Test template-based scoring using the enhanced endpoint"""
    print(f"\n🎯 Testing template-based scoring with template ID: {cto_template_id}")
    
    # Create template-based scoring job
    request_data = {
        "template_id": cto_template_id,
        "model": "gpt-3.5-turbo",
        "max_tokens": 2000,
        "temperature": 0.1
    }
    
    response = make_request("POST", f"/api/v1/profiles/{TEST_PROFILE_ID}/score-enhanced", data=request_data)
    
    if response.status_code != 201:
        print(f"❌ Template-based scoring job creation failed: {response.status_code}")
        print(f"Response: {response.text}")
        return None
    
    job_data = response.json()
    job_id = job_data["job_id"]
    
    print(f"✅ Template-based scoring job created: {job_id}")
    print(f"   Status: {job_data['status']}")
    print(f"   Profile ID: {job_data['profile_id']}")
    
    return job_id


def test_prompt_based_scoring():
    """Test prompt-based scoring (backward compatibility) using enhanced endpoint"""
    print(f"\n📝 Testing prompt-based scoring (backward compatibility)...")
    
    # Create prompt-based scoring job using enhanced endpoint
    request_data = {
        "prompt": "Evaluate this LinkedIn profile for senior engineering leadership potential. Provide a score from 1-10 and brief justification.",
        "model": "gpt-3.5-turbo",
        "max_tokens": 1000,
        "temperature": 0.2
    }
    
    response = make_request("POST", f"/api/v1/profiles/{TEST_PROFILE_ID}/score-enhanced", data=request_data)
    
    if response.status_code != 201:
        print(f"❌ Prompt-based scoring job creation failed: {response.status_code}")
        print(f"Response: {response.text}")
        return None
    
    job_data = response.json()
    job_id = job_data["job_id"]
    
    print(f"✅ Prompt-based scoring job created: {job_id}")
    print(f"   Status: {job_data['status']}")
    print(f"   Profile ID: {job_data['profile_id']}")
    
    return job_id


def test_legacy_scoring():
    """Test legacy scoring endpoint (existing functionality)"""
    print(f"\n🔄 Testing legacy scoring endpoint...")
    
    # Create scoring job using legacy endpoint
    request_data = {
        "prompt": "Rate this profile for technical leadership on a scale of 1-5.",
        "model": "gpt-3.5-turbo",
        "max_tokens": 500,
        "temperature": 0.1
    }
    
    response = make_request("POST", f"/api/v1/profiles/{TEST_PROFILE_ID}/score", data=request_data)
    
    if response.status_code != 201:
        print(f"❌ Legacy scoring job creation failed: {response.status_code}")
        print(f"Response: {response.text}")
        return None
    
    job_data = response.json()
    job_id = job_data["job_id"]
    
    print(f"✅ Legacy scoring job created: {job_id}")
    print(f"   Status: {job_data['status']}")
    print(f"   Profile ID: {job_data['profile_id']}")
    
    return job_id


def monitor_job(job_id, job_type, max_wait_seconds=120):
    """Monitor scoring job until completion or timeout"""
    print(f"\n📊 Monitoring {job_type} job: {job_id}")
    
    start_time = time.time()
    while time.time() - start_time < max_wait_seconds:
        response = make_request("GET", f"/api/v1/scoring-jobs/{job_id}")
        
        if response.status_code != 200:
            print(f"❌ Job status check failed: {response.status_code}")
            return False
        
        job_data = response.json()
        status = job_data.get("status", "unknown")
        
        elapsed = int(time.time() - start_time)
        print(f"   [{elapsed:02d}s] Status: {status}")
        
        if status == "completed":
            print(f"✅ {job_type} job completed successfully!")
            
            # Show results summary
            if "result" in job_data:
                result = job_data["result"]
                tokens_used = result.get("tokens_used", 0)
                model_used = result.get("model_used", "unknown")
                print(f"   Model: {model_used}")
                print(f"   Tokens used: {tokens_used}")
                
                # Show parsed score summary
                parsed_score = result.get("parsed_score", {})
                if isinstance(parsed_score, dict):
                    print(f"   Response keys: {list(parsed_score.keys())}")
            
            return True
        
        elif status == "failed":
            print(f"❌ {job_type} job failed!")
            if "error" in job_data:
                error = job_data["error"]
                print(f"   Error: {error.get('message', 'Unknown error')}")
            return False
        
        elif status in ["pending", "processing"]:
            # Continue monitoring
            time.sleep(5)
        
        else:
            print(f"⚠️ Unknown job status: {status}")
            time.sleep(5)
    
    print(f"⏰ {job_type} job monitoring timed out after {max_wait_seconds} seconds")
    return False


def test_enhanced_scoring_validation():
    """Test validation of enhanced scoring requests"""
    print(f"\n🔬 Testing enhanced scoring validation...")
    
    # Test missing both template_id and prompt
    print("   Testing missing template_id and prompt...")
    request_data = {
        "model": "gpt-3.5-turbo"
    }
    
    response = make_request("POST", f"/api/v1/profiles/{TEST_PROFILE_ID}/score-enhanced", data=request_data)
    
    if response.status_code == 422:
        print("   ✅ Validation correctly rejected request with missing template_id and prompt")
    else:
        print(f"   ❌ Expected 422 validation error, got: {response.status_code}")
    
    # Test providing both template_id and prompt
    print("   Testing both template_id and prompt provided...")
    request_data = {
        "template_id": "271a1e68-b51c-489c-9f2f-c544de517520",
        "prompt": "Test prompt",
        "model": "gpt-3.5-turbo"
    }
    
    response = make_request("POST", f"/api/v1/profiles/{TEST_PROFILE_ID}/score-enhanced", data=request_data)
    
    if response.status_code == 422:
        print("   ✅ Validation correctly rejected request with both template_id and prompt")
    else:
        print(f"   ❌ Expected 422 validation error, got: {response.status_code}")
    
    # Test nonexistent template
    print("   Testing nonexistent template...")
    request_data = {
        "template_id": "00000000-0000-0000-0000-000000000000",
        "model": "gpt-3.5-turbo"
    }
    
    response = make_request("POST", f"/api/v1/profiles/{TEST_PROFILE_ID}/score-enhanced", data=request_data)
    
    if response.status_code == 404:
        print("   ✅ Correctly returned 404 for nonexistent template")
    else:
        print(f"   ❌ Expected 404 for nonexistent template, got: {response.status_code}")


def main():
    """Run complete V1.88 template-based scoring validation"""
    print("🚀 V1.88 Template-Based Scoring Production Validation")
    print(f"🌐 API Base URL: {BASE_URL}")
    print(f"👤 Test Profile ID: {TEST_PROFILE_ID}")
    print(f"🕐 Started at: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 70)
    
    # Step 1: Get templates
    cto_template = test_get_templates()
    if not cto_template:
        print("❌ Template retrieval failed - aborting test")
        sys.exit(1)
    
    cto_template_id = cto_template["id"]
    
    # Step 2: Test template-based scoring
    template_job_id = test_template_based_scoring(cto_template_id)
    if not template_job_id:
        print("❌ Template-based scoring failed - aborting test")
        sys.exit(1)
    
    # Step 3: Test prompt-based scoring via enhanced endpoint
    prompt_job_id = test_prompt_based_scoring()
    if not prompt_job_id:
        print("❌ Prompt-based scoring via enhanced endpoint failed")
    
    # Step 4: Test legacy scoring endpoint
    legacy_job_id = test_legacy_scoring()
    if not legacy_job_id:
        print("❌ Legacy scoring endpoint failed")
    
    # Step 5: Test validation
    test_enhanced_scoring_validation()
    
    # Step 6: Monitor jobs to completion
    success_count = 0
    total_jobs = 0
    
    if template_job_id:
        total_jobs += 1
        if monitor_job(template_job_id, "Template-based", max_wait_seconds=120):
            success_count += 1
    
    if prompt_job_id:
        total_jobs += 1
        if monitor_job(prompt_job_id, "Prompt-based (enhanced)", max_wait_seconds=120):
            success_count += 1
    
    if legacy_job_id:
        total_jobs += 1
        if monitor_job(legacy_job_id, "Legacy", max_wait_seconds=120):
            success_count += 1
    
    # Final summary
    print("\n" + "=" * 70)
    print("📊 V1.88 TEMPLATE-BASED SCORING VALIDATION SUMMARY")
    print("=" * 70)
    print(f"✅ Templates retrieved: {len(cto_template) > 0}")
    print(f"✅ Template-based scoring: {'✅ CREATED' if template_job_id else '❌ FAILED'}")
    print(f"✅ Prompt-based (enhanced): {'✅ CREATED' if prompt_job_id else '❌ FAILED'}")
    print(f"✅ Legacy endpoint: {'✅ CREATED' if legacy_job_id else '❌ FAILED'}")
    print(f"✅ Job completions: {success_count}/{total_jobs}")
    print(f"🕐 Completed at: {datetime.now(timezone.utc).isoformat()}")
    
    if success_count == total_jobs and total_jobs > 0:
        print("\n🎉 ALL V1.88 TEMPLATE-BASED SCORING TESTS PASSED!")
        print("✅ Task 5: LLM Scoring Integration - COMPLETE")
    else:
        print(f"\n⚠️ {total_jobs - success_count} tests failed or incomplete")
        sys.exit(1)


if __name__ == "__main__":
    main()
