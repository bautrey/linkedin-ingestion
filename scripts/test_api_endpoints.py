#!/usr/bin/env python3
"""
Production-like API Endpoint Testing Script

This script tests all API endpoints with realistic production scenarios:
1. Health check endpoints
2. Profile endpoints (CRUD operations)
3. Enhanced profile ingestion endpoints
4. Batch profile ingestion endpoints 
5. Company endpoints
6. Template management endpoints
7. Error handling and edge cases

Run with: python scripts/test_api_endpoints.py
"""

import asyncio
import httpx
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import uuid
from datetime import datetime

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.config import settings

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_API_KEY = settings.API_KEY or "test-api-key"
TIMEOUT = 30.0

# Test LinkedIn URLs (should be realistic but not necessarily valid for actual ingestion)
TEST_URLS = [
    "https://www.linkedin.com/in/test-user-1/",
    "https://www.linkedin.com/in/test-user-2/",
    "https://www.linkedin.com/in/test-user-3/",
]

class APIEndpointTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=TIMEOUT)
        self.results = []
        self.profile_ids = []
        self.company_ids = []
        self.template_ids = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                          headers: Optional[Dict] = None, expected_status: int = 200) -> Dict[str, Any]:
        """Make HTTP request and record result"""
        url = f"{BASE_URL}{endpoint}"
        
        # Default headers
        request_headers = {"Content-Type": "application/json"}
        if headers:
            request_headers.update(headers)
            
        try:
            if method.upper() == "GET":
                response = await self.client.get(url, headers=request_headers)
            elif method.upper() == "POST":
                response = await self.client.post(url, json=data, headers=request_headers)
            elif method.upper() == "PUT":
                response = await self.client.put(url, json=data, headers=request_headers)
            elif method.upper() == "DELETE":
                response = await self.client.delete(url, headers=request_headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            result = {
                "method": method,
                "endpoint": endpoint,
                "status_code": response.status_code,
                "expected_status": expected_status,
                "success": response.status_code == expected_status,
                "response_time": response.elapsed.total_seconds(),
                "content_type": response.headers.get("content-type", ""),
                "response_size": len(response.content)
            }
            
            # Try to parse JSON response
            try:
                result["response_data"] = response.json()
            except:
                result["response_text"] = response.text[:200] + "..." if len(response.text) > 200 else response.text
            
            # Record result
            self.results.append(result)
            
            return result
            
        except Exception as e:
            result = {
                "method": method,
                "endpoint": endpoint,
                "status_code": 0,
                "expected_status": expected_status,
                "success": False,
                "error": str(e)
            }
            self.results.append(result)
            return result

    def auth_headers(self) -> Dict[str, str]:
        """Get authentication headers"""
        return {"X-API-Key": TEST_API_KEY}

    async def test_health_endpoints(self):
        """Test health and status endpoints"""
        print("\n=== Testing Health Endpoints ===")
        
        # Basic health check
        result = await self.make_request("GET", "/api/v1/health")
        print(f"✅ Basic health check: {result['status_code']}")
        
        # Detailed health check (requires auth)
        result = await self.make_request("GET", "/api/v1/health/detailed", 
                                       headers=self.auth_headers())
        print(f"✅ Detailed health check: {result['status_code']}")
        
        # OpenAI test endpoint
        result = await self.make_request("GET", "/api/v1/openai-test", 
                                       headers=self.auth_headers())
        print(f"✅ OpenAI test: {result['status_code']}")
        
        # Root endpoint
        result = await self.make_request("GET", "/")
        print(f"✅ Root endpoint: {result['status_code']}")
        
        # Version endpoint
        result = await self.make_request("GET", "/api/version")
        print(f"✅ Version endpoint: {result['status_code']}")

    async def test_profile_endpoints(self):
        """Test profile CRUD operations"""
        print("\n=== Testing Profile Endpoints ===")
        
        # List profiles (should work with auth)
        result = await self.make_request("GET", "/api/v1/profiles", 
                                       headers=self.auth_headers())
        print(f"✅ List profiles: {result['status_code']}")
        
        # Test authentication requirement
        result = await self.make_request("GET", "/api/v1/profiles", 
                                       expected_status=403)
        print(f"✅ Profile list without auth: {result['status_code']} (should be 403)")
        
        # Test profile creation with minimal payload
        create_data = {
            "linkedin_url": TEST_URLS[0],
            "suggested_role": "CTO"
        }
        result = await self.make_request("POST", "/api/v1/profiles", 
                                       data=create_data, 
                                       headers=self.auth_headers(),
                                       expected_status=201)
        print(f"✅ Create profile: {result['status_code']}")
        
        # Get profile by ID if creation was successful
        if result.get("success") and result.get("response_data"):
            profile_id = result["response_data"].get("id")
            if profile_id:
                self.profile_ids.append(profile_id)
                
                # Get profile by ID
                result = await self.make_request("GET", f"/api/v1/profiles/{profile_id}",
                                               headers=self.auth_headers())
                print(f"✅ Get profile by ID: {result['status_code']}")
        
        # Test invalid profile creation
        invalid_data = {
            "linkedin_url": "invalid-url",
            "suggested_role": "INVALID_ROLE"
        }
        result = await self.make_request("POST", "/api/v1/profiles", 
                                       data=invalid_data, 
                                       headers=self.auth_headers(),
                                       expected_status=422)
        print(f"✅ Invalid profile creation: {result['status_code']} (should be 422)")

    async def test_enhanced_profile_endpoints(self):
        """Test enhanced profile ingestion endpoints"""
        print("\n=== Testing Enhanced Profile Endpoints ===")
        
        # Enhanced single profile ingestion
        enhance_data = {
            "linkedin_url": TEST_URLS[1],
            "suggested_role": "CIO",
            "include_companies": True
        }
        result = await self.make_request("POST", "/api/v1/profiles/enhanced", 
                                       data=enhance_data, 
                                       headers=self.auth_headers(),
                                       expected_status=201)
        print(f"✅ Enhanced profile creation: {result['status_code']}")
        
        if result.get("success") and result.get("response_data"):
            profile_id = result["response_data"].get("id")
            if profile_id:
                self.profile_ids.append(profile_id)

    async def test_batch_profile_endpoints(self):
        """Test batch profile ingestion endpoints"""
        print("\n=== Testing Batch Profile Endpoints ===")
        
        # Valid batch request
        batch_data = {
            "profiles": [
                {
                    "linkedin_url": TEST_URLS[0],
                    "suggested_role": "CTO"
                },
                {
                    "linkedin_url": TEST_URLS[1], 
                    "suggested_role": "CIO"
                }
            ],
            "max_concurrent": 2
        }
        result = await self.make_request("POST", "/api/v1/profiles/batch-enhanced",
                                       data=batch_data,
                                       headers=self.auth_headers(),
                                       expected_status=201)
        print(f"✅ Batch profile creation: {result['status_code']}")
        
        # Test empty batch (should fail validation)
        empty_batch = {
            "profiles": [],
            "max_concurrent": 1
        }
        result = await self.make_request("POST", "/api/v1/profiles/batch-enhanced",
                                       data=empty_batch,
                                       headers=self.auth_headers(),
                                       expected_status=422)
        print(f"✅ Empty batch validation: {result['status_code']} (should be 422)")
        
        # Test too many profiles (should fail validation)
        too_many_profiles = {
            "profiles": [
                {"linkedin_url": f"https://www.linkedin.com/in/user{i}/", "suggested_role": "CTO"} 
                for i in range(11)  # Over limit of 10
            ],
            "max_concurrent": 2
        }
        result = await self.make_request("POST", "/api/v1/profiles/batch-enhanced",
                                       data=too_many_profiles,
                                       headers=self.auth_headers(),
                                       expected_status=422)
        print(f"✅ Too many profiles validation: {result['status_code']} (should be 422)")
        
        # Test invalid concurrent value
        invalid_concurrent = {
            "profiles": [{"linkedin_url": TEST_URLS[0], "suggested_role": "CTO"}],
            "max_concurrent": 10  # Over limit of 5
        }
        result = await self.make_request("POST", "/api/v1/profiles/batch-enhanced",
                                       data=invalid_concurrent,
                                       headers=self.auth_headers(),
                                       expected_status=422)
        print(f"✅ Invalid concurrent validation: {result['status_code']} (should be 422)")

    async def test_company_endpoints(self):
        """Test company management endpoints"""
        print("\n=== Testing Company Endpoints ===")
        
        # List companies
        result = await self.make_request("GET", "/api/v1/companies",
                                       headers=self.auth_headers())
        print(f"✅ List companies: {result['status_code']}")
        
        # Create company
        company_data = {
            "company_name": f"Test Company {uuid.uuid4().hex[:8]}",
            "description": "A test company for API testing",
            "employee_count": 100,
            "industries": ["Technology", "Software"],
            "hq_city": "San Francisco",
            "hq_country": "United States"
        }
        result = await self.make_request("POST", "/api/v1/companies",
                                       data=company_data,
                                       headers=self.auth_headers(),
                                       expected_status=201)
        print(f"✅ Create company: {result['status_code']}")
        
        if result.get("success") and result.get("response_data"):
            company_id = result["response_data"].get("id")
            if company_id:
                self.company_ids.append(company_id)
                
                # Get company by ID
                result = await self.make_request("GET", f"/api/v1/companies/{company_id}",
                                               headers=self.auth_headers())
                print(f"✅ Get company by ID: {result['status_code']}")
                
                # Update company
                update_data = {
                    "description": "Updated description for test company",
                    "employee_count": 150
                }
                result = await self.make_request("PUT", f"/api/v1/companies/{company_id}",
                                               data=update_data,
                                               headers=self.auth_headers())
                print(f"✅ Update company: {result['status_code']}")

    async def test_template_endpoints(self):
        """Test template management endpoints"""
        print("\n=== Testing Template Endpoints ===")
        
        # List templates
        result = await self.make_request("GET", "/api/v1/templates",
                                       headers=self.auth_headers())
        print(f"✅ List templates: {result['status_code']}")
        
        # List template summaries
        result = await self.make_request("GET", "/api/v1/templates/summaries",
                                       headers=self.auth_headers())
        print(f"✅ List template summaries: {result['status_code']}")
        
        # Create template
        template_data = {
            "name": f"Test Template {uuid.uuid4().hex[:8]}",
            "category": "CTO",
            "description": "A test template for API testing",
            "prompt_text": "Rate this profile for CTO suitability on a scale of 1-10.",
            "is_active": True,
            "is_default": False
        }
        result = await self.make_request("POST", "/api/v1/templates",
                                       data=template_data,
                                       headers=self.auth_headers(),
                                       expected_status=201)
        print(f"✅ Create template: {result['status_code']}")
        
        if result.get("success") and result.get("response_data"):
            template_id = result["response_data"].get("id")
            if template_id:
                self.template_ids.append(template_id)
                
                # Get template by ID
                result = await self.make_request("GET", f"/api/v1/templates/{template_id}",
                                               headers=self.auth_headers())
                print(f"✅ Get template by ID: {result['status_code']}")

    async def test_error_scenarios(self):
        """Test error handling and edge cases"""
        print("\n=== Testing Error Scenarios ===")
        
        # 404 endpoints
        result = await self.make_request("GET", "/api/v1/profiles/nonexistent-id",
                                       headers=self.auth_headers(),
                                       expected_status=404)
        print(f"✅ Nonexistent profile: {result['status_code']} (should be 404)")
        
        result = await self.make_request("GET", "/api/v1/companies/nonexistent-id",
                                       headers=self.auth_headers(),
                                       expected_status=404)
        print(f"✅ Nonexistent company: {result['status_code']} (should be 404)")
        
        result = await self.make_request("GET", "/api/v1/templates/nonexistent-id",
                                       headers=self.auth_headers(),
                                       expected_status=404)
        print(f"✅ Nonexistent template: {result['status_code']} (should be 404)")
        
        # Large payload test
        large_batch = {
            "profiles": [
                {"linkedin_url": f"https://www.linkedin.com/in/user{i}/", "suggested_role": "CTO"}
                for i in range(5)  # Within limits but larger
            ],
            "max_concurrent": 3
        }
        result = await self.make_request("POST", "/api/v1/profiles/batch-enhanced",
                                       data=large_batch,
                                       headers=self.auth_headers(),
                                       expected_status=201)
        print(f"✅ Large batch request: {result['status_code']}")

    async def cleanup_test_data(self):
        """Clean up created test data"""
        print("\n=== Cleaning Up Test Data ===")
        
        # Delete test profiles
        for profile_id in self.profile_ids:
            result = await self.make_request("DELETE", f"/api/v1/profiles/{profile_id}",
                                           headers=self.auth_headers(),
                                           expected_status=204)
            print(f"✅ Delete profile {profile_id[:8]}...: {result['status_code']}")
        
        # Delete test companies
        for company_id in self.company_ids:
            result = await self.make_request("DELETE", f"/api/v1/companies/{company_id}",
                                           headers=self.auth_headers(),
                                           expected_status=204)
            print(f"✅ Delete company {company_id[:8]}...: {result['status_code']}")
        
        # Delete test templates (soft delete)
        for template_id in self.template_ids:
            result = await self.make_request("DELETE", f"/api/v1/templates/{template_id}",
                                           headers=self.auth_headers())
            print(f"✅ Delete template {template_id[:8]}...: {result['status_code']}")

    def print_summary(self):
        """Print test results summary"""
        print(f"\n{'='*60}")
        print(f"API ENDPOINT TESTING SUMMARY")
        print(f"{'='*60}")
        
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r.get("success", False))
        failed_tests = total_tests - successful_tests
        
        print(f"Total API calls: {total_tests}")
        print(f"Successful: {successful_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(successful_tests/total_tests)*100:.1f}%")
        
        # Response time statistics
        response_times = [r.get("response_time", 0) for r in self.results if r.get("response_time")]
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            max_time = max(response_times)
            print(f"Average Response Time: {avg_time:.3f}s")
            print(f"Max Response Time: {max_time:.3f}s")
        
        # Failed requests details
        failed_results = [r for r in self.results if not r.get("success", False)]
        if failed_results:
            print(f"\n❌ Failed Requests:")
            for i, result in enumerate(failed_results[:5], 1):  # Show first 5 failures
                print(f"{i}. {result['method']} {result['endpoint']}: {result['status_code']} (expected {result['expected_status']})")
                if result.get("error"):
                    print(f"   Error: {result['error']}")

async def main():
    """Main test execution"""
    print("🚀 Starting Production-like API Endpoint Testing")
    print(f"Base URL: {BASE_URL}")
    print(f"API Key configured: {'✅' if TEST_API_KEY else '❌'}")
    
    async with APIEndpointTester() as tester:
        try:
            # Run all test categories
            await tester.test_health_endpoints()
            await tester.test_profile_endpoints() 
            await tester.test_enhanced_profile_endpoints()
            await tester.test_batch_profile_endpoints()
            await tester.test_company_endpoints()
            await tester.test_template_endpoints()
            await tester.test_error_scenarios()
            
            # Clean up test data
            await tester.cleanup_test_data()
            
        except KeyboardInterrupt:
            print("\n⚠️  Testing interrupted by user")
        except Exception as e:
            print(f"\n❌ Unexpected error during testing: {str(e)}")
        finally:
            # Always print summary
            tester.print_summary()
            
            # Exit with appropriate code
            failed_tests = sum(1 for r in tester.results if not r.get("success", False))
            if failed_tests > 0:
                print(f"\n⚠️  {failed_tests} API test(s) failed - check server and configuration")
                sys.exit(1)
            else:
                print(f"\n🎉 All API tests passed! Endpoints are ready for production.")
                sys.exit(0)

if __name__ == "__main__":
    # Check if server is likely running
    if not os.getenv("SKIP_SERVER_CHECK"):
        import socket
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', 8000))
            sock.close()
            if result != 0:
                print("❌ Server doesn't appear to be running on localhost:8000")
                print("   Start the server with: python -m uvicorn main:app --reload")
                sys.exit(1)
        except:
            pass
    
    asyncio.run(main())
