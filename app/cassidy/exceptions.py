"""
Custom exceptions for Cassidy integration
"""

from typing import Optional, Dict, Any


class CassidyException(Exception):
    """Base exception for Cassidy-related errors"""
    
    def __init__(self, message: str, status_code: Optional[int] = None, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class CassidyAPIError(CassidyException):
    """Raised when Cassidy API returns an error response"""
    pass


class CassidyTimeoutError(CassidyException):
    """Raised when Cassidy workflow times out"""
    pass


class CassidyWorkflowError(CassidyException):
    """Raised when Cassidy workflow fails or returns invalid data"""
    pass


class CassidyRateLimitError(CassidyException):
    """Raised when hitting Cassidy API rate limits"""
    pass


class CassidyConnectionError(CassidyException):
    """Raised when connection to Cassidy API fails"""
    pass


class CassidyValidationError(CassidyException):
    """Raised when Cassidy response data validation fails"""
    pass
