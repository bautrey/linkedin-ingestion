"""
Stage 1: LinkedIn Profile Verification Endpoint

Calls Cassidy to verify a LinkedIn URL returns valid profile data.
This is the first stage of the 3-stage evaluation workflow.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, HttpUrl, Field
from typing import Dict, Any, Optional
import asyncio
import urllib.parse
from datetime import datetime

from app.core.logging import LoggerMixin
from app.cassidy.client import CassidyClient
from app.cassidy.exceptions import CassidyAPIError, CassidyTimeoutError, CassidyWorkflowError
from app.cassidy.models import ProfileIngestionRequest

router = APIRouter(prefix="/api/v1/profiles", tags=["Profile Verification"])


def normalize_and_clean_linkedin_url(url: str) -> str:
    """
    Normalize and clean LinkedIn profile URLs to consistent format.
    Handles encoding issues, BOMs, and malformed URLs.
    
    Args:
        url: Raw LinkedIn URL (possibly malformed)
        
    Returns:
        Cleaned and normalized LinkedIn URL
    """
    # Strip whitespace
    url = url.strip()
    
    # Remove any trailing encoded BOM sequences like %EF%BB%BF BEFORE URL decoding
    bom_sequences = ['%EF%BB%BF', '%FEFF', '%200B', '%200C', '%200D']
    for bom_seq in bom_sequences:
        if bom_seq.lower() in url.lower():
            url = url.replace(bom_seq, '').replace(bom_seq.lower(), '')
    
    # URL decode any percent-encoded characters
    try:
        url = urllib.parse.unquote(url, errors='ignore')
    except Exception:
        # If URL decoding fails, continue with original
        pass
    
    # Remove BOM characters (after decoding)
    bom_chars = ['\ufeff', '\u200b', '\u200c', '\u200d', '\ufffe', '\uffff']
    for bom_char in bom_chars:
        url = url.replace(bom_char, '')
    
    # Strip again after cleaning
    url = url.strip()
    
    # Ensure https protocol
    if not url.startswith('http'):
        url = 'https://' + url
    
    # Ensure www subdomain for linkedin.com
    if '://linkedin.com' in url:
        url = url.replace('://linkedin.com', '://www.linkedin.com')
    
    # Ensure trailing slash
    if not url.endswith('/'):
        url += '/'
    
    return url


class ProfileVerificationRequest(BaseModel):
    """Request model for profile verification"""
    linkedin_url: HttpUrl = Field(..., description="LinkedIn profile URL to verify")
    
    class Config:
        json_schema_extra = {
            "example": {
                "linkedin_url": "https://www.linkedin.com/in/sample-profile"
            }
        }


class ProfileVerificationResponse(BaseModel):
    """Response model for profile verification"""
    verified: bool = Field(..., description="Whether the profile was successfully verified")
    linkedin_url: str = Field(..., description="The original LinkedIn URL")
    
    # Success fields
    profile_data: Optional[Dict[str, Any]] = Field(None, description="Basic profile data if verified")
    data_completeness: Optional[str] = Field(None, description="Assessment of data completeness")
    executive_indicators: Optional[bool] = Field(None, description="Whether profile shows executive experience")
    proceed_to_sanity_check: Optional[bool] = Field(None, description="Whether to proceed to Stage 2")
    cassidy_response_time: Optional[float] = Field(None, description="Time taken by Cassidy API call")
    
    # Error fields
    error: Optional[str] = Field(None, description="Error message if verification failed")
    error_type: Optional[str] = Field(None, description="Type of error encountered")
    cassidy_error: Optional[str] = Field(None, description="Raw error from Cassidy API")
    
    class Config:
        json_schema_extra = {
            "example": {
                "verified": True,
                "linkedin_url": "https://www.linkedin.com/in/sample-profile",
                "profile_data": {
                    "name": "John Doe",
                    "headline": "CTO at TechCorp", 
                    "about": "Experienced technology leader...",
                    "experience_count": 5,
                    "education_count": 2,
                    "city": "San Francisco",
                    "country": "United States"
                },
                "data_completeness": "COMPLETE",
                "executive_indicators": True,
                "proceed_to_sanity_check": True,
                "cassidy_response_time": 4.2
            }
        }


class ProfileVerificationService(LoggerMixin):
    """Service class for profile verification logic"""
    
    def __init__(self):
        self.cassidy_client = CassidyClient()
    
    async def verify_profile(self, linkedin_url: str) -> ProfileVerificationResponse:
        """
        Verify a LinkedIn profile by calling Cassidy
        
        Args:
            linkedin_url: LinkedIn profile URL to verify
            
        Returns:
            ProfileVerificationResponse with verification results
        """
        start_time = datetime.now()
        
        self.logger.info("Starting profile verification", linkedin_url=linkedin_url)
        
        try:
            # Call Cassidy to fetch profile data (no company ingestion)
            profile = await self.cassidy_client.fetch_profile(linkedin_url)
            
            # Calculate response time
            response_time = (datetime.now() - start_time).total_seconds()
            
            # Extract basic profile data for response
            profile_data = {
                "name": profile.full_name or profile.name,
                "headline": profile.headline,
                "about": profile.about[:200] + "..." if profile.about and len(profile.about) > 200 else profile.about,
                "experience_count": len(profile.experiences) if profile.experiences else 0,
                "education_count": len(profile.educations) if profile.educations else 0,
                "city": profile.city,
                "country": profile.country,
                "company": profile.company,
                "job_title": profile.job_title
            }
            
            # Assess data completeness
            required_fields = [profile.full_name or profile.name, profile.headline, profile.experiences]
            missing_count = sum(1 for field in required_fields if not field)
            data_completeness = "COMPLETE" if missing_count == 0 else "PARTIAL" if missing_count <= 1 else "INSUFFICIENT"
            
            # Check for executive indicators
            executive_indicators = self._has_executive_indicators(profile)
            
            # Determine if should proceed to sanity check
            proceed_to_sanity_check = (
                data_completeness in ["COMPLETE", "PARTIAL"] and
                executive_indicators and
                (profile.experiences and len(profile.experiences) > 0)
            )
            
            self.logger.info(
                "Profile verification completed successfully",
                linkedin_url=linkedin_url,
                verified=True,
                data_completeness=data_completeness,
                executive_indicators=executive_indicators,
                proceed_to_sanity_check=proceed_to_sanity_check,
                response_time=response_time
            )
            
            return ProfileVerificationResponse(
                verified=True,
                linkedin_url=linkedin_url,
                profile_data=profile_data,
                data_completeness=data_completeness,
                executive_indicators=executive_indicators,
                proceed_to_sanity_check=proceed_to_sanity_check,
                cassidy_response_time=response_time
            )
            
        except CassidyAPIError as e:
            self.logger.error(
                "Cassidy API error during profile verification",
                linkedin_url=linkedin_url,
                error=str(e),
                status_code=getattr(e, 'status_code', None)
            )
            
            return ProfileVerificationResponse(
                verified=False,
                linkedin_url=linkedin_url,
                error="Profile verification failed due to API error",
                error_type="CassidyAPIError",
                cassidy_error=str(e)
            )
            
        except CassidyTimeoutError as e:
            self.logger.error(
                "Cassidy timeout during profile verification",
                linkedin_url=linkedin_url,
                error=str(e)
            )
            
            return ProfileVerificationResponse(
                verified=False,
                linkedin_url=linkedin_url,
                error="Profile verification timed out",
                error_type="CassidyTimeoutError",
                cassidy_error=str(e)
            )
            
        except CassidyWorkflowError as e:
            self.logger.error(
                "Cassidy workflow error during profile verification",
                linkedin_url=linkedin_url,
                error=str(e)
            )
            
            return ProfileVerificationResponse(
                verified=False,
                linkedin_url=linkedin_url,
                error="Invalid LinkedIn URL or profile not accessible",
                error_type="CassidyWorkflowError", 
                cassidy_error=str(e)
            )
            
        except Exception as e:
            self.logger.error(
                "Unexpected error during profile verification",
                linkedin_url=linkedin_url,
                error=str(e),
                error_type=type(e).__name__
            )
            
            return ProfileVerificationResponse(
                verified=False,
                linkedin_url=linkedin_url,
                error=f"Unexpected error: {str(e)}",
                error_type=type(e).__name__
            )
    
    def _has_executive_indicators(self, profile) -> bool:
        """
        Check if profile shows executive-level experience indicators
        
        Args:
            profile: LinkedInProfile object
            
        Returns:
            bool indicating if executive indicators are present
        """
        executive_keywords = [
            'chief', 'cto', 'cio', 'ciso', 'ceo', 'cfo', 'coo',
            'vice president', 'vp', 'director', 'head of', 'lead',
            'senior director', 'executive', 'president', 'founder'
        ]
        
        # Check current headline/title
        if profile.headline:
            headline_lower = profile.headline.lower()
            if any(keyword in headline_lower for keyword in executive_keywords):
                return True
        
        # Check job title
        if profile.job_title:
            job_title_lower = profile.job_title.lower()
            if any(keyword in job_title_lower for keyword in executive_keywords):
                return True
        
        # Check experience titles
        if profile.experiences:
            for exp in profile.experiences:
                if exp.title:
                    title_lower = exp.title.lower()
                    if any(keyword in title_lower for keyword in executive_keywords):
                        return True
        
        return False


# Initialize the service
verification_service = ProfileVerificationService()


@router.post("/verify", response_model=ProfileVerificationResponse, summary="Verify LinkedIn Profile")
async def verify_linkedin_profile(request: ProfileVerificationRequest) -> ProfileVerificationResponse:
    """
    **Stage 1: Profile Verification**
    
    Verify that a LinkedIn URL returns valid profile data from Cassidy.
    This is the first stage of the 3-stage evaluation workflow.
    
    - **Calls Cassidy**: Uses profile workflow (no company ingestion)
    - **Validates Data**: Checks for required fields and executive indicators  
    - **Fast Response**: Optimized for quick verification
    - **Gateway**: Determines if profile should proceed to Stage 2 screening
    
    **Next Steps**:
    - If `proceed_to_sanity_check` is `true`, proceed to Stage 2 with `/api/v1/profiles/score`
    - If `false`, stop the evaluation process
    """
    try:
        # Clean and normalize URL first to handle BOM and encoding issues
        raw_url = str(request.linkedin_url)
        cleaned_url = normalize_and_clean_linkedin_url(raw_url)
        
        # Use Pydantic URL validation with cleaned URL
        validated_request = ProfileIngestionRequest(linkedin_url=cleaned_url)
        normalized_url = str(validated_request.linkedin_url)
        
        result = await verification_service.verify_profile(normalized_url)
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "Invalid LinkedIn URL format",
                "message": str(e),
                "raw_url": str(request.linkedin_url),
                "suggestions": [
                    "Use the modern LinkedIn URL format: https://www.linkedin.com/in/username",
                    "Ensure the LinkedIn URL is publicly accessible",
                    "Remove any invisible characters or encoding artifacts from the URL",
                    "Avoid old LinkedIn URL formats like /pub/ which are no longer supported"
                ]
            }
        )
