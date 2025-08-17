#!/usr/bin/env python3
"""
Production Integration Tests

End-to-end tests that validate the production deployment of the
LLM scoring system with template management integration.
"""

import pytest
import httpx
import asyncio
import os
from typing import Dict, Any, Optional
import uuid
from datetime import datetime


@pytest.mark.integration
@pytest.mark.production
class TestProductionIntegration:
    """Production environment integration tests for template-based scoring."""

    @pytest.fixture
    def production_url(self) -> str:
        """Production URL for testing."""
        return "https://smooth-mailbox-production.up.railway.app"
    
    @pytest.fixture
    def api_headers(self) -> Dict[str, str]:
        """API headers for production requests."""
        return {"x-api-key": "li_HieZz-IjBp0uE7d-rZkRE0qyy12r5_ZJS_FR4jMvv0I"}
    
    @pytest.fixture
    def test_profile_id(self) -> str:
        """Known test profile ID in production."""
        return "435ccbf7-6c5e-4e2d-bdc3-052a244d7121"

    @pytest.mark.asyncio
    async def test_health_check_production(self, production_url: str, api_headers: Dict[str, str]):
        """Test that production health check includes all services."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{production_url}/api/v1/health", headers=api_headers)
        
        assert response.status_code == 200
        health_data = response.json()
        
        # Verify basic health structure
        assert health_data["status"] == "healthy"
        assert "timestamp" in health_data
        assert "version" in health_data
        assert "database" in health_data
        
        # Verify database health
        db_health = health_data["database"]
        assert db_health["status"] == "healthy"
        assert db_health["connection"] == "established"

    @pytest.mark.asyncio
    async def test_template_system_production_health(self, production_url: str, api_headers: Dict[str, str]):
        """Test template system health in production."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test template listing
            response = await client.get(f"{production_url}/api/v1/templates", headers=api_headers)
        
        assert response.status_code == 200
        templates_data = response.json()
        
        assert "templates" in templates_data
        assert "count" in templates_data
        assert isinstance(templates_data["templates"], list)
        
        # Verify default templates exist
        template_names = [t["name"] for t in templates_data["templates"]]
        assert any("CTO" in name for name in template_names), "Should have CTO template"

    @pytest.mark.asyncio
    async def test_openai_service_health(self, production_url: str, api_headers: Dict[str, str]):
        """Test OpenAI service configuration in production."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{production_url}/api/v1/openai-test", headers=api_headers)
        
        assert response.status_code == 200
        openai_data = response.json()
        
        # Verify OpenAI is configured
        assert openai_data["has_api_key"] is True, "OpenAI API key should be configured in production"
        assert openai_data["has_client"] is True, "OpenAI client should be initialized"
        assert "token_counting_test" in openai_data
        assert openai_data["token_counting_test"]["token_count"] > 0

    @pytest.mark.asyncio
    async def test_end_to_end_template_scoring(self, production_url: str, api_headers: Dict[str, str]):
        """Test complete end-to-end template-based scoring workflow in production."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Step 1: Get available templates
            templates_response = await client.get(
                f"{production_url}/api/v1/templates?category=CTO",
                headers=api_headers
            )
            assert templates_response.status_code == 200
            templates = templates_response.json()["templates"]
            
            # Find a CTO template
            cto_template = None
            for template in templates:
                if "CTO" in template["name"]:
                    cto_template = template
                    break
            
            assert cto_template is not None, "Should have a CTO template available"
            
            # Step 2: Create scoring job using template
            scoring_request = {
                "template_id": cto_template["id"]
            }
            
            scoring_response = await client.post(
                f"{production_url}/api/v1/profiles/{self.test_profile_id}/score",
                json=scoring_request,
                headers=api_headers,
                timeout=30.0
            )
            
            print(f"Scoring response status: {scoring_response.status_code}")
            print(f"Scoring response: {scoring_response.text}")
            
            # In production, this might return 404 if profile doesn't exist or 202 if it does
            # Both are valid depending on test data state
            assert scoring_response.status_code in [202, 404], f"Expected 202 or 404, got {scoring_response.status_code}"
            
            if scoring_response.status_code == 202:
                job_data = scoring_response.json()
                assert "job_id" in job_data
                assert job_data["template_id"] == cto_template["id"]
                assert job_data["status"] == "pending"
                
                # Step 3: Check job status
                job_id = job_data["job_id"]
                status_response = await client.get(
                    f"{production_url}/api/v1/scoring-jobs/{job_id}",
                    headers=api_headers
                )
                assert status_response.status_code == 200
                
                status_data = status_response.json()
                assert status_data["id"] == job_id
                assert status_data["template_id"] == cto_template["id"]
                assert status_data["status"] in ["pending", "completed", "failed"]

    @pytest.mark.asyncio
    async def test_template_crud_operations_production(self, production_url: str, api_headers: Dict[str, str]):
        """Test template CRUD operations work in production environment."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Create unique test template
            unique_suffix = str(uuid.uuid4())[:8]
            template_data = {
                "name": f"Production Test Template {unique_suffix}",
                "category": "TEST",
                "prompt_text": "Test prompt for production validation",
                "description": "Temporary template for production testing"
            }
            
            # Create template
            create_response = await client.post(
                f"{production_url}/api/v1/templates",
                json=template_data,
                headers=api_headers
            )
            assert create_response.status_code == 201
            
            created_template = create_response.json()
            template_id = created_template["id"]
            assert created_template["name"] == template_data["name"]
            assert created_template["category"] == "TEST"
            
            # Update template
            update_data = {
                "description": "Updated description for production test"
            }
            update_response = await client.put(
                f"{production_url}/api/v1/templates/{template_id}",
                json=update_data,
                headers=api_headers
            )
            assert update_response.status_code == 200
            
            updated_template = update_response.json()
            assert updated_template["description"] == update_data["description"]
            
            # Get template
            get_response = await client.get(
                f"{production_url}/api/v1/templates/{template_id}",
                headers=api_headers
            )
            assert get_response.status_code == 200
            
            retrieved_template = get_response.json()
            assert retrieved_template["id"] == template_id
            assert retrieved_template["description"] == update_data["description"]
            
            # Delete template (cleanup)
            delete_response = await client.delete(
                f"{production_url}/api/v1/templates/{template_id}",
                headers=api_headers
            )
            assert delete_response.status_code == 200
            
            # Verify deletion (soft delete - template should be inactive)
            verify_response = await client.get(
                f"{production_url}/api/v1/templates/{template_id}",
                headers=api_headers
            )
            # Template may still exist but be inactive (soft delete)
            if verify_response.status_code == 200:
                template_data = verify_response.json()
                assert template_data["is_active"] is False, "Template should be inactive after deletion"
            else:
                assert verify_response.status_code == 404, "Template should be not found after deletion"

    @pytest.mark.asyncio
    async def test_production_performance_characteristics(self, production_url: str, api_headers: Dict[str, str]):
        """Test production performance characteristics."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test template listing performance
            start_time = datetime.now()
            response = await client.get(f"{production_url}/api/v1/templates", headers=api_headers)
            response_time = (datetime.now() - start_time).total_seconds()
            
            assert response.status_code == 200
            assert response_time < 5.0, f"Template listing took {response_time}s, should be < 5s"
            
            # Test health check performance
            start_time = datetime.now()
            health_response = await client.get(f"{production_url}/api/v1/health", headers=api_headers)
            health_time = (datetime.now() - start_time).total_seconds()
            
            assert health_response.status_code == 200
            assert health_time < 2.0, f"Health check took {health_time}s, should be < 2s"

    @pytest.mark.asyncio
    async def test_authentication_and_security(self, production_url: str):
        """Test authentication and security measures."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test that endpoints require authentication
            endpoints = [
                "/api/v1/templates",
                "/api/v1/health",
                "/api/v1/openai-test"
            ]
            
            for endpoint in endpoints:
                response = await client.get(f"{production_url}{endpoint}")
                assert response.status_code == 401, f"Endpoint {endpoint} should require authentication"
            
            # Test invalid API key
            invalid_headers = {"x-api-key": "invalid-key"}
            for endpoint in endpoints:
                response = await client.get(f"{production_url}{endpoint}", headers=invalid_headers)
                assert response.status_code == 403, f"Endpoint {endpoint} should reject invalid API key"

    @pytest.mark.asyncio
    async def test_error_handling_production(self, production_url: str, api_headers: Dict[str, str]):
        """Test error handling in production environment."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test non-existent template
            response = await client.get(
                f"{production_url}/api/v1/templates/non-existent-id",
                headers=api_headers
            )
            assert response.status_code == 404
            error_data = response.json()
            assert "error" in error_data
            
            # Test invalid template creation
            invalid_template = {
                "name": "",  # Empty name should fail
                "category": "TEST",
                "prompt_text": "Test"
            }
            response = await client.post(
                f"{production_url}/api/v1/templates",
                json=invalid_template,
                headers=api_headers
            )
            assert response.status_code == 422  # Validation error
            
            # Test scoring with non-existent template
            scoring_request = {
                "template_id": "non-existent-template-id"
            }
            response = await client.post(
                f"{production_url}/api/v1/profiles/some-profile-id/score",
                json=scoring_request,
                headers=api_headers
            )
            assert response.status_code in [400, 404]  # Template not found or profile not found


@pytest.mark.integration
class TestProductionHealthMonitoring:
    """Test production health monitoring capabilities."""

    @pytest.fixture
    def production_url(self) -> str:
        return "https://smooth-mailbox-production.up.railway.app"
    
    @pytest.fixture
    def api_headers(self) -> Dict[str, str]:
        return {"x-api-key": "li_HieZz-IjBp0uE7d-rZkRE0qyy12r5_ZJS_FR4jMvv0I"}

    @pytest.mark.asyncio
    async def test_comprehensive_system_health(self, production_url: str, api_headers: Dict[str, str]):
        """Test comprehensive system health monitoring."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test multiple services concurrently
            tasks = [
                client.get(f"{production_url}/api/v1/health", headers=api_headers),
                client.get(f"{production_url}/api/v1/templates", headers=api_headers),
                client.get(f"{production_url}/api/v1/openai-test", headers=api_headers),
            ]
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # All requests should succeed
            for i, response in enumerate(responses):
                assert not isinstance(response, Exception), f"Request {i} failed: {response}"
                assert response.status_code == 200, f"Request {i} returned {response.status_code}"

    @pytest.mark.asyncio
    async def test_service_availability_monitoring(self, production_url: str, api_headers: Dict[str, str]):
        """Test service availability for monitoring purposes."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test core service endpoints
            endpoints_to_test = [
                ("/", "GET"),
                ("/api/v1/health", "GET"),
                ("/api/v1/templates", "GET"),
                ("/api/v1/openai-test", "GET"),
            ]
            
            availability_results = {}
            
            for endpoint, method in endpoints_to_test:
                try:
                    if endpoint == "/":
                        response = await client.get(f"{production_url}{endpoint}")
                    else:
                        response = await client.get(f"{production_url}{endpoint}", headers=api_headers)
                    
                    availability_results[endpoint] = {
                        "status_code": response.status_code,
                        "available": response.status_code < 500,
                        "response_time_ms": response.elapsed.total_seconds() * 1000 if hasattr(response, 'elapsed') else 0
                    }
                except Exception as e:
                    availability_results[endpoint] = {
                        "status_code": None,
                        "available": False,
                        "error": str(e)
                    }
            
            # Verify core services are available
            assert availability_results["/"]["available"], "Root endpoint should be available"
            assert availability_results["/api/v1/health"]["available"], "Health endpoint should be available"
            assert availability_results["/api/v1/templates"]["available"], "Templates endpoint should be available"
            
            print(f"Service availability results: {availability_results}")


if __name__ == "__main__":
    # Run production tests
    pytest.main([__file__, "-v", "-m", "production"])
