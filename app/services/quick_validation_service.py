"""
Quick Validation Service for LinkedIn Profiles

This service performs lightweight validation using Cassidy's profile fetching
without the expensive company processing step. This is Stage 2 of the quality gates system.

Features:
- Quick LinkedIn profile accessibility check via Cassidy
- Basic profile data validation
- Fast failure for inaccessible/invalid profiles
- Minimal resource usage (no company processing)
"""

import asyncio
from typing import Optional, Dict, Any, List, Tuple
from pydantic import BaseModel
from datetime import datetime, timezone
import uuid

from app.core.logging import get_logger
from app.cassidy.client import CassidyClient
from app.cassidy.models import LinkedInProfile
from app.cassidy.exceptions import CassidyWorkflowError, CassidyException

logger = get_logger(__name__)


class QuickValidationResult(BaseModel):
    """Result of quick profile validation"""
    is_valid: bool
    profile_accessible: bool
    basic_data_valid: bool
    validation_errors: List[str] = []
    warnings: List[str] = []
    profile_summary: Optional[Dict[str, Any]] = None
    processing_time_ms: Optional[float] = None
    cassidy_error: Optional[str] = None


class QuickProfileSummary(BaseModel):
    """Lightweight profile summary for validation purposes"""
    profile_id: Optional[str] = None
    full_name: Optional[str] = None
    headline: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    experience_count: int = 0
    has_basic_info: bool = False
    

class CassidyQuickValidationService:
    """
    Quick validation service using Cassidy profile fetch without company processing
    
    This service provides Stage 2 validation in the quality gates system by:
    1. Using Cassidy to fetch the LinkedIn profile (validates accessibility)
    2. Checking basic profile data completeness
    3. Returning lightweight summary without expensive company processing
    """
    
    def __init__(self):
        self.cassidy_client = CassidyClient()
        self.logger = get_logger(__name__)
    
    async def quick_validate_profile(self, linkedin_url: str) -> QuickValidationResult:
        """
        Perform quick validation of LinkedIn profile accessibility and basic data
        
        This is the main method for Stage 2 of quality gates - uses Cassidy to
        fetch profile but skips company processing for speed.
        
        Args:
            linkedin_url: Sanitized LinkedIn URL from Stage 1
            
        Returns:
            QuickValidationResult with validation status and profile summary
        """
        start_time = datetime.now()
        validation_id = str(uuid.uuid4())[:8]
        
        self.logger.info(
            f"🔍 QUICK_VALIDATION_START: Starting profile accessibility check",
            validation_id=validation_id,
            linkedin_url=linkedin_url,
            stage="STAGE_2_CASSIDY_VALIDATION"
        )
        
        validation_errors = []
        warnings = []
        profile_summary = None
        profile_accessible = False
        basic_data_valid = False
        cassidy_error = None
        
        try:
            # Step 1: Attempt to fetch profile from Cassidy (this validates accessibility)
            try:
                self.logger.info("Fetching profile from Cassidy for validation", validation_id=validation_id)
                profile = await self.cassidy_client.fetch_profile(linkedin_url)
                profile_accessible = True
                
                self.logger.info(
                    f"✅ PROFILE_FETCH_SUCCESS: Cassidy profile fetch successful",
                    validation_id=validation_id,
                    profile_name=getattr(profile, 'full_name', getattr(profile, 'name', 'Unknown')),
                    stage="STAGE_2_CASSIDY_VALIDATION"
                )
                
            except CassidyWorkflowError as e:
                cassidy_error = str(e)
                profile_accessible = False
                
                # Check if this is a URL format error
                if "not a valid LinkedIn profile URL" in str(e):
                    validation_errors.append("LinkedIn URL is not accessible or has invalid format")
                    self.logger.warning(
                        f"❌ PROFILE_ACCESS_FAILED: LinkedIn URL not accessible",
                        validation_id=validation_id,
                        error="Invalid URL format detected by Cassidy",
                        stage="STAGE_2_CASSIDY_VALIDATION"
                    )
                else:
                    validation_errors.append(f"Profile fetch failed: {str(e)}")
                    self.logger.warning(
                        f"❌ PROFILE_FETCH_FAILED: Cassidy workflow error",
                        validation_id=validation_id,
                        error=str(e),
                        stage="STAGE_2_CASSIDY_VALIDATION"
                    )
                
                # Return early failure - no point in further validation
                return QuickValidationResult(
                    is_valid=False,
                    profile_accessible=False,
                    basic_data_valid=False,
                    validation_errors=validation_errors,
                    warnings=warnings,
                    cassidy_error=cassidy_error,
                    processing_time_ms=self._get_processing_time(start_time)
                )
                
            except CassidyException as e:
                cassidy_error = str(e)
                profile_accessible = False
                validation_errors.append(f"Cassidy API error: {str(e)}")
                
                self.logger.error(
                    f"❌ CASSIDY_API_ERROR: Cassidy service error",
                    validation_id=validation_id,
                    error=str(e),
                    error_type=type(e).__name__,
                    stage="STAGE_2_CASSIDY_VALIDATION"
                )
                
                return QuickValidationResult(
                    is_valid=False,
                    profile_accessible=False,
                    basic_data_valid=False,
                    validation_errors=validation_errors,
                    warnings=warnings,
                    cassidy_error=cassidy_error,
                    processing_time_ms=self._get_processing_time(start_time)
                )
            
            # Step 2: Validate basic profile data completeness
            if profile_accessible and profile:
                profile_summary, basic_data_valid, data_warnings = self._validate_basic_profile_data(profile)
                warnings.extend(data_warnings)
                
                if basic_data_valid:
                    self.logger.info(
                        f"✅ DATA_VALIDATION_SUCCESS: Profile has sufficient basic data",
                        validation_id=validation_id,
                        profile_name=profile_summary.full_name,
                        has_experience=profile_summary.experience_count > 0,
                        stage="STAGE_2_CASSIDY_VALIDATION"
                    )
                else:
                    self.logger.warning(
                        f"⚠️ DATA_VALIDATION_WARNING: Profile has minimal data",
                        validation_id=validation_id,
                        profile_name=profile_summary.full_name,
                        warnings=data_warnings,
                        stage="STAGE_2_CASSIDY_VALIDATION"
                    )
            
            # Step 3: Overall validation result
            is_valid = profile_accessible and basic_data_valid
            
            processing_time = self._get_processing_time(start_time)
            
            if is_valid:
                self.logger.info(
                    f"🎉 QUICK_VALIDATION_SUCCESS: Profile validation completed successfully",
                    validation_id=validation_id,
                    profile_name=profile_summary.full_name if profile_summary else "Unknown",
                    processing_time_ms=processing_time,
                    stage="STAGE_2_CASSIDY_VALIDATION",
                    status="PASSED"
                )
            else:
                self.logger.warning(
                    f"🚫 QUICK_VALIDATION_FAILED: Profile validation failed",
                    validation_id=validation_id,
                    errors=validation_errors,
                    warnings=warnings,
                    processing_time_ms=processing_time,
                    stage="STAGE_2_CASSIDY_VALIDATION",
                    status="FAILED"
                )
            
            return QuickValidationResult(
                is_valid=is_valid,
                profile_accessible=profile_accessible,
                basic_data_valid=basic_data_valid,
                validation_errors=validation_errors,
                warnings=warnings,
                profile_summary=profile_summary.model_dump() if profile_summary else None,
                cassidy_error=cassidy_error,
                processing_time_ms=processing_time
            )
        
        except Exception as e:
            self.logger.error(
                f"❌ QUICK_VALIDATION_ERROR: Unexpected error during validation",
                validation_id=validation_id,
                error=str(e),
                error_type=type(e).__name__,
                stage="STAGE_2_CASSIDY_VALIDATION"
            )
            
            validation_errors.append(f"Unexpected validation error: {str(e)}")
            
            return QuickValidationResult(
                is_valid=False,
                profile_accessible=False,
                basic_data_valid=False,
                validation_errors=validation_errors,
                warnings=warnings,
                processing_time_ms=self._get_processing_time(start_time)
            )
    
    def _validate_basic_profile_data(self, profile: LinkedInProfile) -> Tuple[QuickProfileSummary, bool, List[str]]:
        """
        Validate basic profile data completeness without deep processing
        
        Args:
            profile: LinkedInProfile from Cassidy
            
        Returns:
            Tuple of (profile_summary, is_valid, warnings)
        """
        warnings = []
        
        # Extract basic profile information
        profile_summary = QuickProfileSummary(
            profile_id=getattr(profile, 'profile_id', getattr(profile, 'id', None)),
            full_name=getattr(profile, 'full_name', getattr(profile, 'name', None)),
            headline=getattr(profile, 'headline', getattr(profile, 'position', None)),
            company=getattr(profile, 'company', None),
            location=getattr(profile, 'location', getattr(profile, 'city', None)),
            linkedin_url=getattr(profile, 'linkedin_url', getattr(profile, 'url', None)),
            experience_count=len(getattr(profile, 'experience', getattr(profile, 'experiences', [])))
        )
        
        # Check if profile has basic required information
        has_name = bool(profile_summary.full_name and profile_summary.full_name.strip())
        has_url = bool(profile_summary.linkedin_url and profile_summary.linkedin_url.strip())
        
        profile_summary.has_basic_info = has_name and has_url
        
        # Validation criteria for basic data
        is_valid = True
        
        if not has_name:
            warnings.append("Profile has no name or empty name")
            is_valid = False
        
        if not has_url:
            warnings.append("Profile has no LinkedIn URL")
            is_valid = False
        
        if not profile_summary.headline:
            warnings.append("Profile has no headline/position information")
            # Don't fail validation for missing headline - it's common
        
        if profile_summary.experience_count == 0:
            warnings.append("Profile has no work experience listed")
            # Don't fail validation for no experience - might be valid for some roles
        
        return profile_summary, is_valid, warnings
    
    def _get_processing_time(self, start_time: datetime) -> float:
        """Calculate processing time in milliseconds"""
        end_time = datetime.now()
        return (end_time - start_time).total_seconds() * 1000
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of quick validation service"""
        try:
            cassidy_health = await self.cassidy_client.health_check()
            return {
                "service": "quick_validation",
                "status": "healthy" if cassidy_health.get("status") == "healthy" else "degraded",
                "cassidy_api": cassidy_health,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            return {
                "service": "quick_validation", 
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
