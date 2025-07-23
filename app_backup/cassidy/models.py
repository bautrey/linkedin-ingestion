"""
Pydantic models for Cassidy LinkedIn workflow responses

Fixed models based on actual Cassidy API response structure observed in debug output
"""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, HttpUrl, validator
from datetime import datetime
from enum import Enum


class WorkflowStatus(str, Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"


# Education Entry from actual API
class EducationEntry(BaseModel):
    """Education entry matching actual Cassidy API response"""
    activities: Optional[str] = None
    date_range: Optional[str] = None
    degree: Optional[str] = None
    end_month: Optional[str] = None
    end_year: Optional[int] = None
    field_of_study: Optional[str] = None
    school: Optional[str] = None
    school_id: Optional[str] = None
    school_linkedin_url: Optional[str] = None
    start_month: Optional[str] = None
    start_year: Optional[int] = None
    
    @validator('end_year', 'start_year', pre=True)
    def handle_empty_year(cls, v):
        """Handle empty string years"""
        if v == "":
            return None
        if isinstance(v, str) and v.isdigit():
            return int(v)
        return v


# Experience Entry from actual API
class ExperienceEntry(BaseModel):
    """Experience entry matching actual Cassidy API response"""
    company: Optional[str] = None
    company_id: Optional[str] = None
    company_linkedin_url: Optional[str] = None
    company_logo_url: Optional[str] = None
    current_job: Optional[bool] = None
    date_range: Optional[str] = None
    description: Optional[str] = None
    end_month: Optional[str] = None
    end_year: Optional[int] = None
    job_title: Optional[str] = None
    location: Optional[str] = None
    start_month: Optional[str] = None
    start_year: Optional[int] = None
    
    @validator('end_year', 'start_year', pre=True)
    def handle_empty_year(cls, v):
        """Handle empty string years"""
        if v == "":
            return None
        if isinstance(v, str) and v.isdigit():
            return int(v)
        return v
    
    @validator('start_month', 'end_month', pre=True)
    def handle_month(cls, v):
        """Handle month fields that might be int or string"""
        if isinstance(v, int):
            return str(v)
        return v


# Current Company Info
class CurrentCompanyInfo(BaseModel):
    """Current company information"""
    name: Optional[str] = None
    position: Optional[str] = None
    linkedin_url: Optional[str] = None


class LinkedInProfile(BaseModel):
    """LinkedIn profile matching actual Cassidy API response structure"""
    
    # Core fields - mapped from actual API response
    profile_id: str = Field(..., description="LinkedIn profile ID")
    full_name: str = Field(..., description="Full name")
    linkedin_url: HttpUrl = Field(..., description="LinkedIn profile URL")
    
    # Additional profile fields from actual API
    about: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None  # Not country_code
    headline: Optional[str] = None  # This is the position/title
    location: Optional[str] = None
    state: Optional[str] = None
    
    # Company information
    company: Optional[str] = None
    job_title: Optional[str] = None
    company_description: Optional[str] = None
    company_domain: Optional[str] = None
    company_employee_count: Optional[int] = None
    company_employee_range: Optional[str] = None
    company_industry: Optional[str] = None
    company_linkedin_url: Optional[str] = None
    company_logo_url: Optional[str] = None
    company_website: Optional[str] = None
    company_year_founded: Optional[str] = None  # Note: comes as string, might be empty
    
    # Social metrics
    follower_count: Optional[int] = None
    connection_count: Optional[int] = None
    
    # Current job details
    current_company_join_month: Optional[int] = None
    current_company_join_year: Optional[int] = None
    current_job_duration: Optional[str] = None
    
    # Profile flags
    is_creator: Optional[bool] = None
    is_influencer: Optional[bool] = None
    is_premium: Optional[bool] = None
    is_verified: Optional[bool] = None
    
    # Contact information
    email: Optional[str] = None
    phone: Optional[str] = None
    
    # Profile details
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    profile_image_url: Optional[str] = None
    public_id: Optional[str] = None
    urn: Optional[str] = None
    
    # HQ information
    hq_city: Optional[str] = None
    hq_country: Optional[str] = None
    hq_region: Optional[str] = None
    
    # Education info
    school: Optional[str] = None
    
    # Arrays
    educations: List[EducationEntry] = Field(default_factory=list)
    experiences: List[ExperienceEntry] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)
    
    # Timestamp
    timestamp: Optional[datetime] = None
    
    # Convenience properties to maintain compatibility with existing code
    @property
    def id(self) -> str:
        """Alias for profile_id for backward compatibility"""
        return self.profile_id
    
    @property
    def name(self) -> str:
        """Alias for full_name for backward compatibility"""
        return self.full_name
        
    @property
    def url(self) -> HttpUrl:
        """Alias for linkedin_url for backward compatibility"""
        return self.linkedin_url
    
    @property
    def position(self) -> Optional[str]:
        """Alias for headline for backward compatibility"""
        return self.headline
    
    @property
    def country_code(self) -> Optional[str]:
        """Map country to country_code for backward compatibility"""
        return self.country
        
    @property
    def followers(self) -> Optional[int]:
        """Alias for follower_count for backward compatibility"""
        return self.follower_count
        
    @property
    def connections(self) -> Optional[int]:
        """Alias for connection_count for backward compatibility"""
        return self.connection_count
    
    @property
    def experience(self) -> List[ExperienceEntry]:
        """Alias for experiences for backward compatibility"""
        return self.experiences
        
    @property
    def education(self) -> List[EducationEntry]:
        """Alias for educations for backward compatibility"""
        return self.educations
        
    @property
    def certifications(self) -> List[Dict]:
        """Empty list for backward compatibility"""
        return []
    
    @property
    def current_company(self) -> Optional[Dict[str, str]]:
        """Build current company info from available fields"""
        if self.company:
            return {
                "name": self.company,
                "position": self.job_title or self.headline,
                "linkedin_url": self.company_linkedin_url
            }
        return None


# Company funding info from actual API
class FundingInfo(BaseModel):
    """Company funding information matching actual API"""
    crunchbase_url: Optional[str] = None
    last_funding_round_amount: Optional[str] = None
    last_funding_round_currency: Optional[str] = None
    last_funding_round_investor_count: Optional[int] = None
    last_funding_round_month: Optional[int] = None  # Note: API returns int, not string
    last_funding_round_type: Optional[str] = None
    last_funding_round_year: Optional[int] = None   # Note: API returns int, not string


# Company location from actual API
class CompanyLocation(BaseModel):
    """Company location matching actual API"""
    city: Optional[str] = None
    country: Optional[str] = None
    full_address: Optional[str] = None
    is_headquarter: Optional[bool] = None
    line1: Optional[str] = None
    line2: Optional[str] = None
    region: Optional[str] = None
    zipcode: Optional[str] = None


# Affiliated company from actual API
class AffiliatedCompany(BaseModel):
    """Affiliated company information"""
    company_id: Optional[str] = None
    linkedin_url: Optional[str] = None
    name: Optional[str] = None


class CompanyProfile(BaseModel):
    """Company profile matching actual Cassidy API response structure"""
    
    # Core fields from actual API
    company_id: str = Field(..., description="LinkedIn company ID")
    company_name: str = Field(..., description="Company name")
    
    # Optional company information
    description: Optional[str] = None
    domain: Optional[str] = None
    email: Optional[str] = None
    employee_count: Optional[int] = None
    employee_range: Optional[str] = None
    follower_count: Optional[int] = None
    linkedin_url: Optional[HttpUrl] = None
    logo_url: Optional[str] = None
    phone: Optional[str] = None
    specialties: Optional[str] = None
    tagline: Optional[str] = None
    website: Optional[str] = None
    year_founded: Optional[str] = None  # Note: comes as string, might be empty
    
    # Address information
    hq_address_line1: Optional[str] = None
    hq_address_line2: Optional[str] = None
    hq_city: Optional[str] = None
    hq_country: Optional[str] = None
    hq_full_address: Optional[str] = None
    hq_postalcode: Optional[str] = None
    hq_region: Optional[str] = None
    
    # Complex fields
    funding_info: Optional[FundingInfo] = None
    industries: List[str] = Field(default_factory=list)
    locations: List[CompanyLocation] = Field(default_factory=list)
    affiliated_companies: List[AffiliatedCompany] = Field(default_factory=list)
    
    @validator('year_founded', pre=True)
    def handle_empty_year_founded(cls, v):
        """Handle empty string year_founded"""
        if v == "":
            return None
        if isinstance(v, str) and v.isdigit():
            return int(v)
        return v
    
    @validator('funding_info', pre=True)
    def handle_funding_info(cls, v):
        """Handle funding info validation"""
        if isinstance(v, dict) and v:
            return FundingInfo(**v)
        return None


# Workflow response models
class ActionResult(BaseModel):
    """Individual action result within workflow"""
    name: str
    status: str
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class WorkflowRun(BaseModel):
    """Workflow run information"""
    status: str
    createdAt: str
    finishedAt: Optional[str] = None
    inputFieldValues: Dict[str, Any]
    actionResults: List[ActionResult]


class CassidyWorkflowResponse(BaseModel):
    """Top-level Cassidy workflow response"""
    message: str
    description: str
    workflowRun: WorkflowRun
