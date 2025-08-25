#!/usr/bin/env python3

import requests
import json
import time

# API details
base_url = "https://smooth-mailbox-production.up.railway.app/api/v1"
headers = {
    "x-api-key": "li_HieZz-IjBp0uE7d-rZkRE0qyy12r5_ZJS_FR4jMvv0I",
    "Content-Type": "application/json"
}

# Test profile ID (you may need to replace this with an actual profile ID from your database)
test_profile_id = "123e4567-e89b-12d3-a456-426614174000"

print("🧪 Testing Enhanced Scoring API with Role-Based Template Resolution")
print("=" * 70)

# Test 1: Role-based scoring (should use the CIO template we just created)
print("\n1️⃣ Testing role-based scoring with CIO role...")

role_based_payload = {
    "role": "CIO"  # This should automatically resolve to our CIO template
}

try:
    response = requests.post(
        f"{base_url}/profiles/{test_profile_id}/score-template",
        headers=headers,
        json=role_based_payload,
        timeout=30
    )
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 201:
        result = response.json()
        print("✅ Role-based scoring request successful!")
        print(f"Job ID: {result.get('job_id')}")
        print(f"Profile ID: {result.get('profile_id')}")
        print(f"Status: {result.get('status')}")
        job_id = result.get('job_id')
    else:
        print("❌ Role-based scoring failed")
        try:
            error_data = response.json()
            print("Error Response:")
            print(json.dumps(error_data, indent=2))
        except:
            print("Raw Response:")
            print(response.text)
        job_id = None

except requests.exceptions.RequestException as e:
    print(f"❌ Request failed: {e}")
    job_id = None

# Test 2: Check job status if we got a job ID
if job_id:
    print(f"\n2️⃣ Checking job status for {job_id}...")
    
    try:
        response = requests.get(
            f"{base_url}/scoring-jobs/{job_id}",
            headers=headers,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("✅ Job status retrieved successfully!")
            print(f"Status: {result.get('status')}")
            print(f"Created: {result.get('created_at')}")
            print(f"Updated: {result.get('updated_at')}")
            
            if result.get('status') == 'completed':
                print("Job completed! Results:")
                if result.get('result'):
                    print(f"Score: {result['result'].get('parsed_score')}")
                    print(f"Model: {result['result'].get('model_used')}")
                    print(f"Tokens: {result['result'].get('tokens_used')}")
                    
        else:
            print("❌ Failed to get job status")
            try:
                error_data = response.json()
                print("Error Response:")
                print(json.dumps(error_data, indent=2))
            except:
                print("Raw Response:")
                print(response.text)
                
    except requests.exceptions.RequestException as e:
        print(f"❌ Status check failed: {e}")

# Test 3: Template-based scoring (direct template ID)
print(f"\n3️⃣ Testing template-based scoring with specific template ID...")

template_based_payload = {
    "template_id": "04fa093b-172a-4b3a-8f69-2092e2b6c573"  # Our CIO template ID
}

try:
    response = requests.post(
        f"{base_url}/profiles/{test_profile_id}/score-template",
        headers=headers,
        json=template_based_payload,
        timeout=30
    )
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 201:
        result = response.json()
        print("✅ Template-based scoring request successful!")
        print(f"Job ID: {result.get('job_id')}")
        print(f"Profile ID: {result.get('profile_id')}")
        print(f"Status: {result.get('status')}")
    else:
        print("❌ Template-based scoring failed")
        try:
            error_data = response.json()
            print("Error Response:")
            print(json.dumps(error_data, indent=2))
        except:
            print("Raw Response:")
            print(response.text)

except requests.exceptions.RequestException as e:
    print(f"❌ Request failed: {e}")

# Test 4: Get templates for CIO role to verify our template is there
print(f"\n4️⃣ Verifying CIO templates are available...")

try:
    response = requests.get(
        f"{base_url}/templates?category=CIO",
        headers=headers,
        timeout=30
    )
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        templates = result.get('templates', [])
        print(f"✅ Found {len(templates)} CIO templates:")
        
        for template in templates:
            print(f"  - {template.get('name')} (ID: {template.get('id')})")
            print(f"    Active: {template.get('is_active')}")
            print(f"    Created: {template.get('created_at')}")
            print()
            
    else:
        print("❌ Failed to get templates")
        try:
            error_data = response.json()
            print("Error Response:")
            print(json.dumps(error_data, indent=2))
        except:
            print("Raw Response:")
            print(response.text)

except requests.exceptions.RequestException as e:
    print(f"❌ Request failed: {e}")

print("\n" + "=" * 70)
print("🧪 Enhanced Scoring API Test Complete!")
