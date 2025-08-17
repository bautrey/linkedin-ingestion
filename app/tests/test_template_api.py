"""
Integration tests for V1.88 Template Management API endpoints

Tests the FastAPI endpoints for template CRUD operations with proper mocking
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from datetime import datetime, timezone
from uuid import UUID
import json

from main import app
from app.models.template_models import (
    PromptTemplate,
    CreateTemplateRequest,
    UpdateTemplateRequest,
    TemplateSummary
)


# Test client setup
client = TestClient(app)

# Mock API key for testing
TEST_API_KEY = "test-api-key-12345"


class TestTemplateAPIEndpoints:
    """Test the Template Management API endpoints"""

    @pytest.fixture(autouse=True)
    def setup_api_key_mock(self):
        """Mock the API key verification for all tests"""
        with patch('main.settings.API_KEY', TEST_API_KEY):
            yield

    @pytest.fixture
    def sample_template(self):
        """Sample template for testing"""
        return PromptTemplate(
            id=UUID("123e4567-e89b-12d3-a456-426614174000"),
            name="Test CTO Template",
            category="CTO",
            prompt_text="Evaluate this candidate for CTO role...",
            version=1,
            is_active=True,
            description="Test template description",
            metadata={"tags": ["test"]},
            created_at=datetime(2025, 8, 13, 12, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2025, 8, 13, 12, 0, 0, tzinfo=timezone.utc)
        )

    @pytest.fixture
    def sample_template_summary(self):
        """Sample template summary for testing"""
        return TemplateSummary(
            id=UUID("123e4567-e89b-12d3-a456-426614174000"),
            name="Test CTO Template",
            category="CTO",
            description="Test template description",
            version=1,
            is_active=True,
            created_at=datetime(2025, 8, 13, 12, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2025, 8, 13, 12, 0, 0, tzinfo=timezone.utc),
            metadata={"tags": ["test"]}
        )

    @patch('main.get_template_service')
    def test_list_templates_success(self, mock_get_service, sample_template):
        """Test successful template listing"""
        # Mock the service
        mock_service = AsyncMock()
        mock_service.list_templates.return_value = [sample_template]
        mock_get_service.return_value = mock_service

        response = client.get(
            "/api/v1/templates",
            headers={"X-API-Key": TEST_API_KEY}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert len(data["templates"]) == 1
        assert data["templates"][0]["name"] == "Test CTO Template"
        assert data["templates"][0]["category"] == "CTO"

        # Verify service was called correctly
        mock_service.list_templates.assert_called_once_with(
            category=None,
            include_inactive=False,
            limit=None
        )

    @patch('main.get_template_service')
    def test_list_templates_with_filters(self, mock_get_service, sample_template):
        """Test template listing with category filter"""
        mock_service = AsyncMock()
        mock_service.list_templates.return_value = [sample_template]
        mock_get_service.return_value = mock_service

        response = client.get(
            "/api/v1/templates?category=CTO&include_inactive=true&limit=10",
            headers={"X-API-Key": TEST_API_KEY}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1

        # Verify service was called with correct filters
        mock_service.list_templates.assert_called_once_with(
            category="CTO",
            include_inactive=True,
            limit=10
        )

    @patch('main.get_template_service')
    def test_list_templates_unauthorized(self, mock_get_service):
        """Test template listing without API key"""
        response = client.get("/api/v1/templates")
        
        assert response.status_code == 403
        data = response.json()
        assert data["detail"]["error_code"] == "UNAUTHORIZED"

    @patch('main.get_template_service')
    def test_list_templates_service_error(self, mock_get_service):
        """Test template listing with service error"""
        mock_service = AsyncMock()
        mock_service.list_templates.side_effect = Exception("Database error")
        mock_get_service.return_value = mock_service

        response = client.get(
            "/api/v1/templates",
            headers={"X-API-Key": TEST_API_KEY}
        )

        assert response.status_code == 500
        data = response.json()
        assert data["detail"]["error_code"] == "TEMPLATE_LIST_FAILED"

    @patch('main.get_template_service')
    def test_list_template_summaries_success(self, mock_get_service, sample_template_summary):
        """Test successful template summaries listing"""
        mock_service = AsyncMock()
        mock_service.list_template_summaries.return_value = [sample_template_summary]
        mock_get_service.return_value = mock_service

        response = client.get(
            "/api/v1/templates/summaries",
            headers={"X-API-Key": TEST_API_KEY}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert len(data["templates"]) == 1
        assert data["templates"][0]["name"] == "Test CTO Template"
        # Should not include prompt_text in summaries
        assert "prompt_text" not in data["templates"][0]

        mock_service.list_template_summaries.assert_called_once_with(
            category=None,
            include_inactive=False,
            limit=None
        )

    @patch('main.get_template_service')
    def test_get_template_success(self, mock_get_service, sample_template):
        """Test successful template retrieval by ID"""
        mock_service = AsyncMock()
        mock_service.get_template_by_id.return_value = sample_template
        mock_get_service.return_value = mock_service

        template_id = "123e4567-e89b-12d3-a456-426614174000"
        response = client.get(
            f"/api/v1/templates/{template_id}",
            headers={"X-API-Key": TEST_API_KEY}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test CTO Template"
        assert data["category"] == "CTO"
        assert data["prompt_text"] == "Evaluate this candidate for CTO role..."

        mock_service.get_template_by_id.assert_called_once_with(template_id)

    @patch('main.get_template_service')
    def test_get_template_not_found(self, mock_get_service):
        """Test template retrieval when template doesn't exist"""
        mock_service = AsyncMock()
        mock_service.get_template_by_id.return_value = None
        mock_get_service.return_value = mock_service

        template_id = "nonexistent-id"
        response = client.get(
            f"/api/v1/templates/{template_id}",
            headers={"X-API-Key": TEST_API_KEY}
        )

        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["error_code"] == "TEMPLATE_NOT_FOUND"

    @patch('main.get_template_service')
    def test_create_template_success(self, mock_get_service, sample_template):
        """Test successful template creation"""
        mock_service = AsyncMock()
        mock_service.create_template.return_value = sample_template
        mock_get_service.return_value = mock_service

        template_data = {
            "name": "New CTO Template",
            "category": "CTO",
            "prompt_text": "New evaluation prompt for CTO candidates",
            "description": "Custom CTO evaluation",
            "is_active": True,
            "metadata": {"created_by": "test"}
        }

        response = client.post(
            "/api/v1/templates",
            headers={"X-API-Key": TEST_API_KEY},
            json=template_data
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test CTO Template"  # From mock return value
        assert data["category"] == "CTO"

        # Verify service was called with correct data
        mock_service.create_template.assert_called_once()
        call_args = mock_service.create_template.call_args[0][0]
        assert call_args.name == "New CTO Template"
        assert call_args.category == "CTO"
        assert call_args.prompt_text == "New evaluation prompt for CTO candidates"

    @patch('main.get_template_service')
    def test_create_template_validation_error(self, mock_get_service):
        """Test template creation with invalid data"""
        mock_service = AsyncMock()
        mock_get_service.return_value = mock_service

        # Missing required fields
        template_data = {
            "name": "Test Template"
            # Missing category and prompt_text
        }

        response = client.post(
            "/api/v1/templates",
            headers={"X-API-Key": TEST_API_KEY},
            json=template_data
        )

        assert response.status_code == 422
        data = response.json()
        assert data["error_code"] == "VALIDATION_ERROR"

    @patch('main.get_template_service')
    def test_update_template_success(self, mock_get_service, sample_template):
        """Test successful template update"""
        # Create updated template
        updated_template = sample_template.model_copy(deep=True)
        updated_template.name = "Updated Template Name"
        updated_template.description = "Updated description"

        mock_service = AsyncMock()
        mock_service.update_template.return_value = updated_template
        mock_get_service.return_value = mock_service

        template_id = "123e4567-e89b-12d3-a456-426614174000"
        update_data = {
            "name": "Updated Template Name",
            "description": "Updated description"
        }

        response = client.put(
            f"/api/v1/templates/{template_id}",
            headers={"X-API-Key": TEST_API_KEY},
            json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Template Name"
        assert data["description"] == "Updated description"

        mock_service.update_template.assert_called_once()
        call_args = mock_service.update_template.call_args
        assert call_args[0][0] == template_id  # First arg is template_id
        assert call_args[0][1].name == "Updated Template Name"  # Second arg is UpdateTemplateRequest

    @patch('main.get_template_service')
    def test_update_template_not_found(self, mock_get_service):
        """Test template update when template doesn't exist"""
        mock_service = AsyncMock()
        mock_service.update_template.return_value = None
        mock_get_service.return_value = mock_service

        template_id = "nonexistent-id"
        update_data = {"name": "Updated Name"}

        response = client.put(
            f"/api/v1/templates/{template_id}",
            headers={"X-API-Key": TEST_API_KEY},
            json=update_data
        )

        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["error_code"] == "TEMPLATE_NOT_FOUND"

    @patch('main.get_template_service')
    def test_delete_template_success(self, mock_get_service):
        """Test successful template deletion"""
        mock_service = AsyncMock()
        mock_service.delete_template.return_value = True
        mock_get_service.return_value = mock_service

        template_id = "123e4567-e89b-12d3-a456-426614174000"
        response = client.delete(
            f"/api/v1/templates/{template_id}",
            headers={"X-API-Key": TEST_API_KEY}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Template successfully deactivated"
        assert data["template_id"] == template_id

        mock_service.delete_template.assert_called_once_with(template_id)

    @patch('main.get_template_service')
    def test_delete_template_not_found(self, mock_get_service):
        """Test template deletion when template doesn't exist"""
        mock_service = AsyncMock()
        mock_service.delete_template.return_value = False
        mock_get_service.return_value = mock_service

        template_id = "nonexistent-id"
        response = client.delete(
            f"/api/v1/templates/{template_id}",
            headers={"X-API-Key": TEST_API_KEY}
        )

        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["error_code"] == "TEMPLATE_NOT_FOUND"

    def test_template_endpoints_require_authentication(self):
        """Test that all template endpoints require API key authentication"""
        endpoints = [
            ("GET", "/api/v1/templates"),
            ("GET", "/api/v1/templates/summaries"),
            ("GET", "/api/v1/templates/test-id"),
            ("POST", "/api/v1/templates"),
            ("PUT", "/api/v1/templates/test-id"),
            ("DELETE", "/api/v1/templates/test-id")
        ]

        for method, url in endpoints:
            if method == "GET":
                response = client.get(url)
            elif method == "POST":
                response = client.post(url, json={})
            elif method == "PUT":
                response = client.put(url, json={})
            elif method == "DELETE":
                response = client.delete(url)

            assert response.status_code == 403, f"Endpoint {method} {url} should require authentication"
            data = response.json()
            assert data["detail"]["error_code"] == "UNAUTHORIZED"

    @patch('main.get_template_service')
    def test_template_endpoints_error_logging(self, mock_get_service):
        """Test that template endpoints log errors appropriately"""
        mock_service = AsyncMock()
        mock_service.list_templates.side_effect = Exception("Test database error")
        mock_get_service.return_value = mock_service

        with patch('main.logger') as mock_logger:
            response = client.get(
                "/api/v1/templates",
                headers={"X-API-Key": TEST_API_KEY}
            )

            assert response.status_code == 500
            
            # Verify error was logged
            mock_logger.error.assert_called_once()
            log_call = mock_logger.error.call_args
            assert "Failed to list templates" in log_call[0][0]

    @patch('main.get_template_service')
    def test_create_template_success_logging(self, mock_get_service, sample_template):
        """Test that successful template creation is logged"""
        mock_service = AsyncMock()
        mock_service.create_template.return_value = sample_template
        mock_get_service.return_value = mock_service

        template_data = {
            "name": "New Template",
            "category": "CTO",
            "prompt_text": "Test prompt"
        }

        with patch('main.logger') as mock_logger:
            response = client.post(
                "/api/v1/templates",
                headers={"X-API-Key": TEST_API_KEY},
                json=template_data
            )

            assert response.status_code == 201
            
            # Verify success was logged
            mock_logger.info.assert_called_once()
            log_call = mock_logger.info.call_args
            assert "Template created successfully" in log_call[0][0]

    @patch('main.get_template_service')  
    def test_query_parameter_validation(self, mock_get_service, sample_template):
        """Test query parameter validation for template listing"""
        mock_service = AsyncMock()
        mock_service.list_templates.return_value = [sample_template]
        mock_get_service.return_value = mock_service

        # Test invalid limit (too high)
        response = client.get(
            "/api/v1/templates?limit=200",
            headers={"X-API-Key": TEST_API_KEY}
        )

        assert response.status_code == 422
        data = response.json()
        assert data["error_code"] == "VALIDATION_ERROR"

        # Test invalid limit (negative)
        response = client.get(
            "/api/v1/templates?limit=-1",
            headers={"X-API-Key": TEST_API_KEY}
        )

        assert response.status_code == 422

    @patch('main.get_template_service')
    def test_template_id_uuid_format_handling(self, mock_get_service, sample_template):
        """Test that template endpoints handle UUID format correctly"""
        mock_service = AsyncMock()
        mock_service.get_template_by_id.return_value = sample_template
        mock_get_service.return_value = mock_service

        # Test with valid UUID format
        valid_uuid = "123e4567-e89b-12d3-a456-426614174000"
        response = client.get(
            f"/api/v1/templates/{valid_uuid}",
            headers={"X-API-Key": TEST_API_KEY}
        )

        assert response.status_code == 200

        # Test with invalid UUID format - should still work as it's just a string parameter
        invalid_uuid = "not-a-uuid"
        mock_service.get_template_by_id.return_value = None
        response = client.get(
            f"/api/v1/templates/{invalid_uuid}",
            headers={"X-API-Key": TEST_API_KEY}
        )

        # Should return 404 (not found) rather than validation error
        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["error_code"] == "TEMPLATE_NOT_FOUND"
