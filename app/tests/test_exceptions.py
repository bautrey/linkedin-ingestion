"""
Tests for custom application exceptions
"""

import pytest
from app.exceptions import (
    LinkedInIngestionError,
    InvalidLinkedInURLError,
    ProfileAlreadyExistsError
)


class TestLinkedInIngestionError:
    """Test the base LinkedInIngestionError exception"""
    
    def test_base_exception_creation(self):
        """Test creating base exception with message"""
        message = "Base ingestion error"
        error = LinkedInIngestionError(message)
        
        assert str(error) == message
        assert error.message == message
        assert error.error_code == "INGESTION_ERROR"
        assert error.status_code is None
        assert error.details == {}
    
    def test_base_exception_with_status_code(self):
        """Test creating base exception with status code"""
        message = "Server error"
        status_code = 500
        error = LinkedInIngestionError(message, status_code=status_code)
        
        assert error.status_code == status_code
        assert error.message == message
    
    def test_base_exception_with_details(self):
        """Test creating base exception with details"""
        message = "Error with details"
        details = {"field": "value", "count": 42}
        error = LinkedInIngestionError(message, details=details)
        
        assert error.details == details
        assert error.message == message
    
    def test_base_exception_inheritance(self):
        """Test that LinkedInIngestionError inherits from Exception"""
        error = LinkedInIngestionError("test")
        assert isinstance(error, Exception)


class TestInvalidLinkedInURLError:
    """Test the InvalidLinkedInURLError exception"""
    
    def test_invalid_url_error_creation(self):
        """Test creating InvalidLinkedInURLError"""
        url = "invalid-url"
        error = InvalidLinkedInURLError(url)
        
        expected_message = f"Invalid LinkedIn URL format: {url}"
        assert str(error) == expected_message
        assert error.message == expected_message
        assert error.error_code == "INVALID_LINKEDIN_URL"
        assert error.status_code == 400
        assert error.url == url
    
    def test_invalid_url_error_with_custom_message(self):
        """Test creating InvalidLinkedInURLError with custom message"""
        url = "bad-url"
        custom_message = "Custom error message"
        error = InvalidLinkedInURLError(url, message=custom_message)
        
        assert str(error) == custom_message
        assert error.message == custom_message
        assert error.url == url
    
    def test_invalid_url_error_inheritance(self):
        """Test that InvalidLinkedInURLError inherits from LinkedInIngestionError"""
        error = InvalidLinkedInURLError("test-url")
        assert isinstance(error, LinkedInIngestionError)
        assert isinstance(error, Exception)
    
    def test_invalid_url_error_suggestions(self):
        """Test that InvalidLinkedInURLError includes helpful suggestions"""
        url = "linkedin.com/in/johndoe"
        error = InvalidLinkedInURLError(url)
        
        assert "suggestions" in error.details
        suggestions = error.details["suggestions"]
        assert len(suggestions) > 0
        assert any("https://" in suggestion for suggestion in suggestions)


class TestProfileAlreadyExistsError:
    """Test the ProfileAlreadyExistsError exception"""
    
    def test_profile_exists_error_creation(self):
        """Test creating ProfileAlreadyExistsError"""
        profile_id = "existing-profile-123"
        error = ProfileAlreadyExistsError(profile_id)
        
        expected_message = f"Profile already exists in database: {profile_id}"
        assert str(error) == expected_message
        assert error.message == expected_message
        assert error.error_code == "PROFILE_ALREADY_EXISTS"
        assert error.status_code == 409
        assert error.profile_id == profile_id
    
    def test_profile_exists_error_with_custom_message(self):
        """Test creating ProfileAlreadyExistsError with custom message"""
        profile_id = "duplicate-123"
        custom_message = "Duplicate found"
        error = ProfileAlreadyExistsError(profile_id, message=custom_message)
        
        assert str(error) == custom_message
        assert error.message == custom_message
        assert error.profile_id == profile_id
    
    def test_profile_exists_error_inheritance(self):
        """Test that ProfileAlreadyExistsError inherits from LinkedInIngestionError"""
        error = ProfileAlreadyExistsError("test-id")
        assert isinstance(error, LinkedInIngestionError)
        assert isinstance(error, Exception)
    
    def test_profile_exists_error_with_existing_profile_data(self):
        """Test ProfileAlreadyExistsError with existing profile data"""
        profile_id = "existing-123"
        existing_data = {
            "name": "John Doe",
            "headline": "Software Engineer",
            "created_at": "2023-07-01"
        }
        error = ProfileAlreadyExistsError(profile_id, existing_profile_data=existing_data)
        
        assert "existing_profile" in error.details
        assert error.details["existing_profile"] == existing_data
    
    def test_profile_exists_error_suggestions(self):
        """Test that ProfileAlreadyExistsError includes actionable suggestions"""
        profile_id = "duplicate-456"
        error = ProfileAlreadyExistsError(profile_id)
        
        assert "suggestions" in error.details
        suggestions = error.details["suggestions"]
        assert len(suggestions) > 0
        assert any("update" in suggestion.lower() for suggestion in suggestions)
        assert any("retrieve" in suggestion.lower() for suggestion in suggestions)


class TestExceptionErrorCodes:
    """Test that all exceptions have unique error codes"""
    
    def test_unique_error_codes(self):
        """Test that each exception has a unique error code"""
        base_error = LinkedInIngestionError("test")
        url_error = InvalidLinkedInURLError("test-url")
        profile_error = ProfileAlreadyExistsError("test-id")
        
        error_codes = [
            base_error.error_code,
            url_error.error_code,
            profile_error.error_code
        ]
        
        # Check that all error codes are unique
        assert len(error_codes) == len(set(error_codes))
        
        # Check specific codes
        assert base_error.error_code == "INGESTION_ERROR"
        assert url_error.error_code == "INVALID_LINKEDIN_URL"
        assert profile_error.error_code == "PROFILE_ALREADY_EXISTS"


class TestExceptionStatusCodes:
    """Test that exceptions have appropriate HTTP status codes"""
    
    def test_status_codes_mapping(self):
        """Test that exceptions map to correct HTTP status codes"""
        base_error = LinkedInIngestionError("test")
        url_error = InvalidLinkedInURLError("test-url")
        profile_error = ProfileAlreadyExistsError("test-id")
        
        # Base error has no default status code
        assert base_error.status_code is None
        
        # URL error should be 400 Bad Request
        assert url_error.status_code == 400
        
        # Profile exists should be 409 Conflict
        assert profile_error.status_code == 409
