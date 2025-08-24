"""
Tests for the Quick Validation Service

This test suite verifies the CassidyQuickValidationService works correctly
for Stage 2 of the quality gates pipeline.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime

from app.services.quick_validation_service import (
    CassidyQuickValidationService,
    QuickValidationResult,
    QuickProfileSummary
)
from app.cassidy.models import LinkedInProfile
from app.cassidy.exceptions import CassidyWorkflowError, CassidyException


class TestCassidyQuickValidationService:
    
    @pytest.fixture
    def validation_service(self):
        return CassidyQuickValidationService()
    
    @pytest.fixture
    def mock_profile(self):
        """Mock LinkedIn profile with complete data"""
        profile = Mock()
        profile.full_name = "John Smith"
        profile.headline = "Software Engineer at Google"
        profile.company = "Google"
        profile.location = "San Francisco, CA"
        profile.linkedin_url = "https://www.linkedin.com/in/johnsmith/"
        profile.experience = [
            {"company": "Google", "title": "Software Engineer"},
            {"company": "Meta", "title": "Junior Developer"}
        ]
        profile.profile_id = "john-smith-123"
        return profile
    
    @pytest.fixture
    def minimal_profile(self):
        """Mock LinkedIn profile with minimal data"""
        profile = Mock()
        profile.full_name = "Jane Doe"
        profile.headline = None
        profile.company = None
        profile.location = None
        profile.linkedin_url = "https://www.linkedin.com/in/janedoe/"
        profile.experience = []
        profile.profile_id = "jane-doe-456"
        return profile
    
    @pytest.fixture
    def invalid_profile(self):
        """Mock LinkedIn profile with missing required data"""
        profile = Mock()
        profile.full_name = None
        profile.headline = None
        profile.company = None
        profile.location = None
        profile.linkedin_url = None
        profile.experience = []
        profile.profile_id = None
        return profile

    @pytest.mark.asyncio
    async def test_successful_validation_complete_profile(self, validation_service, mock_profile):
        """Test successful validation with complete profile data"""
        
        with patch.object(validation_service.cassidy_client, 'fetch_profile', return_value=mock_profile):
            result = await validation_service.quick_validate_profile(
                "https://www.linkedin.com/in/johnsmith/"
            )
        
        assert result.is_valid is True
        assert result.profile_accessible is True
        assert result.basic_data_valid is True
        assert len(result.validation_errors) == 0
        assert result.cassidy_error is None
        assert result.processing_time_ms is not None
        
        # Check profile summary
        assert result.profile_summary is not None
        summary = result.profile_summary
        assert summary["full_name"] == "John Smith"
        assert summary["headline"] == "Software Engineer at Google"
        assert summary["company"] == "Google"
        assert summary["experience_count"] == 2
        assert summary["has_basic_info"] is True

    @pytest.mark.asyncio
    async def test_successful_validation_minimal_profile(self, validation_service, minimal_profile):
        """Test validation with minimal profile data (should still pass)"""
        
        with patch.object(validation_service.cassidy_client, 'fetch_profile', return_value=minimal_profile):
            result = await validation_service.quick_validate_profile(
                "https://www.linkedin.com/in/janedoe/"
            )
        
        assert result.is_valid is True
        assert result.profile_accessible is True
        assert result.basic_data_valid is True
        assert len(result.validation_errors) == 0
        assert len(result.warnings) > 0  # Should have warnings about missing data
        
        # Should warn about missing data but not fail
        warning_messages = result.warnings
        assert any("headline" in warning.lower() for warning in warning_messages)
        assert any("experience" in warning.lower() for warning in warning_messages)

    @pytest.mark.asyncio
    async def test_validation_failure_invalid_profile(self, validation_service, invalid_profile):
        """Test validation failure with invalid/incomplete profile"""
        
        with patch.object(validation_service.cassidy_client, 'fetch_profile', return_value=invalid_profile):
            result = await validation_service.quick_validate_profile(
                "https://www.linkedin.com/in/invalid/"
            )
        
        assert result.is_valid is False
        assert result.profile_accessible is True  # Profile was fetched
        assert result.basic_data_valid is False  # But data is invalid
        assert len(result.validation_errors) == 0  # No fetch errors
        assert len(result.warnings) > 0  # Should have data warnings
        
        # Should have warnings about missing required data
        warning_messages = result.warnings
        assert any("name" in warning.lower() for warning in warning_messages)

    @pytest.mark.asyncio
    async def test_validation_failure_cassidy_workflow_error(self, validation_service):
        """Test validation failure when Cassidy can't fetch profile"""
        
        with patch.object(
            validation_service.cassidy_client, 
            'fetch_profile', 
            side_effect=CassidyWorkflowError("not a valid LinkedIn profile URL")
        ):
            result = await validation_service.quick_validate_profile(
                "https://www.linkedin.com/in/nonexistent/"
            )
        
        assert result.is_valid is False
        assert result.profile_accessible is False
        assert result.basic_data_valid is False
        assert len(result.validation_errors) == 1
        assert "not accessible" in result.validation_errors[0].lower()
        assert result.cassidy_error is not None
        assert result.processing_time_ms is not None

    @pytest.mark.asyncio
    async def test_validation_failure_cassidy_api_error(self, validation_service):
        """Test validation failure when Cassidy API has issues"""
        
        with patch.object(
            validation_service.cassidy_client, 
            'fetch_profile', 
            side_effect=CassidyException("API rate limit exceeded")
        ):
            result = await validation_service.quick_validate_profile(
                "https://www.linkedin.com/in/johnsmith/"
            )
        
        assert result.is_valid is False
        assert result.profile_accessible is False
        assert result.basic_data_valid is False
        assert len(result.validation_errors) == 1
        assert "cassidy api error" in result.validation_errors[0].lower()
        assert result.cassidy_error is not None

    @pytest.mark.asyncio
    async def test_validation_unexpected_error(self, validation_service):
        """Test validation handling of unexpected errors"""
        
        with patch.object(
            validation_service.cassidy_client, 
            'fetch_profile', 
            side_effect=Exception("Unexpected network error")
        ):
            result = await validation_service.quick_validate_profile(
                "https://www.linkedin.com/in/johnsmith/"
            )
        
        assert result.is_valid is False
        assert result.profile_accessible is False
        assert result.basic_data_valid is False
        assert len(result.validation_errors) == 1
        assert "unexpected validation error" in result.validation_errors[0].lower()

    @pytest.mark.asyncio
    async def test_health_check_healthy(self, validation_service):
        """Test health check when service is healthy"""
        
        mock_cassidy_health = {"status": "healthy", "version": "1.0.0"}
        with patch.object(
            validation_service.cassidy_client, 
            'health_check', 
            return_value=mock_cassidy_health
        ):
            health = await validation_service.health_check()
        
        assert health["service"] == "quick_validation"
        assert health["status"] == "healthy"
        assert health["cassidy_api"] == mock_cassidy_health
        assert "timestamp" in health

    @pytest.mark.asyncio
    async def test_health_check_degraded(self, validation_service):
        """Test health check when Cassidy service is degraded"""
        
        mock_cassidy_health = {"status": "degraded", "error": "High latency"}
        with patch.object(
            validation_service.cassidy_client, 
            'health_check', 
            return_value=mock_cassidy_health
        ):
            health = await validation_service.health_check()
        
        assert health["service"] == "quick_validation"
        assert health["status"] == "degraded"
        assert health["cassidy_api"] == mock_cassidy_health

    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self, validation_service):
        """Test health check when Cassidy service is down"""
        
        with patch.object(
            validation_service.cassidy_client, 
            'health_check', 
            side_effect=Exception("Connection failed")
        ):
            health = await validation_service.health_check()
        
        assert health["service"] == "quick_validation"
        assert health["status"] == "unhealthy"
        assert "error" in health
        assert health["error"] == "Connection failed"

    def test_validate_basic_profile_data_complete(self, validation_service, mock_profile):
        """Test profile data validation with complete data"""
        
        summary, is_valid, warnings = validation_service._validate_basic_profile_data(mock_profile)
        
        assert is_valid is True
        assert summary.full_name == "John Smith"
        assert summary.headline == "Software Engineer at Google"
        assert summary.experience_count == 2
        assert summary.has_basic_info is True
        # May have warnings about missing optional data, but should be valid

    def test_validate_basic_profile_data_minimal(self, validation_service, minimal_profile):
        """Test profile data validation with minimal data"""
        
        summary, is_valid, warnings = validation_service._validate_basic_profile_data(minimal_profile)
        
        assert is_valid is True  # Should still be valid with name and URL
        assert summary.full_name == "Jane Doe"
        assert summary.headline is None
        assert summary.experience_count == 0
        assert summary.has_basic_info is True
        assert len(warnings) > 0  # Should have warnings

    def test_validate_basic_profile_data_invalid(self, validation_service, invalid_profile):
        """Test profile data validation with invalid data"""
        
        summary, is_valid, warnings = validation_service._validate_basic_profile_data(invalid_profile)
        
        assert is_valid is False
        assert summary.full_name is None
        assert summary.has_basic_info is False
        assert len(warnings) > 0
        # Should have warnings about missing name and URL
        warning_text = " ".join(warnings).lower()
        assert "name" in warning_text


if __name__ == "__main__":
    # Run a simple test to verify the service loads correctly
    service = CassidyQuickValidationService()
    print("✅ CassidyQuickValidationService loaded successfully")
    print(f"Service class: {service.__class__.__name__}")
    print(f"Cassidy client: {service.cassidy_client.__class__.__name__}")
