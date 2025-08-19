"""
Integration tests for the LinkedIn Ingestion Service
"""

import pytest
from app.testing.compatibility import TestClient
from unittest.mock import patch, MagicMock

from main import app


class TestIntegration:
    """Integration test suite for the full application stack"""
    
    def setup_method(self):
        """Set up test client and headers"""
        self.client = TestClient(app)
        self.headers = {"x-api-key": "li_HieZz-IjBp0uE7d-rZkRE0qyy12r5_ZJS_FR4jMvv0I"}
    
    @patch("main.get_db_client")
    def test_get_profile_not_found(self, mock_db):
        """Test that a 404 error is returned for a non-existent profile"""
        # Mock the database client to return None
        mock_instance = MagicMock()
        
        async def mock_get_profile_by_id(profile_id):
            return None
        
        mock_instance.get_profile_by_id = mock_get_profile_by_id
        mock_db.return_value = mock_instance
        
        response = self.client.get("/api/v1/profiles/non-existent-id", headers=self.headers)
        
        assert response.status_code == 404
        data = response.json()
        # HTTPException puts the ErrorResponse in the "detail" field
        assert "detail" in data
        detail = data["detail"]
        assert detail["error_code"] == "PROFILE_NOT_FOUND"
        assert "suggestions" not in detail["details"] # No suggestions for 404
