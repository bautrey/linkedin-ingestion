"""
Error response models for LinkedIn Ingestion Service API

Provides standardized error response formats with comprehensive OpenAPI documentation
for consistent error handling across all endpoints.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict


class ErrorResponse(BaseModel):
    """
    Standardized error response model for API endpoints.
    
    This model ensures consistent error formatting across all API responses,
    providing clients with predictable error information including error codes,
    messages, and optional details for debugging.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error_code": "LINKEDIN_API_ERROR",
                "message": "Failed to retrieve LinkedIn profile data",
                "details": {
                    "status_code": 500,
                    "endpoint": "/api/linkedin/profile",
                    "cassidy_error": "Connection timeout"
                },
                "suggestions": [
                    "Check your internet connection",
                    "Verify the LinkedIn profile URL is accessible",
                    "Try again in a few minutes"
                ]
            }
        }
    )
    
    error_code: str = Field(
        ...,
        description="Machine-readable error code identifying the specific error type",
        json_schema_extra={"example": "LINKEDIN_API_ERROR"}
    )
    
    message: str = Field(
        ...,
        description="Human-readable error message describing what went wrong",
        json_schema_extra={"example": "Failed to retrieve LinkedIn profile data"}
    )
    
    details: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional additional details about the error for debugging purposes",
        json_schema_extra={
            "example": {
                "status_code": 500,
                "endpoint": "/api/linkedin/profile",
                "cassidy_error": "Connection timeout"
            }
        }
    )
    
    suggestions: Optional[List[str]] = Field(
        None,
        description="List of actionable suggestions to help resolve the error",
        json_schema_extra={
            "example": [
                "Use the format: https://www.linkedin.com/in/username",
                "Check the URL for typos or missing components",
                "Verify the profile is publicly accessible"
            ]
        }
    )


class ValidationErrorResponse(ErrorResponse):
    """
    Specialized error response for validation errors.
    
    Extends the base ErrorResponse with validation-specific defaults
    and ensures validation_errors field is always populated.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error_code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": {
                    "total_errors": 2,
                    "endpoint": "/api/linkedin/profile"
                },
                "validation_errors": [
                    {
                        "field": "linkedin_url",
                        "message": "Invalid LinkedIn URL format",
                        "invalid_value": "not-a-url",
                        "expected_format": "https://www.linkedin.com/in/username"
                    },
                    {
                        "field": "timeout",
                        "message": "Timeout must be between 1 and 300 seconds",
                        "invalid_value": 500,
                        "min_value": 1,
                        "max_value": 300
                    }
                ]
            }
        }
    )
    
    error_code: str = Field(
        default="VALIDATION_ERROR",
        description="Error code for validation failures",
        json_schema_extra={"example": "VALIDATION_ERROR"}
    )
    
    validation_errors: List[Dict[str, Any]] = Field(
        ...,
        description="List of validation errors with field-specific details",
        min_length=1,
        json_schema_extra={
            "example": [
                {
                    "field": "linkedin_url",
                    "message": "Invalid LinkedIn URL format",
                    "invalid_value": "not-a-url",
                    "expected_format": "https://www.linkedin.com/in/username"
                }
            ]
        }
    )
