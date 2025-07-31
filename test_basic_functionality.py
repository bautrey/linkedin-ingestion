#!/usr/bin/env python3
"""
Basic unit tests for LinkedIn ingestion functionality
Non-async tests that verify core functionality works
"""

import json
from app.cassidy.models import LinkedInProfile, CompanyProfile
from app.cassidy.client import CassidyClient
from app.tests.fixtures.mock_responses import (
    MOCK_CASSIDY_PROFILE_RESPONSE,
    MOCK_CASSIDY_COMPANY_RESPONSE,
    MOCK_PROFILE_MINIMAL_DATA,
    MOCK_PROFILE_WITH_MULTIPLE_COMPANIES
)


def test_profile_model_validation():
    """Test that LinkedInProfile model accepts valid data"""
    print("🧪 Testing Profile Model Validation...")
    
    client = CassidyClient()
    profile_data = client._extract_profile_data(MOCK_CASSIDY_PROFILE_RESPONSE)
    transformed_data = client._transform_profile_data(profile_data)
    
    # Should not raise validation error
    profile = LinkedInProfile(**transformed_data)
    
    assert profile.name == "Ronald Sorozan (MBA, CISM, PMP)"
    assert profile.id == "ronald-sorozan-mba-cism-pmp-8325652"
    assert len(profile.experience) == 1
    assert len(profile.education) == 1
    assert len(profile.certifications) == 2
    assert profile.followers == 1503
    assert profile.connections == 500
    
    print("✅ Profile model validation passed")


def test_company_model_validation():
    """Test that CompanyProfile model accepts valid data"""
    print("🧪 Testing Company Model Validation...")
    
    client = CassidyClient()
    company_data = client._extract_company_data(MOCK_CASSIDY_COMPANY_RESPONSE)
    transformed_data = client._transform_company_data(company_data)
    
    # Should not raise validation error
    company = CompanyProfile(**transformed_data)
    
    assert company.company_name == "JAM+"
    assert company.company_id == "jambnc"
    assert company.employee_count == 250
    assert company.year_founded == "2018"
    assert "Printing" in company.industries
    assert len(company.locations) == 1
    
    print("✅ Company model validation passed")


def test_minimal_profile_data():
    """Test profile with minimal data"""
    print("🧪 Testing Minimal Profile Data...")
    
    client = CassidyClient()
    profile_data = client._extract_profile_data(MOCK_PROFILE_MINIMAL_DATA)
    transformed_data = client._transform_profile_data(profile_data)
    
    profile = LinkedInProfile(**transformed_data)
    
    assert profile.name == "Jane Smith"
    assert profile.id == "test-minimal-profile"
    assert profile.position == "Software Engineer"
    assert len(profile.experience) == 0
    assert len(profile.education) == 0
    
    print("✅ Minimal profile data test passed")


def test_multiple_companies_profile():
    """Test profile with multiple work experiences"""
    print("🧪 Testing Multiple Companies Profile...")
    
    client = CassidyClient()
    profile_data = client._extract_profile_data(MOCK_PROFILE_WITH_MULTIPLE_COMPANIES)
    transformed_data = client._transform_profile_data(profile_data)
    
    profile = LinkedInProfile(**transformed_data)
    
    assert profile.name == "John Doe"
    assert len(profile.experience) == 2
    assert profile.experience[0].company == "Tech Corp"
    assert profile.experience[1].company == "StartupXYZ"
    
    print("✅ Multiple companies profile test passed")


def test_data_extraction_methods():
    """Test the data extraction methods work correctly"""
    print("🧪 Testing Data Extraction Methods...")
    
    client = CassidyClient()
    
    # Test profile extraction
    profile_data = client._extract_profile_data(MOCK_CASSIDY_PROFILE_RESPONSE)
    assert isinstance(profile_data, dict)
    assert "full_name" in profile_data
    assert "profile_id" in profile_data
    
    # Test company extraction  
    company_data = client._extract_company_data(MOCK_CASSIDY_COMPANY_RESPONSE)
    assert isinstance(company_data, dict)
    assert "company_name" in company_data
    assert "company_id" in company_data
    
    print("✅ Data extraction methods test passed")


def test_error_handling():
    """Test error handling with invalid data"""
    print("🧪 Testing Error Handling...")
    
    client = CassidyClient()
    
    # Test with invalid structure
    invalid_response = {"invalid": "structure"}
    
    try:
        client._extract_profile_data(invalid_response)
        assert False, "Should have raised an exception"
    except Exception as e:
        assert "workflowRun" in str(e) or "action results" in str(e).lower()
    
    print("✅ Error handling test passed")


def run_all_tests():
    """Run all tests"""
    print("🚀 Running Basic LinkedIn Ingestion Tests")
    print("=" * 60)
    
    tests = [
        test_profile_model_validation,
        test_company_model_validation,
        test_minimal_profile_data,
        test_multiple_companies_profile,
        test_data_extraction_methods,
        test_error_handling
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"❌ {test_func.__name__} failed: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Step 2 complete.")
        print("✅ Unit testing infrastructure working correctly")
        return True
    else:
        print("❌ Some tests failed - need to fix issues")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
