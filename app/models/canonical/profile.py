"""
Canonical Pydantic V2 models for LinkedIn Profile data.

These models serve as the internal, stable data contract for the application,
decoupling it from the specific structure of any single data provider (e.g., Cassidy).
"""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, HttpUrl, ConfigDict
from datetime import datetime, timezone
from enum import Enum

# --- Enums and Helper Models ---

class CanonicalWorkflowStatus(str, Enum):
    """Canonical workflow execution status."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"

class RoleType(str, Enum):
    """Supported role types for profile scoring."""
    CIO = "CIO"
    CTO = "CTO"
    CISO = "CISO"

# --- Nested Profile Models ---

class CanonicalEducationEntry(BaseModel):
    """
    A canonical representation of an education entry on a LinkedIn profile.
    """
    model_config = ConfigDict(extra='allow')

    school: Optional[str] = Field(None, description="The name of the educational institution.")
    degree: Optional[str] = Field(None, description="The degree obtained, e.g., 'Bachelor of Science'.")
    field_of_study: Optional[str] = Field(None, description="The field of study, e.g., 'Computer Science'.")
    start_year: Optional[int] = Field(None, description="The year the education started.")
    end_year: Optional[int] = Field(None, description="The year the education ended.")
    date_range: Optional[str] = Field(None, description="A display string for the education duration, e.g., '2018 - 2022'.")
    activities: Optional[str] = Field(None, description="Associated activities or societies.")
    school_linkedin_url: Optional[HttpUrl] = Field(None, description="The LinkedIn URL of the school.")
    school_id: Optional[str] = Field(None, description="The LinkedIn ID of the school.")

class CanonicalExperienceEntry(BaseModel):
    """
    A canonical representation of a work experience entry on a LinkedIn profile.
    """
    model_config = ConfigDict(extra='allow')

    title: Optional[str] = Field(None, description="The job title for the position.")
    company: Optional[str] = Field(None, description="The name of the company.")
    company_linkedin_url: Optional[HttpUrl] = Field(None, description="The LinkedIn URL of the company.")
    company_logo_url: Optional[HttpUrl] = Field(None, description="A URL for the company's logo.")
    location: Optional[str] = Field(None, description="The location of the job.")
    start_year: Optional[int] = Field(None, description="The year the position started.")
    start_month: Optional[int] = Field(None, description="The month the position started.")
    end_year: Optional[int] = Field(None, description="The year the position ended.")
    end_month: Optional[int] = Field(None, description="The month the position ended.")
    date_range: Optional[str] = Field(None, description="A display string for the employment duration, e.g., 'Jan 2020 - Present'.")
    duration: Optional[str] = Field(None, description="A display string for the total duration, e.g., '2 yrs 5 mos'.")
    description: Optional[str] = Field(None, description="The description of the role and responsibilities.")
    is_current: Optional[bool] = Field(None, description="Indicates if this is the user's current position.")
    job_type: Optional[str] = Field(None, description="The type of employment, e.g., 'Full-time'.")
    skills: Optional[str] = Field(None, description="A comma-separated string of skills associated with the role.") # Source is string
    company_id: Optional[str] = Field(None, description="The LinkedIn ID of the company.")

# --- Main Profile Model ---

class CanonicalProfile(BaseModel):
    """
    A canonical, Pydantic V2-compliant model for a LinkedIn user profile.
    This model captures all known fields from various data providers and normalizes them.
    """
    model_config = ConfigDict(
        extra='allow',  # Allow unexpected fields to be stored
        populate_by_name=True,  # Allows using aliases for field names
    )

    # --- Core Identity ---
    profile_id: Optional[str] = Field(None, description="The unique LinkedIn profile ID.")
    public_id: Optional[str] = Field(None, description="The public vanity URL identifier, e.g., 'john-doe-123'.")
    linkedin_url: Optional[HttpUrl] = Field(None, description="The full URL of the LinkedIn profile.")
    urn: Optional[str] = Field(None, description="The unique LinkedIn URN for the profile.")
    
    # --- Personal Information ---
    first_name: Optional[str] = Field(None, description="The user's first name.")
    last_name: Optional[str] = Field(None, description="The user's last name.")
    full_name: Optional[str] = Field(None, description="The user's full name.")
    headline: Optional[str] = Field(None, description="The user's professional headline below their name.")
    about: Optional[str] = Field(None, description="The user's 'About' section summary.")
    profile_image_url: Optional[HttpUrl] = Field(None, description="A URL for the user's profile picture.")

    # --- Location ---
    city: Optional[str] = Field(None, description="The user's city.")
    state: Optional[str] = Field(None, description="The user's state or region.")
    country: Optional[str] = Field(None, description="The user's country.")
    location: Optional[str] = Field(None, description="A combined, display-friendly location string.")

    # --- Contact Information ---
    email: Optional[str] = Field(None, description="The user's email address (if public).")
    phone: Optional[str] = Field(None, description="The user's phone number (if public).")

    # --- Professional Details ---
    experiences: List[CanonicalExperienceEntry] = Field(default_factory=list, description="A list of the user's work experiences.")
    educations: List[CanonicalEducationEntry] = Field(default_factory=list, description="A list of the user's education history.")
    
    # --- Skills & Languages ---
    languages: List[Union[str, Dict[str, Any]]] = Field(default_factory=list, description="A list of languages the user knows. Can be simple strings or complex objects.")
    
    # --- Social Metrics ---
    follower_count: Optional[int] = Field(None, description="The number of followers the user has.")
    connection_count: Optional[int] = Field(None, description="The number of connections the user has.")

    # --- Current Job Details ---
    company: Optional[str] = Field(None, description="Name of the current company.")
    job_title: Optional[str] = Field(None, description="Title of the current job.")
    company_description: Optional[str] = Field(None, description="Description of the current company.")
    company_domain: Optional[str] = Field(None, description="Domain of the current company's website.")
    company_linkedin_url: Optional[HttpUrl] = Field(None, description="LinkedIn URL of the current company.")
    company_logo_url: Optional[HttpUrl] = Field(None, description="Logo URL of the current company.")
    company_website: Optional[HttpUrl] = Field(None, description="Website of the current company.")
    company_employee_count: Optional[int] = Field(None, description="Employee count of the current company.")
    company_employee_range: Optional[str] = Field(None, description="Employee range of the current company, e.g., '501-1000'.")
    company_industry: Optional[str] = Field(None, description="Industry of the current company.")
    company_year_founded: Optional[str] = Field(None, description="Year the current company was founded.")
    current_company_join_month: Optional[int] = Field(None, description="Month when the user joined their current company.")
    current_company_join_year: Optional[int] = Field(None, description="Year when the user joined their current company.")
    current_job_duration: Optional[str] = Field(None, description="Duration string for current job, e.g., '2 yrs 3 mos'.")
    
    # --- Additional LinkedIn-specific Fields ---
    start_month: Optional[str] = Field(None, description="Start month from Cassidy API.")
    end_month: Optional[str] = Field(None, description="End month from Cassidy API.")
    
    # --- HQ/Company Location ---
    hq_city: Optional[str] = Field(None, description="Headquarters city of current company.")
    hq_country: Optional[str] = Field(None, description="Headquarters country of current company.")
    hq_region: Optional[str] = Field(None, description="Headquarters region of current company.")
    
    # --- Education Info (single school reference) ---
    school: Optional[str] = Field(None, description="Name of a school (legacy field from Cassidy).")
    
    # --- Profile Flags ---
    is_premium: Optional[bool] = Field(None, description="Flag indicating if the user has a LinkedIn Premium account.")
    is_creator: Optional[bool] = Field(None, description="Flag indicating if the user is in LinkedIn's creator mode.")
    is_influencer: Optional[bool] = Field(None, description="Flag indicating if the user is classified as an influencer.")
    is_verified: Optional[bool] = Field(None, description="Flag indicating if the user's profile is verified.")
    
    # --- Role Information ---
    suggested_role: Optional[RoleType] = Field(None, description="The suggested role for this profile: CIO, CTO, or CISO for role-specific scoring.")
    
    # --- Timestamps & Metadata ---
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="The timestamp when the data was processed.")
    raw_data: Optional[Dict[str, Any]] = Field(None, description="The complete, unmodified raw data from the source provider.")
