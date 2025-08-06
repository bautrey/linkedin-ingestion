"""
Tests for V1.8 Scoring API Endpoint

Test-driven development approach: Tests written before implementation
Endpoint: GET /api/v1/profiles/{profile_id}/score?role={role}
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
import json

from main import app
from app.models.canonical import CanonicalProfile, CanonicalExperienceEntry
from app.scoring.models import ScoringRequest, ScoringResponse, CategoryScore

client = TestClient(app)

# Valid test API key
TEST_API_KEY = "li_HieZz-IjBp0uE7d-rZkRE0qyy12r5_ZJS_FR4jMvv0I"

# Test profile data
TEST_PROFILE_ID = "test-profile-123"
TEST_INVALID_PROFILE_ID = "nonexistent-profile"

@pytest.fixture
def mock_canonical_profile():
    """Mock canonical profile for testing"""
    return CanonicalProfile(
        profile_id=TEST_PROFILE_ID,
        public_id="johndoe",
        full_name="John Doe",
        linkedin_url="https://www.linkedin.com/in/johndoe/",
        headline="Senior Software Engineer",
        about="Experienced software engineer with expertise in Python and cloud technologies.",
        city="San Francisco",
        country="US",
        follower_count=1500,
        connection_count=500,
        experiences=[
            CanonicalExperienceEntry(
                title="Senior Software Engineer",
                company="Tech Corp",
                duration="2 years",
                location="San Francisco, CA",
                description="Led backend development using Python and AWS"
            ),
            CanonicalExperienceEntry(
                title="Software Engineer",
                company="Startup Inc",
                duration="3 years",  
                location="San Francisco, CA",
                description="Full-stack development with React and Node.js"
            )
        ],
        educations=[]
    )

@pytest.fixture
def mock_scoring_response():
    """Mock scoring response for testing"""
    return ScoringResponse(
        profile_id=TEST_PROFILE_ID,
        role="CTO",
        overall_score=0.75,
        category_scores=[
            CategoryScore(category="Technical Leadership", score=0.8, weight=0.3),
            CategoryScore(category="Strategic Vision", score=0.7, weight=0.25),
            CategoryScore(category="Team Management", score=0.75, weight=0.25),
            CategoryScore(category="Industry Experience", score=0.8, weight=0.2)
        ],
        summary="Strong technical leader with solid management experience and strategic thinking capabilities.",
        recommendations=[
            "Consider for senior technical leadership roles",
            "Strong fit for CTO positions in mid-size technology companies"
        ],
        alternative_roles=["VP Engineering", "Technical Director"],
        timestamp=datetime.now(timezone.utc).isoformat()
    )


class TestScoringEndpointAuthentication:
    """Test API key authentication for scoring endpoint"""
    
    def test_scoring_endpoint_requires_api_key(self):
        """Test that scoring endpoint requires API key"""
        response = client.get(f"/api/v1/profiles/{TEST_PROFILE_ID}/score?role=CTO")
        
        assert response.status_code == 403
        error_data = response.json()
        assert error_data["detail"]["error_code"] == "UNAUTHORIZED"
        assert "Invalid or missing API key" in error_data["detail"]["message"]
    
    def test_scoring_endpoint_rejects_invalid_api_key(self):
        """Test that scoring endpoint rejects invalid API key"""
        response = client.get(
            f"/api/v1/profiles/{TEST_PROFILE_ID}/score?role=CTO",
            headers={"x-api-key": "invalid-key"}
        )
        
        assert response.status_code == 403
        error_data = response.json()
        assert error_data["detail"]["error_code"] == "UNAUTHORIZED"


class TestScoringEndpointValidation:
    """Test request validation for scoring endpoint"""
    
    def test_scoring_endpoint_requires_role_parameter(self):
        """Test that role query parameter is required"""
        response = client.get(
            f"/api/v1/profiles/{TEST_PROFILE_ID}/score",
            headers={"x-api-key": TEST_API_KEY}
        )
        
        assert response.status_code == 422
        error_data = response.json()
        assert error_data["error_code"] == "VALIDATION_ERROR"
        
        # Check validation error details
        validation_errors = error_data.get("validation_errors", [])
        role_error = next((e for e in validation_errors if "role" in e.get("field", "")), None)
        assert role_error is not None
    
    def test_scoring_endpoint_validates_role_values(self):
        """Test that only valid role values are accepted"""
        invalid_role = "INVALID_ROLE"
        response = client.get(
            f"/api/v1/profiles/{TEST_PROFILE_ID}/score?role={invalid_role}",
            headers={"x-api-key": TEST_API_KEY}
        )
        
        assert response.status_code == 422
        error_data = response.json()
        assert error_data["error_code"] == "VALIDATION_ERROR"
    
    @pytest.mark.parametrize("valid_role", ["CTO", "CIO", "CISO"])
    def test_scoring_endpoint_accepts_valid_roles(self, valid_role, mock_canonical_profile, mock_scoring_response):
        """Test that valid role values are accepted"""
        with patch('main.get_profile_controller') as mock_controller:
            # Mock the controller and its methods
            controller_instance = AsyncMock()
            controller_instance.db_client.get_profile_by_id = AsyncMock(return_value=mock_canonical_profile.model_dump())
            controller_instance.score_profile = AsyncMock(return_value=mock_scoring_response)
            mock_controller.return_value = controller_instance
            
            response = client.get(
                f"/api/v1/profiles/{TEST_PROFILE_ID}/score?role={valid_role}",
                headers={"x-api-key": TEST_API_KEY}
            )
            
            # Should not return validation error for valid roles
            assert response.status_code != 422


class TestScoringEndpointProfileValidation:
    """Test profile existence validation"""
    
    def test_scoring_endpoint_handles_nonexistent_profile(self):
        """Test proper error handling for nonexistent profile"""
        with patch('main.get_profile_controller') as mock_controller:
            # Mock the controller to return None for nonexistent profile
            controller_instance = AsyncMock()
            controller_instance.db_client.get_profile_by_id = AsyncMock(return_value=None)
            mock_controller.return_value = controller_instance
            
            response = client.get(
                f"/api/v1/profiles/{TEST_INVALID_PROFILE_ID}/score?role=CTO",
                headers={"x-api-key": TEST_API_KEY}
            )
            
            assert response.status_code == 404
            error_data = response.json()
            assert error_data["error_code"] == "PROFILE_NOT_FOUND"
            assert TEST_INVALID_PROFILE_ID in error_data["message"]


class TestScoringEndpointSuccessResponse:
    """Test successful scoring response format"""
    
    def test_scoring_endpoint_returns_complete_scoring_response(self, mock_canonical_profile, mock_scoring_response):
        """Test that scoring endpoint returns complete scoring data"""
        with patch('main.get_profile_controller') as mock_controller:
            # Mock the controller and its methods
            controller_instance = AsyncMock()
            controller_instance.db_client.get_profile_by_id = AsyncMock(
                return_value=mock_canonical_profile.model_dump()
            )
            controller_instance.score_profile = AsyncMock(return_value=mock_scoring_response)
            mock_controller.return_value = controller_instance
            
            response = client.get(
                f"/api/v1/profiles/{TEST_PROFILE_ID}/score?role=CTO",
                headers={"x-api-key": TEST_API_KEY}
            )
            
            assert response.status_code == 200
            
            # Parse response data
            data = response.json()
            
            # Verify response structure matches ScoringResponse model
            assert "profile_id" in data
            assert "role" in data
            assert "overall_score" in data
            assert "category_scores" in data
            assert "summary" in data
            assert "recommendations" in data
            assert "alternative_roles" in data
            assert "timestamp" in data
            
            # Verify data types and values
            assert data["profile_id"] == TEST_PROFILE_ID
            assert data["role"] == "CTO"
            assert isinstance(data["overall_score"], float)
            assert 0.0 <= data["overall_score"] <= 1.0
            assert isinstance(data["category_scores"], list)
            assert len(data["category_scores"]) > 0
            assert isinstance(data["summary"], str)
            assert isinstance(data["recommendations"], list)
            assert isinstance(data["alternative_roles"], list)
    
    def test_scoring_endpoint_category_scores_format(self, mock_canonical_profile, mock_scoring_response):
        """Test that category scores are properly formatted"""
        with patch('main.get_profile_controller') as mock_controller:
            # Mock the controller and its methods
            controller_instance = AsyncMock()
            controller_instance.db_client.get_profile_by_id = AsyncMock(
                return_value=mock_canonical_profile.model_dump()
            )
            controller_instance.score_profile = AsyncMock(return_value=mock_scoring_response)
            mock_controller.return_value = controller_instance
            
            response = client.get(
                f"/api/v1/profiles/{TEST_PROFILE_ID}/score?role=CTO",
                headers={"x-api-key": TEST_API_KEY}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify category score structure
            category_scores = data["category_scores"]
            for category in category_scores:
                assert "category" in category
                assert "score" in category
                assert "weight" in category
                assert isinstance(category["score"], float)
                assert isinstance(category["weight"], float)
                assert 0.0 <= category["score"] <= 1.0
                assert 0.0 <= category["weight"] <= 1.0


class TestScoringEndpointPerformance:
    """Test performance requirements for scoring endpoint"""
    
    def test_scoring_endpoint_response_time(self, mock_canonical_profile, mock_scoring_response):
        """Test that scoring endpoint meets response time requirements (<500ms)"""
        import time
        
        with patch('main.get_profile_controller') as mock_controller:
            # Mock the controller and its methods
            controller_instance = AsyncMock()
            controller_instance.db_client.get_profile_by_id = AsyncMock(
                return_value=mock_canonical_profile.model_dump()
            )
            controller_instance.score_profile = AsyncMock(return_value=mock_scoring_response)
            mock_controller.return_value = controller_instance
            
            start_time = time.time()
            response = client.get(
                f"/api/v1/profiles/{TEST_PROFILE_ID}/score?role=CTO",
                headers={"x-api-key": TEST_API_KEY}
            )
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000  # Convert to milliseconds
            
            assert response.status_code == 200
            # Allow generous buffer for test environment, but still validate reasonable performance
            assert response_time < 2000, f"Response time {response_time}ms exceeds 2000ms test threshold"


class TestScoringEndpointErrorHandling:
    """Test error handling scenarios"""
    
    def test_scoring_endpoint_handles_scoring_engine_errors(self, mock_canonical_profile):
        """Test proper error handling when scoring engine fails"""
        with patch('main.get_profile_controller') as mock_controller:
            # Mock the controller to simulate scoring engine error
            controller_instance = AsyncMock()
            controller_instance.db_client.get_profile_by_id = AsyncMock(
                return_value=mock_canonical_profile.model_dump()
            )
            controller_instance.score_profile = AsyncMock(
                side_effect=Exception("Scoring engine error")
            )
            mock_controller.return_value = controller_instance
            
            response = client.get(
                f"/api/v1/profiles/{TEST_PROFILE_ID}/score?role=CTO",
                headers={"x-api-key": TEST_API_KEY}
            )
            
            assert response.status_code == 500
            error_data = response.json()
            assert error_data["error_code"] == "INTERNAL_SERVER_ERROR"
    
    def test_scoring_endpoint_handles_database_connection_errors(self):
        """Test proper error handling when database connection fails"""
        with patch('main.get_profile_controller') as mock_controller:
            # Mock the controller to simulate database connection error
            controller_instance = AsyncMock()
            controller_instance.db_client.get_profile_by_id = AsyncMock(
                side_effect=Exception("Database connection failed")
            )
            mock_controller.return_value = controller_instance
            
            response = client.get(
                f"/api/v1/profiles/{TEST_PROFILE_ID}/score?role=CTO",
                headers={"x-api-key": TEST_API_KEY}
            )
            
            assert response.status_code == 500
            error_data = response.json()
            assert error_data["error_code"] == "INTERNAL_SERVER_ERROR"


class TestScoringEndpointDocumentation:
    """Test that scoring endpoint properly integrates with OpenAPI documentation"""
    
    def test_scoring_endpoint_appears_in_openapi_schema(self):
        """Test that scoring endpoint is documented in OpenAPI schema"""
        response = client.get("/openapi.json")
        
        if response.status_code == 200:  # Only test if docs are enabled
            openapi_data = response.json()
            paths = openapi_data.get("paths", {})
            
            # Check if our scoring endpoint path exists
            scoring_path = "/api/v1/profiles/{profile_id}/score"
            assert scoring_path in paths or any(scoring_path.replace("{profile_id}", "{id}") in path for path in paths)
