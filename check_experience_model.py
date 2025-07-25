#!/usr/bin/env python3
"""
Check if our ExperienceEntry model matches the actual API response
"""

# Actual fields from the sample response
ACTUAL_EXPERIENCE_FIELDS = {
    'company', 'company_id', 'company_linkedin_url', 'company_logo_url', 
    'date_range', 'description', 'duration', 'end_month', 'end_year', 
    'is_current', 'job_type', 'location', 'skills', 'start_month', 
    'start_year', 'title'
}

# Fields in our current ExperienceEntry model
MODEL_EXPERIENCE_FIELDS = {
    'company', 'company_id', 'company_linkedin_url', 'company_logo_url',
    'current_job', 'date_range', 'description', 'end_month', 'end_year',
    'job_title', 'location', 'start_month', 'start_year'
}

print("=== EXPERIENCE MODEL COMPARISON ===")
print(f"Fields in API response: {len(ACTUAL_EXPERIENCE_FIELDS)}")
print(f"Fields in current model: {len(MODEL_EXPERIENCE_FIELDS)}")

in_api_not_model = ACTUAL_EXPERIENCE_FIELDS - MODEL_EXPERIENCE_FIELDS
in_model_not_api = MODEL_EXPERIENCE_FIELDS - ACTUAL_EXPERIENCE_FIELDS

print(f"\nFields in API but missing from model: {len(in_api_not_model)}")
for field in sorted(in_api_not_model):
    print(f"  MISSING: {field}")

print(f"\nFields in model but not in API: {len(in_model_not_api)}")
for field in sorted(in_model_not_api):
    print(f"  EXTRA: {field}")

print(f"\nFields that match: {len(ACTUAL_EXPERIENCE_FIELDS & MODEL_EXPERIENCE_FIELDS)}")
