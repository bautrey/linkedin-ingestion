"""
Canonical Pydantic V2 models for LinkedIn Company data.

These models serve as the internal, stable data contract for the application,
decoupling it from the specific structure of any single data provider (e.g., Cassidy).
"""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, HttpUrl, ConfigDict, field_validator, computed_field, model_validator
from datetime import datetime, timezone
import re
from urllib.parse import urlparse

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
    
    Features:
    - Field validators for data cleaning and validation
    - Computed fields for derived properties (age, size category, etc.)
    - Utility methods for common operations (startup detection, location search)
    - Automatic domain extraction from website URLs
    - Industry deduplication and specialties parsing
    - Comprehensive address handling with HQ synthesis
    
    Examples:
        Basic usage:
        >>> company = CanonicalCompany(company_name="Test Corp")
        >>> print(company.display_name)
        Test Corp
        
        With website (auto-extracts domain):
        >>> company = CanonicalCompany(
        ...     company_name="Test Corp",
        ...     website="https://www.test.com"
        ... )
        >>> print(company.domain)
        test.com
        
        Startup detection:
        >>> company = CanonicalCompany(
        ...     company_name="Young Startup",
        ...     employee_count=15,
        ...     year_founded=2022,
        ...     funding_info={"last_funding_round_type": "Seed"}
        ... )
        >>> print(company.is_startup())
        True
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
    
    # --- Field Validators ---
    
    @field_validator('company_name')
    @classmethod
    def validate_company_name(cls, v: str) -> str:
        """Validate and clean company name."""
        if not v or not v.strip():
            raise ValueError('Company name cannot be empty')
        # Clean up common issues: multiple spaces, leading/trailing whitespace
        cleaned = ' '.join(v.strip().split())
        return cleaned
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        """Basic email validation."""
        if v is None:
            return v
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', v):
            raise ValueError('Invalid email format')
        return v.lower().strip()
    
    @field_validator('year_founded')
    @classmethod
    def validate_year_founded(cls, v: Optional[int]) -> Optional[int]:
        """Validate founding year is reasonable."""
        if v is None:
            return v
        current_year = datetime.now().year
        if v < 1600 or v > current_year + 1:  # Allow for companies founded "next year"
            raise ValueError(f'Year founded must be between 1600 and {current_year + 1}')
        return v
    
    @field_validator('employee_count')
    @classmethod
    def validate_employee_count(cls, v: Optional[int]) -> Optional[int]:
        """Validate employee count is non-negative."""
        if v is None:
            return v
        if v < 0:
            raise ValueError('Employee count cannot be negative')
        return v
    
    @field_validator('follower_count')
    @classmethod
    def validate_follower_count(cls, v: Optional[int]) -> Optional[int]:
        """Validate follower count is non-negative."""
        if v is None:
            return v
        if v < 0:
            raise ValueError('Follower count cannot be negative')
        return v
    
    @field_validator('industries')
    @classmethod
    def validate_industries(cls, v: List[str]) -> List[str]:
        """Clean and deduplicate industries list."""
        if not v:
            return v
        # Clean each industry: strip whitespace, remove empty strings, deduplicate
        cleaned = [industry.strip() for industry in v if industry and industry.strip()]
        return list(dict.fromkeys(cleaned))  # Preserve order while deduplicating
    
    @model_validator(mode='after')
    def validate_domain_website_consistency(self):
        """Ensure domain is consistent with website if both are provided."""
        if self.website and self.domain:
            parsed = urlparse(str(self.website))
            website_domain = parsed.netloc.lower()
            # Remove 'www.' prefix for comparison
            if website_domain.startswith('www.'):
                website_domain = website_domain[4:]
            if self.domain.lower().replace('www.', '') != website_domain:
                # Don't raise error, just log a warning in real usage
                # For now, prefer the website domain
                parsed_url = urlparse(str(self.website))
                self.domain = parsed_url.netloc.lower().replace('www.', '') if parsed_url.netloc else self.domain
        elif self.website and not self.domain:
            # Auto-extract domain from website
            parsed = urlparse(str(self.website))
            if parsed.netloc:
                self.domain = parsed.netloc.lower().replace('www.', '')
        return self
    
    # --- Computed Fields ---
    
    @computed_field
    @property
    def display_name(self) -> str:
        """A clean display name for the company."""
        return self.company_name
    
    @computed_field
    @property
    def company_age(self) -> Optional[int]:
        """Calculate company age in years if year_founded is available."""
        if self.year_founded is None:
            return None
        return datetime.now().year - self.year_founded
    
    @computed_field
    @property
    def size_category(self) -> str:
        """Categorize company by employee count."""
        if self.employee_count is None:
            return "Unknown"
        elif self.employee_count < 10:
            return "Startup"
        elif self.employee_count < 50:
            return "Small"
        elif self.employee_count < 200:
            return "Medium"
        elif self.employee_count < 1000:
            return "Large"
        else:
            return "Enterprise"
    
    @computed_field
    @property
    def headquarters(self) -> Optional[CanonicalCompanyLocation]:
        """Get the headquarters location from the locations list."""
        for location in self.locations:
            if location.is_headquarter:
                return location
        # If no HQ is marked but we have HQ fields, create a synthetic location
        if any([self.hq_city, self.hq_region, self.hq_country, self.hq_full_address]):
            return CanonicalCompanyLocation(
                is_headquarter=True,
                full_address=self.hq_full_address,
                line1=self.hq_address_line1,
                line2=self.hq_address_line2,
                city=self.hq_city,
                region=self.hq_region,
                country=self.hq_country,
                zipcode=self.hq_postalcode
            )
        return None
    
    @computed_field
    @property
    def specialties_list(self) -> List[str]:
        """Convert comma-separated specialties string to a clean list."""
        if not self.specialties:
            return []
        # Split by comma and clean each item
        items = [item.strip() for item in self.specialties.split(',') if item.strip()]
        return items
    
    # --- Utility Methods ---
    
    def to_summary_dict(self) -> Dict[str, Any]:
        """Return a summary dictionary with key company information."""
        return {
            "company_id": self.company_id,
            "company_name": self.company_name,
            "website": str(self.website) if self.website else None,
            "domain": self.domain,
            "employee_count": self.employee_count,
            "size_category": self.size_category,
            "industries": self.industries,
            "year_founded": self.year_founded,
            "company_age": self.company_age,
            "headquarters_city": self.hq_city,
            "headquarters_country": self.hq_country,
            "linkedin_url": str(self.linkedin_url) if self.linkedin_url else None,
        }
    
    def get_primary_industry(self) -> Optional[str]:
        """Get the first/primary industry from the industries list."""
        return self.industries[0] if self.industries else None
    
    def has_funding_info(self) -> bool:
        """Check if the company has any funding information."""
        return self.funding_info is not None and any([
            self.funding_info.last_funding_round_type,
            self.funding_info.last_funding_round_amount,
            self.funding_info.last_funding_round_year
        ])
    
    def is_startup(self) -> bool:
        """Determine if this is likely a startup based on size, age, and funding."""
        # Small company
        if self.employee_count and self.employee_count >= 200:
            return False
        
        # Young company (founded within last 10 years)
        age = self.company_age
        if age is not None and age > 10:
            return False
        
        # Has recent funding rounds typical of startups
        if self.has_funding_info() and self.funding_info:
            funding_type = self.funding_info.last_funding_round_type
            if funding_type and any(term in funding_type.lower() for term in ['seed', 'series a', 'series b', 'angel']):
                return True
        
        # Small and young qualifies as startup
        return (self.employee_count is None or self.employee_count < 50) and (age is None or age <= 7)
    
    def get_location_by_city(self, city: str) -> Optional[CanonicalCompanyLocation]:
        """Find a location by city name."""
        city_lower = city.lower()
        for location in self.locations:
            if location.city and location.city.lower() == city_lower:
                return location
        return None
    
    def __str__(self) -> str:
        """String representation of the company."""
        parts = [self.company_name]
        if self.domain:
            parts.append(f"({self.domain})")
        if self.employee_count:
            parts.append(f"- {self.employee_count} employees")
        return " ".join(parts)
