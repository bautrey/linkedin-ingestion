"""
Error response models for LinkedIn Ingestion Service API

Provides standardized error response formats with comprehensive OpenAPI documentation
for consistent error handling across all endpoints.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime


class ErrorResponse(BaseModel):
    """
    Standardized error response model for API endpoints.
    
    This model ensures consistent error formatting across all API responses,
    providing clients with predictable error information including error codes,
    messages, and optional details for debugging.
    """
    
    error_code: str = Field(
        ...,
        description="Machine-readable error code identifying the specific error type",
        example="LINKEDIN_API_ERROR",
        min_length=1,
        max_length=100
    )
    
    message: str = Field(
        ...,
        description="Human-readable error message describing what went wrong",
        example="Failed to retrieve LinkedIn profile data",
        min_length=1,
        max_length=500
    )
    
    details: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional additional details about the error for debugging purposes",
        example={
            "status_code": 500,
            "endpoint": "/api/linkedin/profile",
            "cassidy_error": "Connection timeout"
        }
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC timestamp when the error occurred",
        example="2024-01-15T10:30:00Z"
    )
    
    request_id: Optional[str] = Field(
        None,
        description="Unique identifier for the request that caused this error",
        example="req_abc123def456",
        min_length=1,
        max_length=50
    )
    
    validation_errors: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="List of validation errors when request data is invalid",
        example=[
            {
                "field": "linkedin_url",
                "message": "Invalid LinkedIn URL format",
                "invalid_value": "not-a-url"
            }
        ]
    )

    class Config:
        """Pydantic model configuration"""
        json_encoders = {
            datetime: lambda v: v.isoformat() + "Z"
        }
        schema_extra = {
            "example": {
                "error_code": "LINKEDIN_API_ERROR",
                "message": "Failed to retrieve LinkedIn profile data",
                "details": {
                    "status_code": 500,
                    "endpoint": "/api/linkedin/profile",
                    "cassidy_error": "Connection timeout"
                },
                "timestamp": "2024-01-15T10:30:00Z",
                "request_id": "req_abc123def456",
                "validation_errors": None
            }
        }


class ValidationErrorResponse(ErrorResponse):
    """
    Specialized error response for validation errors.
    
    Extends the base ErrorResponse with validation-specific defaults
    and ensures validation_errors field is always populated.
    """
    
    error_code: str = Field(
        default="VALIDATION_ERROR",
        description="Error code for validation failures",
        example="VALIDATION_ERROR"
    )
    
    validation_errors: List[Dict[str, Any]] = Field(
        ...,
        description="List of validation errors with field-specific details",
        min_items=1,
        example=[
            {
                "field": "linkedin_url",
                "message": "Invalid LinkedIn URL format",
                "invalid_value": "not-a-url",
                "expected_format": "https://www.linkedin.com/in/username"
            }
        ]
    )

    class Config:
        """Pydantic model configuration for validation errors"""
        schema_extra = {
            "example": {
                "error_code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": {
                    "total_errors": 2,
                    "endpoint": "/api/linkedin/profile"
                },
                "timestamp": "2024-01-15T10:30:00Z",
                "request_id": "req_validation_123",
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
