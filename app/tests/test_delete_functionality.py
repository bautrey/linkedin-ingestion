"""
Unit tests for profile deletion functionality

Tests both SupabaseClient.delete_profile() and DELETE /api/v1/profiles/{id} endpoint
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from app.testing.compatibility import TestClient
from app.database.supabase_client import SupabaseClient
from main import app
from app.core.config import settings


class TestSupabaseClientDelete:
    """Test SupabaseClient delete functionality"""

    @pytest.fixture
    def mock_supabase_client(self):
        """Create a mocked SupabaseClient instance"""
        client = SupabaseClient()
        client.client = AsyncMock()
        client._client_initialized = True
        return client

    @pytest.mark.asyncio
    async def test_delete_profile_success(self, mock_supabase_client):
        """Test successful profile deletion"""
        # Arrange
        profile_id = "test-profile-id"
        mock_result = MagicMock()
        mock_result.data = [{"id": profile_id}]  # Indicates successful deletion
        
        # Set up nested mocks - only final execute should be async
        mock_table = MagicMock()
        mock_delete_query = MagicMock()
        mock_eq_query = MagicMock()
        mock_eq_query.execute = AsyncMock(return_value=mock_result)
        mock_delete_query.eq = MagicMock(return_value=mock_eq_query)
        mock_table.delete = MagicMock(return_value=mock_delete_query)
        mock_supabase_client.client.table = MagicMock(return_value=mock_table)

        # Act
        result = await mock_supabase_client.delete_profile(profile_id)

        # Assert
        assert result is True
        mock_supabase_client.client.table.assert_called_once_with("linkedin_profiles")
        mock_table.delete.assert_called_once()
        mock_delete_query.eq.assert_called_once_with("id", profile_id)

    @pytest.mark.asyncio
    async def test_delete_profile_not_found(self, mock_supabase_client):
        """Test deletion when profile doesn't exist"""
        # Arrange
        profile_id = "nonexistent-profile-id"
        mock_result = MagicMock()
        mock_result.data = []  # Indicates no rows deleted
        
        # Set up nested mocks - only final execute should be async
        mock_table = MagicMock()
        mock_delete_query = MagicMock()
        mock_eq_query = MagicMock()
        mock_eq_query.execute = AsyncMock(return_value=mock_result)
        mock_delete_query.eq = MagicMock(return_value=mock_eq_query)
        mock_table.delete = MagicMock(return_value=mock_delete_query)
        mock_supabase_client.client.table = MagicMock(return_value=mock_table)

        # Act
        result = await mock_supabase_client.delete_profile(profile_id)

        # Assert
        assert result is False
        mock_supabase_client.client.table.assert_called_once_with("linkedin_profiles")

    @pytest.mark.asyncio
    async def test_delete_profile_database_error(self, mock_supabase_client):
        """Test deletion when database error occurs"""
        # Arrange
        profile_id = "test-profile-id"
        
        # Set up nested mocks with error - only final execute should be async
        mock_table = MagicMock()
        mock_delete_query = MagicMock()
        mock_eq_query = MagicMock()
        mock_eq_query.execute = AsyncMock(side_effect=Exception("Database error"))
        mock_delete_query.eq = MagicMock(return_value=mock_eq_query)
        mock_table.delete = MagicMock(return_value=mock_delete_query)
        mock_supabase_client.client.table = MagicMock(return_value=mock_table)

        # Act & Assert
        with pytest.raises(Exception, match="Database error"):
            await mock_supabase_client.delete_profile(profile_id)


class TestDeleteEndpoint:
    """Test DELETE /api/v1/profiles/{id} endpoint"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    def test_delete_profile_success(self, client, monkeypatch):
        """Test DELETE endpoint with successful deletion"""
        # Mock the database client
        mock_db_client = AsyncMock()
        mock_db_client.delete_profile = AsyncMock(return_value=True)
        
        def mock_get_db_client():
            return mock_db_client
        
        monkeypatch.setattr("main.get_db_client", mock_get_db_client)

        # Act
        response = client.delete(
            "/api/v1/profiles/test-profile-id",
            headers={"x-api-key": settings.API_KEY}
        )

        # Assert
        assert response.status_code == 204
        assert response.text == ""  # 204 responses should have empty body

    def test_delete_profile_not_found(self, client, monkeypatch):
        """Test DELETE endpoint when profile doesn't exist"""
        # Mock the database client
        mock_db_client = AsyncMock()
        mock_db_client.delete_profile = AsyncMock(return_value=False)
        
        def mock_get_db_client():
            return mock_db_client
        
        monkeypatch.setattr("main.get_db_client", mock_get_db_client)

        # Act
        response = client.delete(
            "/api/v1/profiles/nonexistent-id",
            headers={"x-api-key": settings.API_KEY}
        )

        # Assert
        assert response.status_code == 404
        response_data = response.json()
        assert response_data["detail"]["error_code"] == "PROFILE_NOT_FOUND"
        assert "nonexistent-id" in response_data["detail"]["message"]

    def test_delete_profile_unauthorized(self, client):
        """Test DELETE endpoint without API key"""
        # Act
        response = client.delete("/api/v1/profiles/test-profile-id")

        # Assert
        assert response.status_code == 403
        response_data = response.json()
        assert response_data["detail"]["error_code"] == "UNAUTHORIZED"

    def test_delete_profile_invalid_api_key(self, client):
        """Test DELETE endpoint with invalid API key"""
        # Act
        response = client.delete(
            "/api/v1/profiles/test-profile-id",
            headers={"x-api-key": "invalid-key"}
        )

        # Assert
        assert response.status_code == 403
        response_data = response.json()
        assert response_data["detail"]["error_code"] == "UNAUTHORIZED"

    def test_delete_profile_database_error(self, client, monkeypatch):
        """Test DELETE endpoint when database error occurs"""
        # Mock the database client to raise an exception
        mock_db_client = AsyncMock()
        mock_db_client.delete_profile = AsyncMock(side_effect=Exception("Database connection failed"))
        
        def mock_get_db_client():
            return mock_db_client
        
        monkeypatch.setattr("main.get_db_client", mock_get_db_client)

        # Act
        response = client.delete(
            "/api/v1/profiles/test-profile-id",
            headers={"x-api-key": settings.API_KEY}
        )

        # Assert
        assert response.status_code == 500
