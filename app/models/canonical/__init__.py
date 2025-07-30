"""
Canonical models package for LinkedIn data.

These models serve as the internal, stable data contract for the application,
decoupling it from the specific structure of any single data provider.
"""

from .profile import (
    CanonicalProfile,
    CanonicalEducationEntry,
    CanonicalExperienceEntry,
    CanonicalWorkflowStatus,
)
from .company import (
    CanonicalCompany,
    CanonicalFundingInfo,
    CanonicalCompanyLocation,
    CanonicalAffiliatedCompany,
)

__all__ = [
    # Profile models
    "CanonicalProfile",
    "CanonicalEducationEntry",
    "CanonicalExperienceEntry",
    "CanonicalWorkflowStatus",
    # Company models
    "CanonicalCompany",
    "CanonicalFundingInfo",
    "CanonicalCompanyLocation",
    "CanonicalAffiliatedCompany",
]
