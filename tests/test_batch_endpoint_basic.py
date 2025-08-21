"""Basic test to verify the batch enhanced profile ingestion endpoint exists."""

import pytest
from app.testing.compatibility import TestClient
from unittest.mock import patch
from app.core.config import settings

# Use actual API key from settings
VALID_API_KEY = settings.API_KEY

@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    from main import app
    return TestClient(app)

def test_batch_endpoint_exists(client):
    """Test that the batch enhanced endpoint exists and accepts requests"""
    # Valid request with one profile
    request_data = {
        "profiles": [
            {
                "linkedin_url": "https://www.linkedin.com/in/testuser/",
                "suggested_role": "CTO"
            }
        ],
        "max_concurrent": 1
    }
    
    # Make request - we expect it to fail but at least the endpoint should exist
    response = client.post(
        "/api/v1/profiles/batch-enhanced",
        json=request_data,
        headers={"X-API-Key": VALID_API_KEY}
    )
    
    # Should not be a 404 (endpoint exists)
    assert response.status_code != 404
    # Might be 500 due to missing dependencies, but that's fine for this basic test

def test_batch_endpoint_validation_errors(client):
    """Test that the batch endpoint properly validates requests"""
    # Empty profiles list should fail validation
    response = client.post(
        "/api/v1/profiles/batch-enhanced",
        json={"profiles": [], "max_concurrent": 1},
        headers={"X-API-Key": VALID_API_KEY}
    )
    
    assert response.status_code == 422  # Validation error
    
    # Too many profiles should fail validation  
    too_many_profiles = {
        "profiles": [
            {"linkedin_url": f"https://www.linkedin.com/in/user{i}/", "suggested_role": "CTO"} 
            for i in range(11)  # Over the limit of 10
        ],
        "max_concurrent": 1
    }
    
    response = client.post(
        "/api/v1/profiles/batch-enhanced",
        json=too_many_profiles,
        headers={"X-API-Key": VALID_API_KEY}
    )
    
    assert response.status_code == 422  # Validation error
    
    # Invalid max_concurrent should fail validation
    response = client.post(
        "/api/v1/profiles/batch-enhanced",
        json={
            "profiles": [{"linkedin_url": "https://www.linkedin.com/in/test/", "suggested_role": "CTO"}],
            "max_concurrent": 10  # Over the limit of 5
        },
        headers={"X-API-Key": VALID_API_KEY}
    )
    
    assert response.status_code == 422  # Validation error

def test_batch_endpoint_unauthorized(client):
    """Test that the endpoint requires authentication"""
    request_data = {
        "profiles": [
            {
                "linkedin_url": "https://www.linkedin.com/in/testuser/",
                "suggested_role": "CTO"
            }
        ]
    }
    
    # Request without API key
    response = client.post(
        "/api/v1/profiles/batch-enhanced",
        json=request_data
    )
    
    assert response.status_code == 403  # Unauthorized
