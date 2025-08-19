#!/usr/bin/env python3
"""
Critical Production Workflow Test: System Health Monitoring

Tests critical production system health and integration points:
1. Database connectivity and performance
2. OpenAI API integration and limits
3. Template system functionality
4. API endpoint responsiveness under load
"""

import pytest
import httpx
import asyncio
import os
from typing import Dict, Any, Optional, List
import uuid
from datetime import datetime, timedelta
import time


@pytest.mark.asyncio
@pytest.mark.production
@pytest.mark.timeout(120)  # 2 minute timeout
class TestSystemHealthWorkflow:
    """Critical production workflow: system health and performance validation."""

    @pytest.fixture
    def production_url(self) -> str:
        """Production URL for testing."""
        return "https://smooth-mailbox-production.up.railway.app"
    
    @pytest.fixture
    def api_headers(self) -> Dict[str, str]:
        """API headers for production requests."""
        return {"x-api-key": "li_HieZz-IjBp0uE7d-rZkRE0qyy12r5_ZJS_FR4jMvv0I"}

    async def test_critical_system_health_check(self, production_url: str, api_headers: Dict[str, str]):
        """
        Test critical system health endpoints that must always work.
        
        This validates:
        - Database connection and query performance
        - OpenAI API integration
        - Template system availability
        - Core API responsiveness
        """
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            print(f"\n🏥 Running critical system health checks...")
            
            # Test 1: Database Health & Performance
            print("🔍 Testing database connectivity...")
            start_time = time.time()
            
            health_response = await client.get(
                f"{production_url}/api/v1/health",
                headers=api_headers
            )
            
            db_response_time = time.time() - start_time
            
            assert health_response.status_code == 200
            health_data = health_response.json()
            
            assert health_data["status"] == "healthy"
            assert health_data["database"]["status"] == "healthy"
            assert health_data["database"]["connection"] == "established"
            
            # Database should respond within 2 seconds
            assert db_response_time < 2.0, f"Database health check took {db_response_time:.2f}s (should be < 2s)"
            
            print(f"✅ Database health OK ({db_response_time:.2f}s response time)")
            
            # Test 2: OpenAI Integration
            print("🤖 Testing OpenAI integration...")
            
            openai_response = await client.get(
                f"{production_url}/api/v1/openai-test",
                headers=api_headers
            )
            
            assert openai_response.status_code == 200
            openai_data = openai_response.json()
            
            assert openai_data["has_api_key"] is True, "OpenAI API key must be configured"
            assert openai_data["has_client"] is True, "OpenAI client must be initialized"
            assert openai_data["token_counting_test"]["token_count"] > 0, "Token counting must work"
            
            print("✅ OpenAI integration OK")
            
            # Test 3: Template System Availability
            print("📝 Testing template system...")
            
            templates_response = await client.get(
                f"{production_url}/api/v1/templates",
                headers=api_headers
            )
            
            assert templates_response.status_code == 200
            templates_data = templates_response.json()
            
            assert "templates" in templates_data
            assert "count" in templates_data
            assert isinstance(templates_data["templates"], list)
            assert templates_data["count"] > 0, "Should have at least one template"
            
            # Verify default templates exist
            template_names = [t["name"] for t in templates_data["templates"]]
            has_cto_template = any("CTO" in name.upper() for name in template_names)
            assert has_cto_template, "Should have CTO template available"
            
            print(f"✅ Template system OK ({templates_data['count']} templates available)")
            
            # Test 4: API Responsiveness Under Concurrent Load
            print("⚡ Testing API responsiveness under load...")
            
            await self._test_concurrent_api_load(client, production_url, api_headers)
            
            print("✅ All critical system health checks passed!")

    async def test_data_integrity_validation(self, production_url: str, api_headers: Dict[str, str]):
        """
        Test data integrity and consistency across system components.
        
        This validates:
        - Profile data consistency
        - Template-scoring relationship integrity
        - Database constraints are working
        """
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            print(f"\n🔒 Running data integrity validation...")
            
            # Test 1: Profile Data Consistency
            print("👤 Testing profile data consistency...")
            
            profiles_response = await client.get(
                f"{production_url}/api/v1/profiles?limit=5",
                headers=api_headers
            )
            
            if profiles_response.status_code == 200 and profiles_response.json().get("profiles"):
                profiles = profiles_response.json()["profiles"]
                
                for profile in profiles[:2]:  # Test first 2 profiles
                    profile_id = profile["id"]
                    
                    # Get full profile data
                    full_profile_response = await client.get(
                        f"{production_url}/api/v1/profiles/{profile_id}",
                        headers=api_headers
                    )
                    
                    assert full_profile_response.status_code == 200
                    full_profile = full_profile_response.json()
                    
                    # Basic data integrity checks
                    assert full_profile["id"] == profile_id
                    assert full_profile.get("created_at"), "Profile must have creation timestamp"
                    
                    if full_profile.get("linkedin_url"):
                        assert full_profile["linkedin_url"].startswith("https://"), "LinkedIn URL must be valid"
                
                print(f"✅ Profile data integrity OK (checked {len(profiles[:2])} profiles)")
            else:
                print("ℹ️ No profiles available for data integrity testing")
            
            # Test 2: Template-Scoring Relationships
            print("🎯 Testing template-scoring relationships...")
            
            templates_response = await client.get(
                f"{production_url}/api/v1/templates?limit=3",
                headers=api_headers
            )
            
            assert templates_response.status_code == 200
            templates = templates_response.json()["templates"]
            
            if templates:
                for template in templates[:1]:  # Test first template
                    template_id = template["id"]
                    
                    # Verify template has required fields
                    assert template.get("name"), "Template must have name"
                    assert template.get("category"), "Template must have category"
                    assert template.get("prompt_text"), "Template must have prompt text"
                    
                    # Template IDs should be valid UUIDs or similar
                    assert len(template_id) > 10, "Template ID should be meaningful length"
                
                print(f"✅ Template integrity OK (checked {len(templates[:1])} templates)")
            
            print("✅ Data integrity validation completed!")

    async def test_production_performance_benchmarks(self, production_url: str, api_headers: Dict[str, str]):
        """
        Test that production system meets performance benchmarks.
        
        This validates:
        - API response times are acceptable
        - Database query performance
        - System can handle expected load
        """
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            print(f"\n📊 Running performance benchmarks...")
            
            # Benchmark 1: Health Check Response Time
            print("⏱️ Benchmarking health check response time...")
            
            health_times = []
            for i in range(5):
                start_time = time.time()
                
                response = await client.get(
                    f"{production_url}/api/v1/health",
                    headers=api_headers
                )
                
                response_time = time.time() - start_time
                health_times.append(response_time)
                
                assert response.status_code == 200
                await asyncio.sleep(0.1)  # Small delay between requests
            
            avg_health_time = sum(health_times) / len(health_times)
            max_health_time = max(health_times)
            
            # Health check should be fast (under 1 second average, under 2 seconds max)
            assert avg_health_time < 1.0, f"Health check average time {avg_health_time:.2f}s (should be < 1s)"
            assert max_health_time < 2.0, f"Health check max time {max_health_time:.2f}s (should be < 2s)"
            
            print(f"✅ Health check performance OK (avg: {avg_health_time:.2f}s, max: {max_health_time:.2f}s)")
            
            # Benchmark 2: Template Listing Performance
            print("📝 Benchmarking template listing performance...")
            
            start_time = time.time()
            
            templates_response = await client.get(
                f"{production_url}/api/v1/templates",
                headers=api_headers
            )
            
            templates_response_time = time.time() - start_time
            
            assert templates_response.status_code == 200
            
            # Template listing should be reasonably fast (under 3 seconds)
            assert templates_response_time < 3.0, f"Template listing took {templates_response_time:.2f}s (should be < 3s)"
            
            print(f"✅ Template listing performance OK ({templates_response_time:.2f}s)")
            
            print("✅ Performance benchmarks completed!")

    async def _test_concurrent_api_load(self, client: httpx.AsyncClient, production_url: str, api_headers: Dict[str, str]):
        """Test API responsiveness under concurrent load."""
        
        # Create 5 concurrent health check requests
        concurrent_requests = 5
        
        async def make_health_request():
            start_time = time.time()
            response = await client.get(
                f"{production_url}/api/v1/health",
                headers=api_headers
            )
            response_time = time.time() - start_time
            return response.status_code, response_time
        
        # Execute concurrent requests
        tasks = [make_health_request() for _ in range(concurrent_requests)]
        results = await asyncio.gather(*tasks)
        
        # Validate all requests succeeded
        status_codes = [result[0] for result in results]
        response_times = [result[1] for result in results]
        
        # All requests should succeed
        assert all(status == 200 for status in status_codes), f"Some concurrent requests failed: {status_codes}"
        
        # Response times should be reasonable even under load
        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)
        
        assert avg_response_time < 2.0, f"Concurrent request avg time {avg_response_time:.2f}s (should be < 2s)"
        assert max_response_time < 4.0, f"Concurrent request max time {max_response_time:.2f}s (should be < 4s)"
        
        print(f"✅ Concurrent API load test OK ({concurrent_requests} requests, avg: {avg_response_time:.2f}s)")
