#!/usr/bin/env python3
"""
Simple validation test for our precise LinkedIn models
"""

import json
from pydantic import ValidationError

from app.cassidy.models import LinkedInProfile, CompanyProfile  
from app.cassidy.client import CassidyClient
from app.tests.fixtures.mock_responses import (
    MOCK_CASSIDY_PROFILE_RESPONSE,
    MOCK_CASSIDY_COMPANY_RESPONSE
)

def test_models():
    """Test that our models work with Cassidy mock data"""
    print("🔍 Testing LinkedIn Models with Cassidy Data")
    print("=" * 50)
    
    client = CassidyClient()
    
    # Test Profile Model
    print("\n📋 Testing Profile Model...")
    try:
        profile_data = client._extract_profile_data(MOCK_CASSIDY_PROFILE_RESPONSE)
        profile = LinkedInProfile(**profile_data)
        
        print(f"✅ Profile created successfully!")
        print(f"   Name: {profile.name}")
        print(f"   ID: {profile.id}")
        print(f"   Position: {profile.position}")
        print(f"   Experience count: {len(profile.experience)}")
        print(f"   Education count: {len(profile.education)}")
        print(f"   Certifications: {len(profile.certifications)}")
        
    except ValidationError as e:
        print(f"❌ Profile validation failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Profile error: {e}")
        return False
    
    # Test Company Model
    print("\n🏢 Testing Company Model...")
    try:
        company_data = client._extract_company_data(MOCK_CASSIDY_COMPANY_RESPONSE)
        company = CompanyProfile(**company_data)
        
        print(f"✅ Company created successfully!")
        print(f"   Name: {company.company_name}")
        print(f"   ID: {company.company_id}")
        print(f"   Employees: {company.employee_count}")
        print(f"   Industries: {company.industries}")
        print(f"   Founded: {company.year_founded}")
        
    except ValidationError as e:
        print(f"❌ Company validation failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Company error: {e}")
        return False
    
    print("\n🎉 All models validated successfully!")
    return True

if __name__ == "__main__":
    success = test_models()
    if success:
        print("\n✅ Step 1 Complete: Model validation fixed!")
        print("Ready to proceed with unit tests...")
    else:
        print("\n❌ Models need further fixes")
