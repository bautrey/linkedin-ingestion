"""
Canonical Pydantic V2 models for LinkedIn Company data.

These models serve as the internal, stable data contract for the application,
decoupling it from the specific structure of any single data provider (e.g., Cassidy).
"""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, HttpUrl, ConfigDict
from datetime import datetime, timezone

# --- Nested Company Models ---

class CanonicalFundingInfo(BaseModel):
    """
    A canonical representation of a company's funding round.
    """
    model_config = ConfigDict(extra='allow')

    crunchbase_url: Optional[HttpUrl] = Field(None, description="URL to the company's Crunchbase profile.")
    last_funding_round_type: Optional[str] = Field(None, description="The type of the last funding round, e.g., 'Series A'.")
    last_funding_round_amount: Optional[str] = Field(None, description="The amount of the last funding round as a display string.")
    last_funding_round_currency: Optional[str] = Field(None, description="The currency of the last funding round.")
    last_funding_round_year: Optional[int] = Field(None, description="The year of the last funding round.")
    last_funding_round_month: Optional[int] = Field(None, description="The month of the last funding round.")
    last_funding_round_investor_count: Optional[int] = Field(None, description="Number of investors in the last funding round.")


class CanonicalCompanyLocation(BaseModel):
    """
    A canonical representation of a company's office location.
    """
    model_config = ConfigDict(extra='allow')

    is_headquarter: Optional[bool] = Field(None, description="Indicates if this location is the company headquarters.")
    full_address: Optional[str] = Field(None, description="The full, combined address string.")
    line1: Optional[str] = Field(None, description="Address line 1.")
    line2: Optional[str] = Field(None, description="Address line 2.")
    city: Optional[str] = Field(None, description="The city of the location.")
    region: Optional[str] = Field(None, description="The state, province, or region.")
    country: Optional[str] = Field(None, description="The country of the location.")
    zipcode: Optional[str] = Field(None, description="The postal or ZIP code.")


class CanonicalAffiliatedCompany(BaseModel):
    """
    A canonical representation of an affiliated company (e.g., subsidiary or parent).
    """
    model_config = ConfigDict(extra='allow')

    name: Optional[str] = Field(None, description="The name of the affiliated company.")
    linkedin_url: Optional[HttpUrl] = Field(None, description="The LinkedIn URL of the affiliated company.")
    company_id: Optional[str] = Field(None, description="The LinkedIn ID of the affiliated company.")


# --- Main Company Model ---

class CanonicalCompany(BaseModel):
    """
    A canonical, Pydantic V2-compliant model for a LinkedIn company profile.
    This model captures all known fields from various data providers and normalizes them.
    """
    model_config = ConfigDict(
        extra='allow',
        populate_by_name=True,
    )

    # --- Core Identity ---
    company_id: Optional[str] = Field(None, description="The unique LinkedIn company ID.")
    company_name: str = Field(..., description="The name of the company.")
    linkedin_url: Optional[HttpUrl] = Field(None, description="The full URL of the LinkedIn company page.")
    
    # --- Company Details ---
    tagline: Optional[str] = Field(None, description="The company's tagline or short slogan.")
    description: Optional[str] = Field(None, description="The full description of the company.")
    website: Optional[HttpUrl] = Field(None, description="The company's official website.")
    domain: Optional[str] = Field(None, description="The company's website domain.")
    logo_url: Optional[HttpUrl] = Field(None, description="A URL for the company's logo.")
    year_founded: Optional[int] = Field(None, description="The year the company was founded.")
    
    # --- Classification ---
    industries: List[str] = Field(default_factory=list, description="A list of industries the company operates in.")
    specialties: Optional[str] = Field(None, description="A comma-separated string of the company's specialties.") # Source is string
    
    # --- Size & Metrics ---
    employee_count: Optional[int] = Field(None, description="The total number of employees.")
    employee_range: Optional[str] = Field(None, description="A display string for the employee count range, e.g., '501-1000'.")
    follower_count: Optional[int] = Field(None, description="The number of followers the company has on LinkedIn.")
    
    # --- HQ Location ---
    hq_address_line1: Optional[str] = Field(None, description="Headquarters address line 1.")
    hq_address_line2: Optional[str] = Field(None, description="Headquarters address line 2.")
    hq_city: Optional[str] = Field(None, description="Headquarters city.")
    hq_region: Optional[str] = Field(None, description="Headquarters state or region.")
    hq_country: Optional[str] = Field(None, description="Headquarters country.")
    hq_postalcode: Optional[str] = Field(None, description="Headquarters postal code.")
    hq_full_address: Optional[str] = Field(None, description="Full, combined headquarters address.")

    # --- Contact Information ---
    email: Optional[str] = Field(None, description="The company's contact email address.")
    phone: Optional[str] = Field(None, description="The company's contact phone number.")

    # --- Complex Nested Data ---
    funding_info: Optional[CanonicalFundingInfo] = Field(None, description="Information about the company's funding rounds.")
    locations: List[CanonicalCompanyLocation] = Field(default_factory=list, description="A list of the company's office locations.")
    affiliated_companies: List[CanonicalAffiliatedCompany] = Field(default_factory=list, description="A list of affiliated companies.")

    # --- Timestamps & Metadata ---
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="The timestamp when the data was processed.")
    raw_data: Optional[Dict[str, Any]] = Field(None, description="The complete, unmodified raw data from the source provider.")
