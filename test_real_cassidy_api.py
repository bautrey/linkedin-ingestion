#!/usr/bin/env python3
"""
Real Cassidy API Integration Test

Tests the actual Cassidy API endpoints with real LinkedIn URLs
to ensure the integration is working properly.
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any

from app.cassidy.client import CassidyClient
from app.cassidy.models import LinkedInProfile, CompanyProfile
from app.core.config import settings


class RealCassidyAPITester:
    """Test real Cassidy API integration"""
    
    def __init__(self):
        self.client = CassidyClient()
        self.test_profile_url = "https://www.linkedin.com/in/satyanadella/"  # Microsoft CEO - public profile
        self.test_company_url = "https://www.linkedin.com/company/microsoft/"  # Microsoft - public company
    
    async def test_profile_fetch(self) -> Dict[str, Any]:
        """Test fetching a real LinkedIn profile via Cassidy"""
        print("=" * 60)
        print("TESTING REAL CASSIDY PROFILE API")
        print("=" * 60)
        print(f"Profile URL: {self.test_profile_url}")
        print(f"Cassidy Workflow URL: {settings.CASSIDY_PROFILE_WORKFLOW_URL}")
        print()
        
        try:
            print("🚀 Sending request to Cassidy API...")
            start_time = datetime.now()
            
            profile = await self.client.fetch_profile(self.test_profile_url)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            print(f"✅ Profile fetched successfully in {duration:.2f} seconds")
            print()
            print("Profile Data:")
            print(f"  ID: {profile.id}")
            print(f"  Name: {profile.name}")
            print(f"  Position: {profile.position}")
            print(f"  City: {profile.city}")
            print(f"  Country: {profile.country_code}")
            print(f"  Followers: {profile.followers:,}" if profile.followers else "  Followers: N/A")
            print(f"  Connections: {profile.connections:,}" if profile.connections else "  Connections: N/A")
            print(f"  Experience Items: {len(profile.experience)}")
            print(f"  Education Items: {len(profile.education)}")
            print(f"  Certifications: {len(profile.certifications)}")
            
            if profile.about:
                about_preview = profile.about[:100] + "..." if len(profile.about) > 100 else profile.about
                print(f"  About: {about_preview}")
            
            if profile.current_company:
                print(f"  Current Company: {profile.current_company}")
            
            print()
            
            return {
                "status": "success",
                "profile": profile,
                "duration": duration,
                "data_quality": {
                    "has_name": bool(profile.name),
                    "has_position": bool(profile.position),
                    "has_about": bool(profile.about),
                    "has_experience": len(profile.experience) > 0,
                    "has_education": len(profile.education) > 0,
                    "total_fields": sum([
                        bool(profile.name),
                        bool(profile.position),
                        bool(profile.about),
                        bool(profile.city),
                        bool(profile.followers),
                        bool(profile.connections),
                        len(profile.experience) > 0,
                        len(profile.education) > 0
                    ])
                }
            }
            
        except Exception as e:
            print(f"❌ Profile fetch failed: {e}")
            print(f"   Error type: {type(e).__name__}")
            
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def test_company_fetch(self) -> Dict[str, Any]:
        """Test fetching a real company profile via Cassidy"""
        print("=" * 60)
        print("TESTING REAL CASSIDY COMPANY API")
        print("=" * 60)
        print(f"Company URL: {self.test_company_url}")
        print(f"Cassidy Workflow URL: {settings.CASSIDY_COMPANY_WORKFLOW_URL}")
        print()
        
        try:
            print("🚀 Sending request to Cassidy API...")
            start_time = datetime.now()
            
            company = await self.client.fetch_company(self.test_company_url)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            print(f"✅ Company fetched successfully in {duration:.2f} seconds")
            print()
            print("Company Data:")
            print(f"  ID: {company.company_id}")
            print(f"  Name: {company.company_name}")
            print(f"  Website: {company.website}")
            print(f"  Employee Count: {company.employee_count:,}" if company.employee_count else "  Employee Count: N/A")
            print(f"  Employee Range: {company.employee_range}")
            print(f"  Founded: {company.year_founded}")
            print(f"  Industries: {', '.join(company.industries) if company.industries else 'N/A'}")
            print(f"  HQ Location: {company.hq_city}, {company.hq_region}, {company.hq_country}")
            print(f"  Locations: {len(company.locations)}")
            
            if company.description:
                desc_preview = company.description[:150] + "..." if len(company.description) > 150 else company.description
                print(f"  Description: {desc_preview}")
            
            if company.funding_info:
                print(f"  Funding Info: {company.funding_info}")
            
            print()
            
            return {
                "status": "success",
                "company": company,
                "duration": duration,
                "data_quality": {
                    "has_name": bool(company.company_name),
                    "has_description": bool(company.description),
                    "has_website": bool(company.website),
                    "has_employee_info": bool(company.employee_count or company.employee_range),
                    "has_location": bool(company.hq_city),
                    "has_industries": bool(company.industries),
                    "total_fields": sum([
                        bool(company.company_name),
                        bool(company.description),
                        bool(company.website),
                        bool(company.employee_count),
                        bool(company.hq_city),
                        bool(company.industries),
                        bool(company.year_founded)
                    ])
                }
            }
            
        except Exception as e:
            print(f"❌ Company fetch failed: {e}")
            print(f"   Error type: {type(e).__name__}")
            
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def test_health_check(self) -> Dict[str, Any]:
        """Test Cassidy API health check"""
        print("=" * 60)
        print("TESTING CASSIDY API HEALTH CHECK")
        print("=" * 60)
        
        try:
            health_result = await self.client.health_check()
            
            print("✅ Health check completed")
            print(f"   Status: {health_result.get('status', 'unknown')}")
            print(f"   Response Time: {health_result.get('response_time', 'N/A')} seconds")
            
            if health_result.get('status') == 'healthy':
                print("   🟢 Cassidy API is operational")
            else:
                print("   🟡 Cassidy API may have issues")
            
            return health_result
            
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def test_error_handling(self) -> Dict[str, Any]:
        """Test error handling with invalid URL"""
        print("=" * 60)
        print("TESTING CASSIDY ERROR HANDLING")
        print("=" * 60)
        
        invalid_url = "https://linkedin.com/in/this-profile-does-not-exist-12345"
        print(f"Testing with invalid URL: {invalid_url}")
        
        try:
            profile = await self.client.fetch_profile(invalid_url)
            
            # If we get here, the API might have returned something unexpected
            print("⚠️  Expected error but got response:")
            print(f"   Profile Name: {profile.name}")
            
            return {
                "status": "unexpected_success",
                "profile": profile
            }
            
        except Exception as e:
            print(f"✅ Error handling working correctly")
            print(f"   Caught expected error: {type(e).__name__}")
            print(f"   Error message: {str(e)[:100]}...")
            
            return {
                "status": "expected_error",
                "error": str(e),
                "error_type": type(e).__name__
            }


async def main():
    """Run all real Cassidy API tests"""
    print("🧪 STARTING REAL CASSIDY API INTEGRATION TESTS")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    print("Configuration:")
    print(f"  Profile Workflow: {settings.CASSIDY_PROFILE_WORKFLOW_URL[:50]}...")
    print(f"  Company Workflow: {settings.CASSIDY_COMPANY_WORKFLOW_URL[:50]}...")
    print(f"  Timeout: {settings.CASSIDY_TIMEOUT} seconds")
    print(f"  Max Retries: {settings.CASSIDY_MAX_RETRIES}")
    print()
    
    tester = RealCassidyAPITester()
    results = {}
    
    try:
        # Test 1: Health Check
        print("Test 1: Health Check")
        results["health_check"] = await tester.test_health_check()
        print()
        
        # Test 2: Real Profile Fetch
        print("Test 2: Real Profile Fetch")
        results["profile_fetch"] = await tester.test_profile_fetch()
        print()
        
        # Test 3: Real Company Fetch  
        print("Test 3: Real Company Fetch")
        results["company_fetch"] = await tester.test_company_fetch()
        print()
        
        # Test 4: Error Handling
        print("Test 4: Error Handling")
        results["error_handling"] = await tester.test_error_handling()
        print()
        
        # Summary
        print("=" * 80)
        print("🎯 REAL CASSIDY API TEST SUMMARY")
        print("=" * 80)
        
        successful_tests = sum(1 for result in results.values() 
                             if result.get("status") in ["success", "expected_error", "healthy"])
        total_tests = len(results)
        
        print(f"Tests Passed: {successful_tests}/{total_tests}")
        print()
        
        for test_name, result in results.items():
            status = result.get("status", "unknown")
            if status in ["success", "healthy", "expected_error"]:
                print(f"✅ {test_name.replace('_', ' ').title()}: {status}")
            else:
                print(f"❌ {test_name.replace('_', ' ').title()}: {status}")
        
        print()
        
        # Data Quality Assessment
        if results.get("profile_fetch", {}).get("status") == "success":
            profile_quality = results["profile_fetch"]["data_quality"]
            print(f"📊 Profile Data Quality: {profile_quality['total_fields']}/8 fields populated")
        
        if results.get("company_fetch", {}).get("status") == "success":
            company_quality = results["company_fetch"]["data_quality"]  
            print(f"📊 Company Data Quality: {company_quality['total_fields']}/7 fields populated")
        
        print()
        
        if successful_tests == total_tests:
            print("🎉 ALL REAL CASSIDY API TESTS PASSED!")
            print("The Cassidy integration is working correctly with real LinkedIn data.")
        else:
            print("⚠️  Some tests failed. Check the Cassidy workflow configuration.")
        
        return 0 if successful_tests == total_tests else 1
        
    except Exception as e:
        print(f"💥 Critical test failure: {e}")
        return 1


if __name__ == "__main__":
    print("Note: This test requires valid Cassidy workflow URLs in your configuration.")
    print("If you haven't set up Cassidy workflows yet, the tests will fail.")
    print("See the Cassidy integration guide for setup instructions.")
    print()
    
    exit_code = asyncio.run(main())
    exit(exit_code)
