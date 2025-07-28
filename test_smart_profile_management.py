"""
Unit tests for Task 3: Smart Profile Management

Tests the enhanced ProfileCreateRequest model and create_profile logic
for duplicate handling, force_create, and include_companies options
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from main import app, ProfileController, ProfileCreateRequest
from app.database.supabase_client import SupabaseClient
from app.cassidy.workflows import LinkedInWorkflow
from app.cassidy.models import ProfileIngestionRequest
from app.core.config import settings


class TestProfileCreateRequest:
    """Test the enhanced ProfileCreateRequest model"""

    def test_default_values(self):
        """Test default values for new fields"""
        request = ProfileCreateRequest(linkedin_url="https://linkedin.com/in/test")
        
        assert request.include_companies is True
        assert request.name is None

    def test_custom_values(self):
        """Test custom values for new fields"""
        request = ProfileCreateRequest(
            linkedin_url="https://linkedin.com/in/test",
            name="Test User",
            include_companies=False
        )
        
        assert request.include_companies is False
        assert request.name == "Test User"


class TestSmartProfileManagement:
    """Test smart profile management functionality"""

    @pytest.fixture
    def mock_controller(self):
        """Create a mocked ProfileController"""
        mock_db = AsyncMock(spec=SupabaseClient)
        mock_cassidy = AsyncMock()
        mock_workflow = AsyncMock(spec=LinkedInWorkflow)
        
        controller = ProfileController(mock_db, mock_cassidy, mock_workflow)
        return controller, mock_db, mock_workflow

    @pytest.mark.asyncio
    async def test_create_profile_no_existing_profile(self, mock_controller):
        """Test creating profile when no existing profile exists"""
        controller, mock_db, mock_workflow = mock_controller
        
        # Mock no existing profile
        mock_db.get_profile_by_url.return_value = None
        
        # Mock workflow response
        mock_result = MagicMock()
        mock_result.profile = MagicMock()
        mock_workflow.process_profile.return_value = ("request-id", mock_result)
        
        # Mock database operations
        mock_db.store_profile.return_value = "new-profile-id"
        mock_db.get_profile_by_id.return_value = {
            "id": "new-profile-id",
            "name": "Test User",
            "url": "https://www.linkedin.com/in/test/",
            "created_at": "2025-07-27T10:00:00"
        }
        
        # Test request
        request = ProfileCreateRequest(
            linkedin_url="https://linkedin.com/in/test",
            include_companies=True
        )
        
        # Execute
        result = await controller.create_profile(request)
        
        # Verify workflow was called with correct parameters
        mock_workflow.process_profile.assert_called_once()
        call_args = mock_workflow.process_profile.call_args[0][0]
        assert isinstance(call_args, ProfileIngestionRequest)
        assert call_args.include_companies is True
        
        # Verify profile was stored
        mock_db.store_profile.assert_called_once()
        mock_db.get_profile_by_id.assert_called_once_with("new-profile-id")
        
        # Verify response
        assert result.id == "new-profile-id"
        assert result.name == "Test User"

    @pytest.mark.asyncio
    async def test_update_existing_profile_default_behavior(self, mock_controller):
        """Test updating existing profile (default behavior when duplicate found)"""
        controller, mock_db, mock_workflow = mock_controller
        
        # Mock existing profile
        existing_profile = {
            "id": "existing-id",
            "name": "Old Data",
            "url": "https://www.linkedin.com/in/test/",
            "created_at": "2025-07-26T10:00:00"
        }
        mock_db.get_profile_by_url.return_value = existing_profile
        
        # Mock successful deletion
        mock_db.delete_profile.return_value = True
        
        # Mock workflow response
        mock_result = MagicMock()
        mock_result.profile = MagicMock()
        mock_workflow.process_profile.return_value = ("request-id", mock_result)
        
        # Mock database operations
        mock_db.store_profile.return_value = "updated-profile-id"
        mock_db.get_profile_by_id.return_value = {
            "id": "updated-profile-id",
            "name": "Updated Data",
            "url": "https://www.linkedin.com/in/test/",
            "created_at": "2025-07-27T10:00:00"
        }
        
        # Test request
        request = ProfileCreateRequest(
            linkedin_url="https://linkedin.com/in/test",
            include_companies=False  # Test custom value
        )
        
        # Execute
        result = await controller.create_profile(request)
        
        # Verify existing profile was deleted
        mock_db.delete_profile.assert_called_once_with("existing-id")
        
        # Verify workflow was called with custom include_companies value
        mock_workflow.process_profile.assert_called_once()
        call_args = mock_workflow.process_profile.call_args[0][0]
        assert call_args.include_companies is False
        
        # Verify new profile was stored
        mock_db.store_profile.assert_called_once()
        
        # Verify response shows updated data
        assert result.id == "updated-profile-id"
        assert result.name == "Updated Data"


    @pytest.mark.asyncio
    async def test_include_companies_parameter_passed_correctly(self, mock_controller):
        """Test that include_companies parameter is passed correctly to workflow"""
        controller, mock_db, mock_workflow = mock_controller
        
        # Mock no existing profile
        mock_db.get_profile_by_url.return_value = None
        
        # Mock workflow response
        mock_result = MagicMock()
        mock_result.profile = MagicMock()
        mock_workflow.process_profile.return_value = ("request-id", mock_result)
        
        # Mock database operations
        mock_db.store_profile.return_value = "new-profile-id"
        mock_db.get_profile_by_id.return_value = {
            "id": "new-profile-id",
            "url": "https://www.linkedin.com/in/test/",
            "created_at": "2025-07-27T10:00:00"
        }
        
        # Test with include_companies=False
        request = ProfileCreateRequest(
            linkedin_url="https://linkedin.com/in/test",
            include_companies=False
        )
        
        # Execute
        await controller.create_profile(request)
        
        # Verify workflow was called with include_companies=False
        mock_workflow.process_profile.assert_called_once()
        call_args = mock_workflow.process_profile.call_args[0][0]
        assert isinstance(call_args, ProfileIngestionRequest)
        assert call_args.include_companies is False


class TestEndpointIntegration:
    """Test REST endpoint integration with smart profile management"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    def test_create_profile_request_with_new_fields(self, client, monkeypatch):
        """Test POST endpoint accepts new fields"""
        # Mock the controller method
        mock_response = {
            "id": "test-id",
            "name": "Test User",
            "url": "https://www.linkedin.com/in/test/",
            "created_at": "2025-07-27T10:00:00"
        }
        
        async def mock_create_profile(request):
            # Verify request has new fields
            assert hasattr(request, 'include_companies')
            assert request.include_companies is False
            
            # Return mock response
            from main import ProfileResponse
            return ProfileResponse(**mock_response)
        
        # Mock the controller
        def mock_get_controller():
            controller = MagicMock()
            controller.create_profile = mock_create_profile
            return controller
        
        monkeypatch.setattr("main.get_profile_controller", mock_get_controller)
        
        # Test request with new fields
        response = client.post(
            "/api/v1/profiles",
            json={
                "linkedin_url": "https://linkedin.com/in/test",
                "include_companies": False
            },
            headers={"x-api-key": settings.API_KEY}
        )
        
        # Verify response
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "test-id"
        assert data["name"] == "Test User"

    def test_create_profile_request_with_defaults(self, client, monkeypatch):
        """Test POST endpoint uses default values when fields not provided"""
        async def mock_create_profile(request):
            # Verify default values
            assert request.include_companies is True  # Default
            
            # Return mock response
            from main import ProfileResponse
            return ProfileResponse(
                id="test-id",
                url="https://www.linkedin.com/in/test/",
                created_at="2025-07-27T10:00:00"
            )
        
        # Mock the controller
        def mock_get_controller():
            controller = MagicMock()
            controller.create_profile = mock_create_profile
            return controller
        
        monkeypatch.setattr("main.get_profile_controller", mock_get_controller)
        
        # Test request with minimal fields (should use defaults)
        response = client.post(
            "/api/v1/profiles",
            json={"linkedin_url": "https://linkedin.com/in/test"},
            headers={"x-api-key": settings.API_KEY}
        )
        
        # Verify response
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "test-id"
