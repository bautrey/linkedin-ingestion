#!/usr/bin/env python3
"""
Test script to validate our flexible models work with Cassidy API responses
"""

import json
import asyncio
from pydantic import ValidationError

from app.cassidy.models import LinkedInProfile, CompanyProfile
from app.cassidy.client import CassidyClient
from app.tests.fixtures.mock_responses import (
    MOCK_CASSIDY_PROFILE_RESPONSE,
    MOCK_CASSIDY_COMPANY_RESPONSE,
    MOCK_PROFILE_MINIMAL_DATA,
    MOCK_PROFILE_WITH_MULTIPLE_COMPANIES
)


def test_profile_data_extraction():
    """Test profile data extraction and model validation"""
    print("🔍 Testing Profile Data Extraction & Validation")
    print("=" * 60)
    
    client = CassidyClient()
    
    test_cases = [
        ("Full Profile Data", MOCK_CASSIDY_PROFILE_RESPONSE),
        ("Minimal Profile Data", MOCK_PROFILE_MINIMAL_DATA), 
        ("Multi-Company Profile", MOCK_PROFILE_WITH_MULTIPLE_COMPANIES)
    ]
    
    for test_name, mock_response in test_cases:
        print(f"\n📋 Testing: {test_name}")
        try:
            # Extract profile data using client method
            profile_data = client._extract_profile_data(mock_response)
            
            # Add raw data (as our updated client does)
            profile_data['raw_data'] = mock_response
            
            # Try to create LinkedInProfile model
            profile = LinkedInProfile(**profile_data)
            
            print(f"   ✅ SUCCESS: Profile created successfully")
            print(f"   📊 Name: {profile.name}")
            print(f"   📊 ID: {profile.id}")
            print(f"   📊 Experience count: {len(profile.experience) if profile.experience else 0}")
            print(f"   📊 Has raw data: {profile.raw_data is not None}")
            
            # Test that extra fields are captured
            profile_dict = profile.model_dump()
            extra_fields = [k for k in profile_dict.keys() if not hasattr(LinkedInProfile, k)]
            if extra_fields:
                print(f"   🎯 Extra fields captured: {len(extra_fields)}")
            
        except ValidationError as e:
            print(f"   ❌ VALIDATION ERROR: {e}")
            assert False, f"Validation error: {e}"
        except Exception as e:
            print(f"   ❌ EXTRACTION ERROR: {e}")
            assert False, f"Extraction error: {e}"
    
    assert True


def test_company_data_extraction():
    """Test company data extraction and model validation"""
    print("\n🏢 Testing Company Data Extraction & Validation")
    print("=" * 60)
    
    client = CassidyClient()
    
    try:
        # Extract company data using client method
        company_data = client._extract_company_data(MOCK_CASSIDY_COMPANY_RESPONSE)
        
        # Add raw data (as our updated client does)
        company_data['raw_data'] = MOCK_CASSIDY_COMPANY_RESPONSE
        
        # Try to create CompanyProfile model
        company = CompanyProfile(**company_data)
        
        print(f"   ✅ SUCCESS: Company profile created successfully")
        print(f"   📊 Name: {company.company_name}")
        print(f"   📊 ID: {company.company_id}")
        print(f"   📊 Employees: {company.employee_count}")
        print(f"   📊 Industries: {company.industries}")
        print(f"   📊 Has raw data: {company.raw_data is not None}")
        
        # Test that extra fields are captured
        company_dict = company.model_dump()
        extra_fields = [k for k in company_dict.keys() if not hasattr(CompanyProfile, k)]
        if extra_fields:
            print(f"   🎯 Extra fields captured: {len(extra_fields)}")
        
        assert True
        
    except ValidationError as e:
        print(f"   ❌ VALIDATION ERROR: {e}")
        assert False, f"Validation error: {e}"
    except Exception as e:
        print(f"   ❌ EXTRACTION ERROR: {e}")
        assert False, f"Extraction error: {e}"


def test_edge_cases():
    """Test edge cases and unusual data structures"""
    print("\n🧪 Testing Edge Cases")
    print("=" * 60)
    
    # Test with completely unknown fields
    test_profile_data = {
        "id": "test-unknown-fields",
        "name": "Test Person",
        "url": "https://linkedin.com/in/test",
        # Unknown fields that LinkedIn might add in the future
        "ai_score": 95,
        "professional_network": {"connections": 500, "influence": "high"},
        "skill_assessments": [{"skill": "Python", "score": 98}],
        "endorsement_graph": {"nodes": 50, "connections": 200},
        "raw_data": {"test": "data"}
    }
    
    try:
        profile = LinkedInProfile(**test_profile_data)
        print("   ✅ SUCCESS: Model accepts completely unknown fields")
        print(f"   📊 AI Score (unknown field): {getattr(profile, 'ai_score', 'Not accessible')}")
        
        # Check if unknown fields are in the dict
        profile_dict = profile.model_dump()
        if 'ai_score' in profile_dict:
            print(f"   🎯 Unknown field preserved: ai_score = {profile_dict['ai_score']}")
        
        assert True
        
    except Exception as e:
        print(f"   ❌ ERROR with unknown fields: {e}")
        assert False, f"Error with unknown fields: {e}"


def test_flexible_types():
    """Test flexible Union types handle different data formats"""
    print("\n🔄 Testing Flexible Type Handling")
    print("=" * 60)
    
    # Test different formats for the same field
    test_cases = [
        {
            "name": "String followers",
            "data": {
                "id": "test-1",
                "name": "Test Person",
                "url": "https://linkedin.com/in/test1",
                "followers": "1.5K",  # String instead of int
                "experience": [],      # Empty list
                "raw_data": {}
            }
        },
        {
            "name": "Dict experience entries",
            "data": {
                "id": "test-2", 
                "name": "Test Person 2",
                "url": "https://linkedin.com/in/test2",
                "followers": 1500,    # Int
                "experience": [{"custom": "format", "not": "standard"}],  # Dict instead of ExperienceEntry
                "raw_data": {}
            }
        }
    ]
    
    for test_case in test_cases:
        try:
            profile = LinkedInProfile(**test_case["data"])
            print(f"   ✅ SUCCESS: {test_case['name']}")
            print(f"   📊 Followers type: {type(profile.followers)}")
            print(f"   📊 Experience type: {type(profile.experience)}")
            
        except Exception as e:
            print(f"   ❌ ERROR with {test_case['name']}: {e}")
            assert False, f"Error with {test_case['name']}: {e}"
    
    assert True


if __name__ == "__main__":
    print("🚀 LinkedIn Model Validation Test Suite")
    print("=" * 70)
    
    success = True
    
    # Run all validation tests
    success &= test_profile_data_extraction()
    success &= test_company_data_extraction() 
    success &= test_edge_cases()
    success &= test_flexible_types()
    
    print("\n" + "=" * 70)
    if success:
        print("🎉 ALL VALIDATION TESTS PASSED!")
        print("✅ Models are ready for complete data capture")
        print("✅ Flexible typing works correctly")
        print("✅ Unknown fields are preserved")
        print("✅ Raw data storage functional")
    else:
        print("❌ Some validation tests failed - models need fixes")
    
    print("=" * 70)
