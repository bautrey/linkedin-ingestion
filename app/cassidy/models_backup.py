"""
Pydantic models for Cassidy LinkedIn workflow responses

Based on analysis of Cassidy blueprint and ronlinkedin_pretty.json data structure
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


# Base Cassidy Workflow Response Models

class WorkflowResult(BaseModel):
    """Base workflow result from Cassidy API"""
    workflow_run_id: str = Field(..., description="Unique workflow execution ID")
    status: WorkflowStatus = Field(..., description="Workflow execution status")
    created_at: datetime = Field(..., description="Workflow creation timestamp")
    completed_at: Optional[datetime] = Field(None, description="Workflow completion timestamp")
    execution_time_ms: Optional[int] = Field(None, description="Total execution time")
    error_message: Optional[str] = Field(None, description="Error message if failed")


class ActionResult(BaseModel):
    """Individual action result within workflow"""
    action_id: str = Field(..., description="Action identifier")
    output: Dict[str, Any] = Field(..., description="Action output data")
    status: str = Field(..., description="Action status")
    execution_time_ms: Optional[int] = Field(None, description="Action execution time")


class CassidyWorkflowResponse(BaseModel):
    """Top-level Cassidy workflow response"""
    workflow_run: Dict[str, Any] = Field(..., description="Workflow run metadata")
    action_results: List[ActionResult] = Field(..., description="Results from each action")


# LinkedIn Profile Models

class CompanyInfo(BaseModel):
    """Basic company information from profile"""
    name: str = Field(..., description="Company name")
    company_id: Optional[str] = Field(None, description="LinkedIn company ID")
    title: str = Field(..., description="Job title at company")
    location: Optional[str] = Field(None, description="Job location")


class ExperienceEntry(BaseModel):
    """Work experience entry"""
    title: str = Field(..., description="Job title")
    company: str = Field(..., description="Company name")
    company_id: Optional[str] = Field(None, description="LinkedIn company ID")
    url: Optional[HttpUrl] = Field(None, description="Company LinkedIn URL")
    company_linkedin_url: Optional[str] = Field(None, description="Company LinkedIn URL as string")
    location: Optional[str] = Field(None, description="Job location")
    start_date: Optional[str] = Field(None, description="Start date (YYYY or YYYY-MM format)")
    end_date: Optional[str] = Field(None, description="End date (YYYY or YYYY-MM format, 'Present' for current)")
    description: Optional[str] = Field(None, description="Job description")
    description_html: Optional[str] = Field(None, description="Job description with HTML formatting")
    company_logo_url: Optional[HttpUrl] = Field(None, description="Company logo URL")
    
    @validator('company_linkedin_url', pre=True)
    def extract_company_url(cls, v, values):
        """Extract company LinkedIn URL for company workflow"""
        if v:
            return v
        if 'url' in values and values['url']:
            return str(values['url'])
        return None


class EducationEntry(BaseModel):
    """Education entry"""
    title: str = Field(..., description="Institution name")
    degree: Optional[str] = Field(None, description="Degree type")
    field: Optional[str] = Field(None, description="Field of study")
    url: Optional[HttpUrl] = Field(None, description="Institution LinkedIn URL")
    description: Optional[str] = Field(None, description="Education description")
    description_html: Optional[str] = Field(None, description="Education description with HTML")
    institute_logo_url: Optional[HttpUrl] = Field(None, description="Institution logo URL")
    start_date: Optional[str] = Field(None, description="Start year")
    end_date: Optional[str] = Field(None, description="End year")


class CertificationEntry(BaseModel):
    """Professional certification"""
    title: str = Field(..., description="Certification name")
    subtitle: Optional[str] = Field(None, description="Issuing organization")
    credential_id: Optional[str] = Field(None, description="Credential ID")
    credential_url: Optional[HttpUrl] = Field(None, description="Credential verification URL")
    issue_date: Optional[str] = Field(None, description="Issue date")
    expiry_date: Optional[str] = Field(None, description="Expiry date")


class PersonProfile(BaseModel):
    """Simplified person profile for people_also_viewed"""
    name: str = Field(..., description="Person name")
    profile_link: HttpUrl = Field(..., description="LinkedIn profile URL")
    about: Optional[str] = Field(None, description="Brief description")
    location: Optional[str] = Field(None, description="Geographic location")


class LinkedInProfile(BaseModel):
    """LinkedIn profile from Cassidy workflow - matches exact Cassidy response structure"""
    
    # Required fields based on Cassidy data structure
    id: str = Field(..., description="LinkedIn profile ID")
    name: str = Field(..., description="Full name")
    url: HttpUrl = Field(..., description="LinkedIn profile URL")
    
    # Core profile information (from Cassidy data)
    city: Optional[str] = Field(None, description="City location")
    country_code: Optional[str] = Field(None, description="Country code (ISO)")
    position: Optional[str] = Field(None, description="Current position/headline")
    about: Optional[str] = Field(None, description="About section content")
    
    # Current company (structured exactly as Cassidy returns)
    current_company: Optional[CompanyInfo] = Field(None, description="Current company information")
    
    # Experience, Education, Certifications (lists from Cassidy)
    experience: List[ExperienceEntry] = Field(default=[], description="Work experience entries")
    education: List[EducationEntry] = Field(default=[], description="Education entries")
    certifications: List[CertificationEntry] = Field(default=[], description="Professional certifications")
    
    # Social metrics (as integers from Cassidy)
    followers: Optional[int] = Field(None, description="Number of followers")
    connections: Optional[int] = Field(None, description="Number of connections")
    
    # Timestamp (from Cassidy)
    timestamp: Optional[datetime] = Field(None, description="Data extraction timestamp")
    
    @validator('timestamp', pre=True)
    def parse_timestamp(cls, v):
        """Parse timestamp from various formats"""
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError:
                return None
        return v


# Company Profile Models

class FundingInfo(BaseModel):
    """Company funding information"""
    crunchbase_url: Optional[str] = Field(None, description="Crunchbase profile URL")
    num_funding_rounds: Optional[str] = Field(None, description="Number of funding rounds")
    last_funding_round_type: Optional[str] = Field(None, description="Type of last funding round")
    last_funding_round_year: Optional[str] = Field(None, description="Year of last funding")
    last_funding_round_month: Optional[str] = Field(None, description="Month of last funding")
    last_funding_round_amount: Optional[str] = Field(None, description="Amount of last funding")
    last_funding_round_currency: Optional[str] = Field(None, description="Currency of last funding")


class LocationInfo(BaseModel):
    """Company location information"""
    city: Optional[str] = Field(None, description="City")
    country: Optional[str] = Field(None, description="Country")
    region: Optional[str] = Field(None, description="State/region")
    full_address: Optional[str] = Field(None, description="Full address")
    line1: Optional[str] = Field(None, description="Address line 1")
    line2: Optional[str] = Field(None, description="Address line 2")
    zipcode: Optional[str] = Field(None, description="Postal code")
    is_headquarter: Optional[bool] = Field(None, description="Whether this is headquarters")


class CompanyProfile(BaseModel):
    """Company profile from Cassidy workflow - matches exact Cassidy response structure"""
    
    # Core fields from Cassidy company data
    company_id: Optional[str] = Field(None, description="LinkedIn company ID")
    company_name: str = Field(..., description="Company name")
    description: Optional[str] = Field(None, description="Company description")
    website: Optional[str] = Field(None, description="Company website")
    linkedin_url: Optional[HttpUrl] = Field(None, description="Company LinkedIn URL")
    
    # Company metrics
    employee_count: Optional[int] = Field(None, description="Number of employees")
    employee_range: Optional[str] = Field(None, description="Employee count range")
    year_founded: Optional[int] = Field(None, description="Year company was founded")
    
    # Industry classification
    industries: List[str] = Field(default=[], description="Industry categories")
    
    # Location information (headquarters)
    hq_city: Optional[str] = Field(None, description="Headquarters city")
    hq_region: Optional[str] = Field(None, description="Headquarters region")
    hq_country: Optional[str] = Field(None, description="Headquarters country")
    
    # Detailed locations
    locations: List[LocationInfo] = Field(default=[], description="Company locations")
    
    # Funding information
    funding_info: Optional[FundingInfo] = Field(None, description="Funding information")


# Request/Response Models for API Endpoints

class ProfileIngestionRequest(BaseModel):
    """Request to ingest a LinkedIn profile"""
    linkedin_url: HttpUrl = Field(..., description="LinkedIn profile URL to ingest")
    include_companies: bool = Field(True, description="Whether to fetch company data for experiences")
    force_refresh: bool = Field(False, description="Force refresh even if profile exists")


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


# Error Response Models

class ErrorDetail(BaseModel):
    """Detailed error information"""
    type: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    field: Optional[str] = Field(None, description="Field that caused error")
    code: Optional[str] = Field(None, description="Error code")


class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str = Field(..., description="Error category")
    message: str = Field(..., description="Human-readable error message")
    details: List[ErrorDetail] = Field(default=[], description="Detailed error information")
    request_id: Optional[str] = Field(None, description="Request identifier for tracking")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
