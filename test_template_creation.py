#!/usr/bin/env python3

import requests
import json

# Your new template content
template_content = """Candidate Data:
{{profile_data}}

STEP 1 — GATEKEEPER FILTER (Pass/Fail)
A candidate MUST have held at least one role that meets ALL of these:
- Exact or equivalent title of CIO
- Top accountable technology executive in the company
- Reported to CEO or another non-technology executive (e.g., COO, CFO)
- Enterprise-wide scope (not just a business unit unless that BU was the enterprise)
- Direct employee (not only consultant, contractor, advisor)

If NO qualifying role exists:
- Output: Gatekeeper Fail — No qualifying CIO role
- Do NOT proceed to scoring.
- Score = 0

STEP 2 — WEIGHTED SCORING (Total 100 points possible)
Only score if Gatekeeper passes. Assign points exactly as defined below.

1. Role Depth (20 points)
- 1 qualifying role: 10
- 2 roles: 15
- 3+ roles: 20

2. Role Tenure (15 points)
- Less than 2 years average tenure: 5
- 2–3 years average tenure: 10
- More than 3 years average tenure: 15

3. Trajectory Integrity (10 points)
- Maintained or increased scope post-CIO: 10
- One lateral: 8
- One downgrade: 5
- Multiple downgrades: 0

4. Industry Breadth (10 points)
- 1 industry: 5
- 2–3 industries: 8
- 4+ industries: 10

5. Company Size Diversity (5 points)
- Startup + mid + enterprise: 5
- Two categories: 3
- One category: 1

6. Stability (5 points)
- Average tenure 2.5 years or more: 5
- 2.0–2.5 years: 3
- Less than 2 years: 0

7. Global Exposure (5 points)
- Direct global scope: 5
- Regional or multi-country: 3
- Domestic only: 0

8. Tech Transformation Depth (15 points)
- Multiple major enterprise transformations: 15
- One major: 8
- None: 0

9. Private Equity / M&A Experience (10 points)
- Significant direct leadership: 10
- Some exposure: 5
- None: 0

10. Recent Relevance (5 points)
- Last CIO role ended within 2 years: 5
- 2–4 years: 3
- More than 4 years: 0

Penalty: Consulting-Only Gap (–10 points)
Deduct 10 points if the last 3 or more years have been exclusively consulting or advisory since the last qualifying role.

STEP 3 — OUTPUT FORMAT
Respond ONLY in the following JSON structure. Do not add commentary.

{
  "gatekeeper_result": "Pass" or "Fail",
  "score_breakdown": {
    "role_depth": number,
    "role_tenure": number,
    "trajectory_integrity": number,
    "industry_breadth": number,
    "company_size_diversity": number,
    "stability": number,
    "global_exposure": number,
    "tech_transformation_depth": number,
    "private_equity_MA_experience": number,
    "recent_relevance": number,
    "consulting_only_penalty": number
  },
  "total_score": number,
  "fit_verdict": "Elite Fortium Fit" | "Strong Fit" | "Good Fit" | "Marginal Fit" | "No Fit",
  "rationale": "Brief 2–4 sentence justification using Fortium's standards"
}

SCORING BANDS
- 90–100: Elite Fortium Fit (extremely rare)
- 80–89: Strong Fit
- 70–79: Good Fit
- Less than 70: Marginal Fit
- Gatekeeper Fail: No Fit"""

# Create the request payload
payload = {
    "name": "Advanced CIO Gatekeeper Template",
    "category": "CIO",
    "prompt_text": template_content,
    "description": "Advanced CIO template with gatekeeper filter and detailed weighted scoring",
    "is_active": True,
    "metadata": {
        "version": "2.0",
        "scoring_type": "gatekeeper_weighted",
        "max_score": 100
    }
}

# API details
url = "https://smooth-mailbox-production.up.railway.app/api/v1/templates"
headers = {
    "x-api-key": "li_HieZz-IjBp0uE7d-rZkRE0qyy12r5_ZJS_FR4jMvv0I",
    "Content-Type": "application/json"
}

print("Creating template...")
print(f"Template name: {payload['name']}")
print(f"Category: {payload['category']}")
print(f"Content length: {len(payload['prompt_text'])} characters")
print()

try:
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    
    print(f"Status Code: {response.status_code}")
    print("Response Headers:")
    for key, value in response.headers.items():
        print(f"  {key}: {value}")
    print()
    
    if response.status_code == 201:
        result = response.json()
        print("✅ Template created successfully!")
        print(f"Template ID: {result.get('id')}")
        print(f"Name: {result.get('name')}")
        print(f"Category: {result.get('category')}")
        print(f"Active: {result.get('is_active')}")
    else:
        print("❌ Template creation failed")
        try:
            error_data = response.json()
            print("Error Response:")
            print(json.dumps(error_data, indent=2))
        except:
            print("Raw Response:")
            print(response.text)

except requests.exceptions.RequestException as e:
    print(f"❌ Request failed: {e}")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
