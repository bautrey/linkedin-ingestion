import pytest
from app.testing.compatibility import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
import uuid
from datetime import datetime, timezone
from app.core.config import settings

# Use actual API key from settings
VALID_API_KEY = settings.API_KEY

# Mock data for testing
MOCK_LINKEDIN_URL1 = "https://www.linkedin.com/in/johndoe/"
MOCK_LINKEDIN_URL2 = "https://www.linkedin.com/in/janedoe/"
MOCK_PROFILE_ID1 = str(uuid.uuid4())
MOCK_PROFILE_ID2 = str(uuid.uuid4())

# Mock request payload for batch endpoint
MOCK_BATCH_REQUEST = {
    "profiles": [
        {
            "linkedin_url": MOCK_LINKEDIN_URL1,
            "suggested_role": "CTO"
        },
        {
            "linkedin_url": MOCK_LINKEDIN_URL2,
            "suggested_role": "CIO"
        }
    ],
    "max_concurrent": 2
}

# Mock successful profile result
def create_mock_profile(profile_id, url, name="Test User"):
    return {
        "id": profile_id,
        "name": name,
        "url": url,
        "position": "CTO",
        "about": "Test profile",
        "experience": [],
        "education": [],
        "certifications": [],
        "created_at": datetime.now(timezone.utc).isoformat()
    }

# Mock successful pipeline result
def create_mock_pipeline_result(profile_id, status="completed"):
    if status == "completed":
        return {
            "status": "completed",
            "pipeline_id": str(uuid.uuid4()),
            "storage_ids": {
                "profile": profile_id
            },
            "companies": [
                {"id": str(uuid.uuid4()), "company_name": "Test Company"}
            ],
            "embeddings": {
                "profile": True
            },
            "started_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": datetime.now(timezone.utc).isoformat()
        }
    else:
        return {
            "status": "failed",
            "pipeline_id": str(uuid.uuid4()),
            "errors": [
                {"error": "Failed to process profile", "details": "Test error"}
            ],
            "started_at": datetime.now(timezone.utc).isoformat()
        }

@pytest.fixture
def mock_batch_pipeline():
    """Fixture for mocking the batch profile pipeline"""
    with patch("app.services.linkedin_pipeline.LinkedInDataPipeline") as mock_pipeline_class:
        mock_pipeline = mock_pipeline_class.return_value
        mock_batch_method = AsyncMock()
        mock_pipeline.batch_ingest_profiles_with_companies = mock_batch_method
        
        # Configure mock to return successful results for first profile and failed for second
        mock_batch_method.return_value = [
            create_mock_pipeline_result(MOCK_PROFILE_ID1, "completed"),
            create_mock_pipeline_result(MOCK_PROFILE_ID2, "failed")
        ]
        
        yield mock_pipeline

@pytest.fixture
def mock_db_client():
    """Fixture for mocking the database client"""
    with patch("app.database.supabase_client.SupabaseClient") as mock_db_class:
        mock_db = mock_db_class.return_value
        mock_db.get_profile_by_id = AsyncMock()
        
        # Configure mock to return profile data
        mock_db.get_profile_by_id.return_value = create_mock_profile(MOCK_PROFILE_ID1, MOCK_LINKEDIN_URL1)
        
        yield mock_db

@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    from main import app
    return TestClient(app)

def test_batch_create_profiles_success(client, mock_batch_pipeline):
    """Test successful batch profile creation with company processing"""
    # Mock the get_profile_controller function to return a controller with mocked db_client
    with patch("main.get_profile_controller") as mock_get_controller:
        # Create a mock controller
        mock_controller = MagicMock()
        mock_controller.batch_create_profiles = AsyncMock()
        
        # Mock successful batch response
        mock_batch_response = {
            "batch_id": str(uuid.uuid4()),
            "total_requested": 2,
            "successful": 1,
            "failed": 1,
            "results": [
                {
                    "id": MOCK_PROFILE_ID1,
                    "name": "John Doe",
                    "url": MOCK_LINKEDIN_URL1,
                    "position": "CTO",
                    "about": "Test profile",
                    "experience": [],
                    "education": [],
                    "certifications": [],
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "companies_processed": [{"id": str(uuid.uuid4()), "company_name": "Test Company"}],
                    "pipeline_metadata": {"pipeline_id": str(uuid.uuid4())}
                },
                {
                    "id": "",
                    "name": f"Failed: {MOCK_LINKEDIN_URL2}",
                    "url": MOCK_LINKEDIN_URL2,
                    "position": "Processing Failed",
                    "about": "Failed to process profile",
                    "experience": [],
                    "education": [],
                    "certifications": [],
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "pipeline_metadata": {"status": "failed"}
                }
            ],
            "started_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "processing_time_seconds": 1.5
        }
        
        # Configure the mock controller to return the batch response
        mock_controller.batch_create_profiles.return_value = mock_batch_response
        mock_get_controller.return_value = mock_controller
        
        # Make request to the batch endpoint
        response = client.post(
            "/api/v1/profiles/batch",
            json=MOCK_BATCH_REQUEST,
            headers={"X-API-Key": VALID_API_KEY}
        )
    
    # Verify response
    assert response.status_code == 201
    data = response.json()
    
    # Validate response structure
    assert "batch_id" in data
    assert data["total_requested"] == 2
    assert data["successful"] == 1
    assert data["failed"] == 1
    assert len(data["results"]) == 2
    
    # Verify successful profile
    assert data["results"][0]["id"] == MOCK_PROFILE_ID1
    assert data["results"][0]["name"] == "John Doe"
    assert data["results"][0]["url"] == MOCK_LINKEDIN_URL1
    assert "companies_processed" in data["results"][0]
    assert "pipeline_metadata" in data["results"][0]
    
    # Verify failed profile
    assert data["results"][1]["id"] == ""  # Empty ID for failed profile
    assert "Failed:" in data["results"][1]["name"]
    assert data["results"][1]["url"] == MOCK_LINKEDIN_URL2
    assert "Failed to process profile" in data["results"][1]["about"]
    
    # Verify metrics in response
    assert "processing_time_seconds" in data
    assert "started_at" in data
    assert "completed_at" in data

def test_batch_create_profiles_empty_batch(client):
    """Test batch creation with empty profiles list"""
    # Make request with empty profiles list
    response = client.post(
        "/api/v1/profiles/batch",
        json={"profiles": [], "max_concurrent": 2},
        headers={"X-API-Key": VALID_API_KEY}
    )
    
    # Should return validation error
    assert response.status_code == 422
    data = response.json()
    # Custom error format with error_code
    assert "error_code" in data
    assert data["error_code"] == "VALIDATION_ERROR"

def test_batch_create_profiles_too_many(client):
    """Test batch creation with too many profiles"""
    # Create a request with 11 profiles (over the limit of 10)
    too_many_profiles = {
        "profiles": [{"linkedin_url": f"https://www.linkedin.com/in/user{i}/", "suggested_role": "CTO"} for i in range(11)],
        "max_concurrent": 3
    }
    
    # Make request with too many profiles
    response = client.post(
        "/api/v1/profiles/batch",
        json=too_many_profiles,
        headers={"X-API-Key": VALID_API_KEY}
    )
    
    # Should return validation error
    assert response.status_code == 422
    data = response.json()
    # Custom error format with error_code
    assert "error_code" in data
    assert data["error_code"] == "VALIDATION_ERROR"

def test_batch_create_profiles_invalid_concurrent(client):
    """Test batch creation with invalid max_concurrent value"""
    # Create request with invalid max_concurrent (out of range 1-5)
    invalid_request = {
        "profiles": [
            {"linkedin_url": MOCK_LINKEDIN_URL1, "suggested_role": "CTO"}
        ],
        "max_concurrent": 10  # Too high
    }
    
    # Make request with invalid max_concurrent
    response = client.post(
        "/api/v1/profiles/batch",
        json=invalid_request,
        headers={"X-API-Key": VALID_API_KEY}
    )
    
    # Should return validation error
    assert response.status_code == 422
    data = response.json()
    # Custom error format with error_code
    assert "error_code" in data
    assert data["error_code"] == "VALIDATION_ERROR"

def test_batch_create_profiles_unauthorized(client):
    """Test batch creation with invalid API key"""
    # Make request with invalid API key
    response = client.post(
        "/api/v1/profiles/batch",
        json=MOCK_BATCH_REQUEST,
        headers={"X-API-Key": "invalid-key"}
    )
    
    # Should return unauthorized
    assert response.status_code == 403
