"""
Tests for profile REST API endpoints
"""

import pytest
from app.testing.compatibility import TestClient
from unittest.mock import patch, MagicMock, AsyncMock

from main import app
from app.exceptions import ProfileAlreadyExistsError


class TestProfileEndpoints:
    """Test suite for profile API endpoints"""
    
    def setup_method(self):
        """Set up test client and headers"""
        self.client = TestClient(app)
        self.headers = {"x-api-key": "li_HieZz-IjBp0uE7d-rZkRE0qyy12r5_ZJS_FR4jMvv0I"}
    
    @patch("main.get_linkedin_workflow")
    @patch("main.get_db_client")
    def test_create_profile_duplicate_url(self, mock_db, mock_workflow):
        """Test that creating a profile with a duplicate URL triggers smart update behavior"""
        # Mock database client with AsyncMock for async methods
        mock_db_instance = MagicMock()
        
        mock_db_instance.get_profile_by_url = AsyncMock(return_value={
            "id": "existing-profile-id", 
            "url": "https://www.linkedin.com/in/duplicate/", 
            "name": "test", 
            "created_at": "now"
        })
        mock_db_instance.delete_profile = AsyncMock(return_value=True)
        mock_db_instance.store_profile = AsyncMock(return_value="new-profile-id")
        mock_db_instance.get_profile_by_id = AsyncMock(return_value={
            "id": "new-profile-id",
            "url": "https://www.linkedin.com/in/duplicate/",
            "name": "Updated Profile",
            "created_at": "2024-01-01T00:00:00Z"
        })
        
        mock_db.return_value = mock_db_instance
        
        # Mock LinkedIn workflow
        mock_workflow_instance = MagicMock()
        
        async def mock_process_profile(request):
            from app.cassidy.workflows import EnrichedProfile
            from app.cassidy.models import LinkedInProfile
            
            # Create a mock LinkedIn profile (Cassidy format)
            mock_profile = LinkedInProfile(
                profile_id="test123",
                full_name="Updated Profile",
                linkedin_url="https://www.linkedin.com/in/duplicate/",
                headline="Software Engineer"
            )
            
            # Create an enriched profile wrapper
            enriched_profile = EnrichedProfile(mock_profile, [])
            
            return "request-id", enriched_profile
        
        mock_workflow_instance.process_profile = mock_process_profile
        mock_workflow.return_value = mock_workflow_instance
        
        # Make the request to create a duplicate profile
        response = self.client.post(
            "/api/v1/profiles",
            json={
                "linkedin_url": "https://www.linkedin.com/in/duplicate", 
                "suggested_role": "CTO"
            },
            headers=self.headers
        )
        
        # Assert that the smart update was successful (201 Created, not 409 Conflict)
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "new-profile-id"
        assert data["name"] == "Updated Profile"
        assert data["url"] == "https://www.linkedin.com/in/duplicate/"
        
        # Verify that delete_profile was called with the existing profile ID
        mock_db_instance.delete_profile.assert_called_once_with("existing-profile-id")
