"""
Tests for profile REST API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from main import app
from app.exceptions import ProfileAlreadyExistsError


class TestProfileEndpoints:
    """Test suite for profile API endpoints"""
    
    def setup_method(self):
        """Set up test client and headers"""
        self.client = TestClient(app)
        self.headers = {"x-api-key": "li_HieZz-IjBp0uE7d-rZkRE0qyy12r5_ZJS_FR4jMvv0I"}
    
    @patch("main.get_db_client")
    def test_create_profile_duplicate_url(self, mock_db):
        """Test that creating a profile with a duplicate URL raises ProfileAlreadyExistsError"""
        # Mock database client to return an existing profile
        mock_instance = MagicMock()
        
        async def mock_get_profile_by_url(url):
            return {"id": "existing-profile-id", "url": url, "name": "test", "created_at": "now"}
        
        mock_instance.get_profile_by_url = mock_get_profile_by_url
        mock_db.return_value = mock_instance
        
        # Make the request to create a duplicate profile
        response = self.client.post(
            "/api/v1/profiles",
            json={"linkedin_url": "https://www.linkedin.com/in/duplicate"},
            headers=self.headers
        )
        
        # Assert that the response is a 409 Conflict with the correct error code
        assert response.status_code == 409
        data = response.json()
        assert data["error_code"] == "PROFILE_ALREADY_EXISTS"
        assert "suggestions" in data["details"]
