"""
Custom exceptions for LinkedIn ingestion application
"""

from typing import Optional, Dict, Any, List


class LinkedInIngestionError(Exception):
    """Base exception for LinkedIn ingestion errors"""
    
    def __init__(
        self, 
        message: str, 
        status_code: Optional[int] = None, 
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = "INGESTION_ERROR"
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class InvalidLinkedInURLError(LinkedInIngestionError):
    """Raised when a LinkedIn URL is invalid or malformed"""
    
    def __init__(
        self, 
        url: str, 
        message: Optional[str] = None, 
        details: Optional[Dict[str, Any]] = None
    ):
        self.url = url
        
        if message is None:
            message = f"Invalid LinkedIn URL format: {url}"
        
        # Generate helpful suggestions
        suggestions = [
            f"Try adding https:// to the beginning: https://{url}",
            "Ensure the URL follows the format: https://linkedin.com/in/username",
            "Check that the URL is a valid LinkedIn profile link"
        ]
        
        # Merge details with suggestions
        combined_details = details or {}
        combined_details["suggestions"] = suggestions
        
        super().__init__(message, status_code=400, details=combined_details)
        self.error_code = "INVALID_LINKEDIN_URL"


class ProfileAlreadyExistsError(LinkedInIngestionError):
    """Raised when attempting to create a profile that already exists"""
    
    def __init__(
        self, 
        profile_id: str, 
        message: Optional[str] = None, 
        existing_profile_data: Optional[Dict[str, Any]] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.profile_id = profile_id
        
        if message is None:
            message = f"Profile already exists in database: {profile_id}"
        
        # Generate actionable suggestions
        suggestions = [
            f"Use the update endpoint to modify the existing profile: PUT /api/v1/profiles/{profile_id}",
            f"Retrieve the existing profile data: GET /api/v1/profiles/{profile_id}",
            "Use force_update=true parameter to overwrite the existing profile"
        ]
        
        # Combine details
        combined_details = details or {}
        combined_details["suggestions"] = suggestions
        
        if existing_profile_data:
            combined_details["existing_profile"] = existing_profile_data
        
        super().__init__(message, status_code=409, details=combined_details)
        self.error_code = "PROFILE_ALREADY_EXISTS"
