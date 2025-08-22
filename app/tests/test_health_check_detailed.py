#!/usr/bin/env python3
"""
Test Enhanced LinkedIn Health Check System

This script tests the new health check system that validates actual
LinkedIn service integration without database writes.
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any

from app.cassidy.health_checker import LinkedInHealthChecker


class HealthCheckTester:
    """Test the enhanced health check system"""
    
    def __init__(self):
        self.health_checker = LinkedInHealthChecker()
    
    async def test_quick_health_check(self) -> Dict[str, Any]:
        """Test the quick health check (API connectivity only)"""
        print("=" * 60)
        print("TESTING QUICK HEALTH CHECK (API CONNECTIVITY)")
        print("=" * 60)
        
        try:
            start_time = datetime.now()
            result = await self.health_checker.quick_health_check()
            end_time = datetime.now()
            
            duration = (end_time - start_time).total_seconds()
            
            print(f"✅ Quick health check completed in {duration:.2f} seconds")
            print(f"   Status: {result['status']}")
            print(f"   Response Time: {result['response_time_ms']:.2f}ms")
            
            if result.get('error'):
                print(f"   ⚠️  Error: {result['error']}")
            
            return result
            
        except Exception as e:
            print(f"❌ Quick health check failed: {e}")
            return {"status": "error", "error": str(e)}
    
    async def test_comprehensive_health_check(self) -> Dict[str, Any]:
        """Test the comprehensive health check (full LinkedIn integration)"""
        print("\n" + "=" * 60)
        print("TESTING COMPREHENSIVE HEALTH CHECK (FULL INTEGRATION)")
        print("=" * 60)
        
        try:
            start_time = datetime.now()
            result = await self.health_checker.comprehensive_health_check()
            end_time = datetime.now()
            
            duration = (end_time - start_time).total_seconds()
            
            print(f"✅ Comprehensive health check completed in {duration:.2f} seconds")
            print(f"   Overall Status: {result['overall_status']}")
            print(f"   Execution Time: {result.get('execution_time_seconds', 0):.2f}s")
            print(f"   Errors: {len(result.get('errors', []))}")
            print(f"   Warnings: {len(result.get('warnings', []))}")
            
            # Print individual check results
            print("\n📊 Individual Check Results:")
            checks = result.get('checks', {})
            
            for check_name, check_data in checks.items():
                status = check_data.get('status', 'unknown')
                response_time = check_data.get('response_time_ms', 0)
                print(f"   {check_name}: {status} ({response_time:.2f}ms)")
                
                if check_data.get('error'):
                    print(f"      ❌ Error: {check_data['error']}")
                
                # Print additional details for profile/company checks
                if 'data_quality' in check_data.get('details', {}):
                    quality = check_data['details']['data_quality']
                    completeness = quality.get('data_completeness_percent', 0)
                    print(f"      📈 Data Completeness: {completeness:.1f}%")
            
            # Print metrics
            print("\n📈 Quality Metrics:")
            metrics = result.get('metrics', {})
            
            if 'data_quality' in metrics:
                dq = metrics['data_quality']
                print(f"   Fields Populated: {dq.get('fields_populated', 0)}/{dq.get('total_expected_fields', 0)}")
                print(f"   Has Core Data: {dq.get('has_core_data', False)}")
                print(f"   Validation Passed: {dq.get('validation_passed', False)}")
            
            if 'performance' in metrics:
                perf = metrics['performance']
                print(f"   Total Requests: {perf.get('total_requests_made', 0)}")
                print(f"   Failed Requests: {perf.get('failed_requests', 0)}")
                print(f"   Success Rate: {perf.get('success_rate_percent', 0):.1f}%")
            
            # Print errors and warnings if any
            if result.get('errors'):
                print("\n❌ Errors:")
                for error in result['errors']:
                    print(f"   {error['service']}: {error['error']}")
            
            if result.get('warnings'):
                print("\n⚠️  Warnings:")
                for warning in result['warnings']:
                    print(f"   {warning['service']}: {warning['message']}")
            
            return result
            
        except Exception as e:
            print(f"❌ Comprehensive health check failed: {e}")
            return {"overall_status": "error", "error": str(e)}
    
    async def test_individual_components(self):
        """Test individual health check components"""
        print("\n" + "=" * 60)
        print("TESTING INDIVIDUAL COMPONENTS")
        print("=" * 60)
        
        # Test API connectivity
        try:
            print("\n🔌 Testing API Connectivity...")
            api_result = await self.health_checker._check_api_connectivity()
            print(f"   Status: {api_result.status}")
            print(f"   Response Time: {api_result.response_time_ms:.2f}ms")
            if api_result.error:
                print(f"   Error: {api_result.error}")
        except Exception as e:
            print(f"   ❌ API connectivity test failed: {e}")
        
        # Test profile ingestion
        try:
            print("\n👤 Testing Profile Ingestion...")
            profile_result = await self.health_checker._check_profile_ingestion()
            print(f"   Status: {profile_result.status}")
            print(f"   Response Time: {profile_result.response_time_ms:.2f}ms")
            
            if profile_result.details:
                details = profile_result.details
                print(f"   Test Profile: {details.get('test_profile_url', 'N/A')}")
                print(f"   Profile Name: {details.get('profile_name', 'N/A')}")
                print(f"   Experience Count: {details.get('experience_count', 0)}")
                print(f"   Education Count: {details.get('education_count', 0)}")
                
                if 'data_quality' in details:
                    dq = details['data_quality']
                    print(f"   Data Completeness: {dq.get('data_completeness_percent', 0):.1f}%")
            
            if profile_result.error:
                print(f"   Error: {profile_result.error}")
                
        except Exception as e:
            print(f"   ❌ Profile ingestion test failed: {e}")
        
        # Test company ingestion
        try:
            print("\n🏢 Testing Company Ingestion...")
            company_result = await self.health_checker._check_company_ingestion()
            print(f"   Status: {company_result.status}")
            print(f"   Response Time: {company_result.response_time_ms:.2f}ms")
            
            if company_result.details:
                details = company_result.details
                print(f"   Test Company: {details.get('test_company_url', 'N/A')}")
                print(f"   Company Name: {details.get('company_name', 'N/A')}")
                print(f"   Employee Count: {details.get('employee_count', 'N/A')}")
                print(f"   Industries Count: {details.get('industries_count', 0)}")
                
                if 'data_quality' in details:
                    dq = details['data_quality']
                    print(f"   Data Completeness: {dq.get('data_completeness_percent', 0):.1f}%")
            
            if company_result.error:
                print(f"   Error: {company_result.error}")
                
        except Exception as e:
            print(f"   ❌ Company ingestion test failed: {e}")
    
    def print_test_profiles(self):
        """Print the test profiles being used"""
        print("\n" + "=" * 60)
        print("TEST PROFILES CONFIGURATION")
        print("=" * 60)
        
        print("📋 Test Profiles:")
        for name, url in self.health_checker.TEST_PROFILES.items():
            print(f"   {name}: {url}")
        
        print("\n🏢 Test Companies:")
        for name, url in self.health_checker.TEST_COMPANIES.items():
            print(f"   {name}: {url}")
        
        print("\n💡 These are public LinkedIn profiles/companies used for testing.")
        print("   No data is saved to the database during health checks.")


async def main():
    """Main test function"""
    print("🚀 Enhanced LinkedIn Health Check System Test")
    print("=" * 60)
    print("This test validates the LinkedIn service integration")
    print("WITHOUT saving any data to the database.")
    print()
    
    tester = HealthCheckTester()
    
    # Print configuration
    tester.print_test_profiles()
    
    # Test individual components
    await tester.test_individual_components()
    
    # Test quick health check
    await tester.test_quick_health_check()
    
    # Test comprehensive health check  
    await tester.test_comprehensive_health_check()
    
    print("\n" + "=" * 60)
    print("✅ ENHANCED HEALTH CHECK SYSTEM TEST COMPLETED")
    print("=" * 60)
    print("You can now use these endpoints in your application:")
    print("   GET /health/detailed      - Basic + LinkedIn quick check")
    print("   GET /health/linkedin      - Comprehensive LinkedIn integration check")
    print()
    print("💡 These health checks can be used for:")
    print("   - Production monitoring and alerting")
    print("   - Detecting API format changes")
    print("   - Validating service connectivity")
    print("   - Performance monitoring")


if __name__ == "__main__":
    asyncio.run(main())
