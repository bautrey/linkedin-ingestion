"""
Models package for LinkedIn Ingestion Service

Contains Pydantic models for request/response validation and API documentation.
"""

from .errors import ErrorResponse, ValidationErrorResponse
from .canonical import (
    CanonicalProfile,
    CanonicalCompany,
    CanonicalEducationEntry,
    CanonicalExperienceEntry,
    CanonicalWorkflowStatus,
    CanonicalFundingInfo,
    CanonicalCompanyLocation,
    CanonicalAffiliatedCompany,
)

__all__ = [
    "ErrorResponse", 
    "ValidationErrorResponse",
    # Canonical models
    "CanonicalProfile",
    "CanonicalCompany",
    "CanonicalEducationEntry",
    "CanonicalExperienceEntry",
    "CanonicalWorkflowStatus",
    "CanonicalFundingInfo",
    "CanonicalCompanyLocation",
    "CanonicalAffiliatedCompany",
]
