"""
Pydantic models for Cassidy LinkedIn workflow responses

Fixed models based on actual Cassidy API response structure observed in debug output
"""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, HttpUrl, field_validator, ConfigDict
from datetime import datetime
from enum import Enum


def safe_int_conversion(value: Any) -> Optional[int]:
    """Safely convert various types to int, handling empty strings and nulls"""
    if value is None or value == "" or value == {}:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None


def safe_str_conversion(value: Any) -> Optional[str]:
    """Safely convert various types to string, handling nulls and empties"""
    if value is None or (isinstance(value, str) and value.strip() == ""):
        return None
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, str):
        return value.strip() or None
    return str(value) if value else None


def safe_list_conversion(value: Any, expected_type: type = dict) -> List[Any]:
    """Safely convert various types to list, handling nulls and single items"""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, expected_type):
        return [value]
    return []


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
    
    @field_validator('end_year', 'start_year', mode='before')
    @classmethod
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
    date_range: Optional[str] = None
    description: Optional[str] = None
    duration: Optional[str] = None  # NEW: e.g., "11 yrs 6 mos"
    end_month: Optional[str] = None
    end_year: Optional[int] = None
    is_current: Optional[bool] = None  # RENAMED from current_job
    job_type: Optional[str] = None  # NEW: job type classification
    location: Optional[str] = None
    skills: Optional[str] = None  # NEW: skills associated with role
    start_month: Optional[int] = None  # Changed: can be int or str
    start_year: Optional[int] = None
    title: Optional[str] = None  # RENAMED from job_title
    
    @field_validator('end_year', 'start_year', mode='before')
    @classmethod
    def handle_empty_year(cls, v):
        """Handle empty string years"""
        if v == "":
            return None
        if isinstance(v, str) and v.isdigit():
            return int(v)
        return v
    
    @field_validator('start_month', 'end_month', mode='before')
    @classmethod
    def handle_month(cls, v):
        """Handle month fields that might be int or string"""
        if v == "":
            return None
        if isinstance(v, int):
            return v  # Keep as int for start_month since API sends int
        if isinstance(v, str) and v.isdigit():
            return int(v)
        return v
    
    @field_validator('company', 'company_id', 'company_linkedin_url', 'company_logo_url',
                     'date_range', 'description', 'duration', 'end_month', 'job_type',
                     'location', 'skills', 'title', mode='before')
    @classmethod
    def handle_flexible_strings(cls, v):
        """Handle string fields that might be null, empty, or other types"""
        return safe_str_conversion(v)
    
    # Backward compatibility properties
    @property
    def job_title(self) -> Optional[str]:
        """Alias for title for backward compatibility"""
        return self.title
    
    @property
    def current_job(self) -> Optional[bool]:
        """Alias for is_current for backward compatibility"""
        return self.is_current


# Current Company Info
class CurrentCompanyInfo(BaseModel):
    """Current company information"""
    name: Optional[str] = None
    position: Optional[str] = None
    linkedin_url: Optional[str] = None


class LinkedInProfile(BaseModel):
    """LinkedIn profile matching actual Cassidy API response structure"""
    
    model_config = ConfigDict(extra="allow")  # Allow extra fields like _certifications
    
    # Core fields - now optional since API format has changed
    profile_id: Optional[str] = None
    full_name: Optional[str] = None
    linkedin_url: Optional[str] = None
    
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
    
    @field_validator('company_year_founded', mode='before')
    @classmethod
    def handle_company_year_founded(cls, v):
        """Handle company_year_founded that might come as int or string"""
        if v is None or v == "":
            return None
        if isinstance(v, int):
            return str(v)
        return v
    
    # Social metrics - flexible type handling
    follower_count: Optional[Union[int, str]] = None
    connection_count: Optional[Union[int, str]] = None
    
    # Current job details - flexible type handling
    current_company_join_month: Optional[Union[int, str]] = None
    current_company_join_year: Optional[Union[int, str]] = None
    current_job_duration: Optional[str] = None
    
    # Flexible validators for common data type issues
    @field_validator('follower_count', 'connection_count', 'current_company_join_month', 
              'current_company_join_year', 'company_employee_count', mode='before')
    @classmethod
    def handle_flexible_ints(cls, v):
        """Handle int fields that might come as strings or be empty"""
        return safe_int_conversion(v)
    
    @field_validator('about', 'city', 'country', 'headline', 'location', 'state', 
              'company', 'job_title', 'company_description', 'company_domain',
              'company_employee_range', 'company_industry', 'company_linkedin_url',
              'company_logo_url', 'company_website', 'email', 'phone',
              'first_name', 'last_name', 'profile_image_url', 'public_id',
              'hq_city', 'hq_country', 'hq_region', 'school', mode='before')
    @classmethod
    def handle_flexible_strings(cls, v):
        """Handle string fields that might be null, empty, or other types"""
        return safe_str_conversion(v)
    
    @field_validator('educations', 'experiences', mode='before')
    @classmethod
    def handle_flexible_arrays(cls, v):
        """Handle array fields that might be null or single items"""
        return safe_list_conversion(v, dict)
    
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
    
    # Arrays - more flexible handling
    educations: List[EducationEntry] = Field(default_factory=list)
    experiences: List[ExperienceEntry] = Field(default_factory=list)
    languages: List[Union[str, Dict[str, Any]]] = Field(default_factory=list)
    
    @field_validator('languages', mode='before')
    @classmethod
    def handle_languages_field(cls, v):
        """Handle languages that could be strings, dicts, or mixed formats"""
        if v is None:
            return []
        if isinstance(v, list):
            return v  # Accept any list format
        if isinstance(v, (str, dict)):
            return [v]  # Convert single item to list
        return []
    
    # Timestamp
    timestamp: Optional[datetime] = None
    
    # Convenience properties to maintain compatibility with existing code
    @property
    def id(self) -> Optional[str]:
        """Alias for profile_id for backward compatibility"""
        return self.profile_id
    
    @property
    def name(self) -> Optional[str]:
        """Alias for full_name for backward compatibility"""
        return self.full_name
        
    @property
    def url(self) -> Optional[str]:
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
        """Return certifications from stored data or empty list"""
        return getattr(self, '_certifications', [])
    
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
    
    model_config = ConfigDict(extra="allow")  # Allow extra fields like raw_data
    
    # Core fields from actual API
    company_id: str = Field(default="unknown", description="LinkedIn company ID")
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
    
    @field_validator('year_founded', mode='before')
    @classmethod
    def handle_empty_year_founded(cls, v):
        """Handle year_founded - convert int to string, handle empty strings"""
        if v == "" or v is None:
            return None
        if isinstance(v, int):
            return str(v)
        if isinstance(v, str) and v.isdigit():
            return v  # Keep as string
        return v
    
    @field_validator('funding_info', mode='before')
    @classmethod
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


# Request/Response Models for API Endpoints

class ProfileIngestionRequest(BaseModel):
    """Request to ingest a LinkedIn profile"""
    linkedin_url: HttpUrl = Field(..., description="LinkedIn profile URL to ingest")
    include_companies: bool = Field(True, description="Whether to fetch company data for experiences")
    force_refresh: bool = Field(False, description="Force refresh even if profile exists")
    
    @field_validator('linkedin_url', mode='before')
    @classmethod
    def normalize_linkedin_url(cls, v):
        """Normalize LinkedIn URLs by adding https:// if missing protocol"""
        if isinstance(v, str):
            # Remove trailing whitespace
            v = v.strip()
            
            # If URL doesn't start with http:// or https://, add https://
            if not v.startswith(('http://', 'https://')):
                # Handle common cases like "www.linkedin.com" or "linkedin.com"
                if v.startswith('www.') or 'linkedin.com' in v:
                    v = f"https://{v}"
        return v


class CompanyIngestionRequest(BaseModel):
    """Request to ingest a company profile"""
    linkedin_url: HttpUrl = Field(..., description="LinkedIn company URL to ingest")
    force_refresh: bool = Field(False, description="Force refresh even if company exists")


class IngestionStatus(BaseModel):
    """Status of an ingestion process"""
    request_id: str = Field(..., description="Unique request identifier")
    status: WorkflowStatus = Field(..., description="Current status")
    profile_url: HttpUrl = Field(..., description="LinkedIn URL being processed")
    started_at: datetime = Field(..., description="Process start time")
    completed_at: Optional[datetime] = Field(None, description="Process completion time")
    progress: Dict[str, Any] = Field(default={}, description="Progress details")
    error_message: Optional[str] = Field(None, description="Error message if failed")


class IngestionResponse(BaseModel):
    """Response from profile/company ingestion"""
    request_id: str = Field(..., description="Unique request identifier")
    status: WorkflowStatus = Field(..., description="Initial status")
    message: str = Field(..., description="Response message")
    estimated_completion_time: Optional[datetime] = Field(None, description="Estimated completion time")
    status_url: Optional[str] = Field(None, description="URL to check status")


class CassidyWorkflowResponse(BaseModel):
    """Top-level Cassidy workflow response"""
    message: str
    description: str
    workflowRun: WorkflowRun
