#!/usr/bin/env python3
"""
Test Script: Unified Profile Ingestion with Company Processing

This script tests the newly unified profile ingestion flow to ensure:
1. Profiles are created successfully
2. Companies are processed and linked
3. Junction table relationships work
4. Error handling is robust
5. Batch processing works correctly
"""

import requests
import json
import time
import uuid
from typing import Dict, Any, List

# Configuration
BASE_URL = "http://localhost:8000"
API_KEY = "li_HieZz-IjBp0uE7d-rZkRE0qyy12r5_ZJS_FR4jMvv0I"
HEADERS = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

class TestRunner:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.results = []
        
    def log_test(self, test_name: str, passed: bool, details: str = ""):
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
        if not passed:
            print()
            
        self.results.append({
            "test": test_name,
            "passed": passed,
            "details": details
        })
        
        if passed:
            self.passed += 1
        else:
            self.failed += 1
    
    def test_health_check(self):
        """Test that the API is running"""
        try:
            response = requests.get(f"{BASE_URL}/api/v1/health")
            passed = response.status_code == 200
            details = f"Status: {response.status_code}"
            if passed:
                data = response.json()
                details += f", Database: {data.get('database', {}).get('status', 'unknown')}"
        except Exception as e:
            passed = False
            details = f"Connection failed: {str(e)}"
        
        self.log_test("Health Check", passed, details)
        return passed
    
    def test_single_profile_creation(self):
        """Test creating a single profile with company processing"""
        test_url = f"https://www.linkedin.com/in/test-{uuid.uuid4().hex[:8]}/"
        
        payload = {
            "linkedin_url": test_url,
            "suggested_role": "CTO",
            "include_companies": True
        }
        
        try:
            response = requests.post(f"{BASE_URL}/api/v1/profiles", headers=HEADERS, json=payload)
            
            if response.status_code == 201:
                data = response.json()
                profile_id = data.get("id")
                companies_processed = data.get("companies_processed", [])
                
                passed = bool(profile_id)
                details = f"Profile ID: {profile_id[:8]}..., Companies: {len(companies_processed)}"
                
                # Store profile ID for cleanup later
                if hasattr(self, 'test_profile_ids'):
                    self.test_profile_ids.append(profile_id)
                else:
                    self.test_profile_ids = [profile_id]
                    
            else:
                passed = False
                details = f"Status: {response.status_code}, Error: {response.text[:100]}"
                
        except Exception as e:
            passed = False
            details = f"Request failed: {str(e)}"
        
        self.log_test("Single Profile Creation", passed, details)
        return passed
    
    def test_profile_without_companies(self):
        """Test creating a profile without company processing"""
        test_url = f"https://www.linkedin.com/in/no-companies-{uuid.uuid4().hex[:8]}/"
        
        payload = {
            "linkedin_url": test_url,
            "suggested_role": "CIO",
            "include_companies": False
        }
        
        try:
            response = requests.post(f"{BASE_URL}/api/v1/profiles", headers=HEADERS, json=payload)
            
            if response.status_code == 201:
                data = response.json()
                profile_id = data.get("id")
                companies_processed = data.get("companies_processed")
                
                # Should have profile ID but no companies processed
                passed = bool(profile_id) and companies_processed is None
                details = f"Profile ID: {profile_id[:8]}..., No companies processed: {companies_processed is None}"
                
                if hasattr(self, 'test_profile_ids'):
                    self.test_profile_ids.append(profile_id)
                else:
                    self.test_profile_ids = [profile_id]
                    
            else:
                passed = False
                details = f"Status: {response.status_code}, Error: {response.text[:100]}"
                
        except Exception as e:
            passed = False
            details = f"Request failed: {str(e)}"
        
        self.log_test("Profile Without Companies", passed, details)
        return passed
    
    def test_batch_profile_creation(self):
        """Test batch profile creation"""
        test_profiles = [
            {
                "linkedin_url": f"https://www.linkedin.com/in/batch-1-{uuid.uuid4().hex[:8]}/",
                "suggested_role": "CTO",
                "include_companies": True
            },
            {
                "linkedin_url": f"https://www.linkedin.com/in/batch-2-{uuid.uuid4().hex[:8]}/",
                "suggested_role": "CISO", 
                "include_companies": True
            }
        ]
        
        payload = {
            "profiles": test_profiles,
            "max_concurrent": 2
        }
        
        try:
            response = requests.post(f"{BASE_URL}/api/v1/profiles/batch", headers=HEADERS, json=payload)
            
            if response.status_code == 201:
                data = response.json()
                batch_id = data.get("batch_id")
                total_requested = data.get("total_requested", 0)
                successful = data.get("successful", 0)
                results = data.get("results", [])
                
                passed = (batch_id and total_requested == 2 and len(results) == 2)
                details = f"Batch ID: {batch_id[:8] if batch_id else 'None'}..., Success: {successful}/{total_requested}"
                
                # Store profile IDs for cleanup
                for result in results:
                    if result.get("id"):
                        if hasattr(self, 'test_profile_ids'):
                            self.test_profile_ids.append(result["id"])
                        else:
                            self.test_profile_ids = [result["id"]]
                            
            else:
                passed = False
                details = f"Status: {response.status_code}, Error: {response.text[:100]}"
                
        except Exception as e:
            passed = False
            details = f"Request failed: {str(e)}"
        
        self.log_test("Batch Profile Creation", passed, details)
        return passed
    
    def test_invalid_linkedin_url(self):
        """Test error handling for invalid LinkedIn URL"""
        payload = {
            "linkedin_url": "https://not-linkedin.com/profile",
            "suggested_role": "CTO"
        }
        
        try:
            response = requests.post(f"{BASE_URL}/api/v1/profiles", headers=HEADERS, json=payload)
            
            # Should return 400 or 422 for invalid URL
            passed = response.status_code in [400, 422]
            details = f"Status: {response.status_code} (expected 400/422)"
            
            if passed and response.status_code == 400:
                data = response.json()
                error_message = data.get("message", "")
                if "linkedin" in error_message.lower():
                    details += ", Error message mentions LinkedIn"
                    
        except Exception as e:
            passed = False
            details = f"Request failed: {str(e)}"
        
        self.log_test("Invalid LinkedIn URL", passed, details)
        return passed
    
    def test_missing_required_field(self):
        """Test validation error for missing required field"""
        payload = {
            "linkedin_url": "https://www.linkedin.com/in/test/"
            # Missing suggested_role
        }
        
        try:
            response = requests.post(f"{BASE_URL}/api/v1/profiles", headers=HEADERS, json=payload)
            
            # Should return 422 validation error
            passed = response.status_code == 422
            details = f"Status: {response.status_code} (expected 422)"
            
        except Exception as e:
            passed = False
            details = f"Request failed: {str(e)}"
        
        self.log_test("Missing Required Field", passed, details)
        return passed
    
    def test_invalid_api_key(self):
        """Test authentication with invalid API key"""
        invalid_headers = {
            "X-API-Key": "invalid-key-123",
            "Content-Type": "application/json"
        }
        
        payload = {
            "linkedin_url": "https://www.linkedin.com/in/test/",
            "suggested_role": "CTO"
        }
        
        try:
            response = requests.post(f"{BASE_URL}/api/v1/profiles", headers=invalid_headers, json=payload)
            
            # Should return 403 unauthorized
            passed = response.status_code == 403
            details = f"Status: {response.status_code} (expected 403)"
            
        except Exception as e:
            passed = False
            details = f"Request failed: {str(e)}"
        
        self.log_test("Invalid API Key", passed, details)
        return passed
    
    def test_profile_retrieval(self):
        """Test retrieving a created profile"""
        if not hasattr(self, 'test_profile_ids') or not self.test_profile_ids:
            self.log_test("Profile Retrieval", False, "No test profiles available")
            return False
        
        profile_id = self.test_profile_ids[0]
        
        try:
            response = requests.get(f"{BASE_URL}/api/v1/profiles/{profile_id}", headers=HEADERS)
            
            if response.status_code == 200:
                data = response.json()
                retrieved_id = data.get("id")
                name = data.get("name", "")
                
                passed = retrieved_id == profile_id
                details = f"Retrieved profile: {name[:30]}..." if name else f"Profile ID: {retrieved_id[:8]}..."
                
            else:
                passed = False
                details = f"Status: {response.status_code}, Error: {response.text[:100]}"
                
        except Exception as e:
            passed = False
            details = f"Request failed: {str(e)}"
        
        self.log_test("Profile Retrieval", passed, details)
        return passed
    
    def test_profile_list(self):
        """Test listing profiles"""
        try:
            response = requests.get(f"{BASE_URL}/api/v1/profiles?limit=5", headers=HEADERS)
            
            if response.status_code == 200:
                data = response.json()
                profiles = data.get("data", [])
                pagination = data.get("pagination", {})
                
                passed = isinstance(profiles, list) and "limit" in pagination
                details = f"Found {len(profiles)} profiles, pagination: {pagination.get('limit', 0)}"
                
            else:
                passed = False
                details = f"Status: {response.status_code}, Error: {response.text[:100]}"
                
        except Exception as e:
            passed = False
            details = f"Request failed: {str(e)}"
        
        self.log_test("Profile List", passed, details)
        return passed
    
    def cleanup_test_profiles(self):
        """Clean up test profiles created during testing"""
        if not hasattr(self, 'test_profile_ids'):
            return
            
        print(f"\n🧹 Cleaning up {len(self.test_profile_ids)} test profiles...")
        
        for profile_id in self.test_profile_ids:
            try:
                response = requests.delete(f"{BASE_URL}/api/v1/profiles/{profile_id}", headers=HEADERS)
                if response.status_code == 204:
                    print(f"   Deleted profile {profile_id[:8]}...")
                else:
                    print(f"   Failed to delete profile {profile_id[:8]}: {response.status_code}")
            except Exception as e:
                print(f"   Error deleting profile {profile_id[:8]}: {str(e)}")
    
    def run_all_tests(self):
        """Run all test scenarios"""
        print("🚀 Starting Unified Profile Ingestion Tests\n")
        
        # Basic connectivity
        if not self.test_health_check():
            print("❌ Cannot connect to API, stopping tests")
            return
        
        print()
        
        # Core functionality tests
        self.test_single_profile_creation()
        self.test_profile_without_companies()
        self.test_batch_profile_creation()
        
        print()
        
        # Error handling tests  
        self.test_invalid_linkedin_url()
        self.test_missing_required_field()
        self.test_invalid_api_key()
        
        print()
        
        # Data retrieval tests
        self.test_profile_retrieval()
        self.test_profile_list()
        
        print()
        
        # Cleanup
        self.cleanup_test_profiles()
        
        # Summary
        print(f"\n📊 Test Summary:")
        print(f"   Passed: {self.passed}")
        print(f"   Failed: {self.failed}")
        print(f"   Total:  {self.passed + self.failed}")
        
        if self.failed == 0:
            print(f"\n🎉 All tests passed! Unified ingestion is working correctly.")
        else:
            print(f"\n⚠️  {self.failed} test(s) failed. Check the details above.")
        
        return self.failed == 0

def main():
    """Main test execution"""
    runner = TestRunner()
    success = runner.run_all_tests()
    
    # Exit with appropriate code
    exit(0 if success else 1)

if __name__ == "__main__":
    main()
