"""
Unit tests for the canonical Pydantic V2 models.

This test suite verifies:
- Correct data type validation and coercion.
- Serialization and deserialization (round-tripping).
- Handling of optional, nullable, and edge-case field values.
- `extra='allow'` behavior for unknown fields.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from app.models.canonical import (
    CanonicalProfile, 
    CanonicalCompany,
    CanonicalFundingInfo,
    CanonicalCompanyLocation,
    CanonicalAffiliatedCompany,
    CanonicalExperienceEntry,
    CanonicalEducationEntry
)

# --- Test Data Fixtures ---

@pytest.fixture
def basic_profile_data():
    """Provides a dictionary with basic, valid data for a CanonicalProfile."""
    return {
        "full_name": "John Doe",
        "headline": "Senior Software Engineer",
        "experiences": [
            {
                "title": "Software Engineer",
                "company": "Tech Corp",
                "start_year": 2020,
            }
        ]
    }

@pytest.fixture
def full_profile_data():
    """Provides a comprehensive, valid data dictionary for a CanonicalProfile."""
    return {
        "profile_id": "12345",
        "full_name": "Jane Smith",
        "headline": "Product Manager at Innovate LLC",
        "linkedin_url": "https://www.linkedin.com/in/janesmith",
        "experiences": [
            {
                "title": "Product Manager",
                "company": "Innovate LLC",
                "start_year": 2022,
                "is_current": True,
                "unknown_field_exp": "should be allowed"
            }
        ],
        "educations": [
            {
                "school": "University of Example",
                "degree": "Master of Science",
                "field_of_study": "Human-Computer Interaction",
                "start_year": 2020,
                "end_year": 2022
            }
        ],
        "follower_count": 1500,
        "unknown_field_profile": "this should also be allowed"
    }

@pytest.fixture
def basic_company_data():
    """Provides a dictionary with basic, valid data for a CanonicalCompany."""
    return {
        "company_name": "Innovate LLC",
        "website": "https://innovatellc.com",
        "employee_count": 250
    }

@pytest.fixture
def full_company_data():
    """Provides comprehensive company data matching Cassidy output structure."""
    return {
        "company_id": "123456",
        "company_name": "PricewaterhouseCoopers",
        "linkedin_url": "https://linkedin.com/company/pwc",
        "tagline": "Building trust in society and solving important problems",
        "description": "A multinational professional services network headquartered in London, United Kingdom.",
        "website": "https://www.pwc.com",
        "domain": "pwc.com",
        "logo_url": "https://media.licdn.com/dms/image/C4D0BAQGqGtCMHfTqKA/company-logo_400_400/0",
        "year_founded": 1998,
        "industries": ["Professional Services", "Consulting", "Tax Services"],
        "specialties": "Assurance, Tax, Advisory, Consulting",
        "employee_count": 284478,
        "employee_range": "10001+",
        "follower_count": 2500000,
        # HQ Location fields
        "hq_city": "London",
        "hq_region": "England",
        "hq_country": "United Kingdom",
        "hq_address_line1": "1 Embankment Place",
        "hq_postalcode": "WC2N 6RH",
        "hq_full_address": "1 Embankment Place, London WC2N 6RH, United Kingdom",
        # Contact info
        "email": "contact@pwc.com",
        "phone": "+44 20 7583 5000",
        # Complex nested data
        "funding_info": {
            "crunchbase_url": "https://www.crunchbase.com/organization/pricewaterhousecoopers",
            "last_funding_round_type": "Private Equity",
            "last_funding_round_amount": "$50M",
            "last_funding_round_currency": "USD",
            "last_funding_round_year": 2020,
            "last_funding_round_month": 3,
            "last_funding_round_investor_count": 2
        },
        "locations": [
            {
                "is_headquarter": True,
                "full_address": "1 Embankment Place, London WC2N 6RH, UK",
                "line1": "1 Embankment Place",
                "city": "London",
                "region": "England",
                "country": "United Kingdom",
                "zipcode": "WC2N 6RH"
            },
            {
                "is_headquarter": False,
                "full_address": "300 Madison Avenue, New York, NY 10017",
                "line1": "300 Madison Avenue",
                "city": "New York",
                "region": "NY",
                "country": "United States",
                "zipcode": "10017"
            }
        ],
        "affiliated_companies": [
            {
                "name": "PwC Digital Services",
                "linkedin_url": "https://linkedin.com/company/pwc-digital",
                "company_id": "789012"
            }
        ],
        "raw_data": {"source": "cassidy", "processed_at": "2025-08-20T21:45:00Z"},
        "custom_field": "should be allowed due to extra='allow'"
    }

@pytest.fixture
def startup_company_data():
    """Company data for a startup to test different scenarios."""
    return {
        "company_name": "TechStartup Inc",
        "linkedin_url": "https://linkedin.com/company/techstartup",
        "employee_count": 45,
        "employee_range": "11-50",
        "industries": ["Technology", "Software", "Artificial Intelligence"],
        "specialties": "AI, Machine Learning, Data Analytics",
        "funding_info": {
            "last_funding_round_type": "Series A",
            "last_funding_round_amount": "$15M",
            "last_funding_round_year": 2024,
            "last_funding_round_investor_count": 3
        },
        "locations": [
            {
                "is_headquarter": True,
                "city": "San Francisco",
                "region": "CA",
                "country": "United States"
            }
        ],
        "description": "Innovative AI solutions for modern businesses."
    }

@pytest.fixture
def minimal_company_data():
    """Minimal valid company data with only required fields."""
    return {
        "company_name": "Minimal Corp"
    }

# --- CanonicalProfile Tests ---

def test_canonical_profile_creation(basic_profile_data):
    """Tests that a CanonicalProfile can be created with basic valid data."""
    profile = CanonicalProfile(**basic_profile_data)
    assert profile.full_name == "John Doe"
    assert profile.headline == "Senior Software Engineer"
    assert len(profile.experiences) == 1
    assert isinstance(profile.experiences[0], CanonicalExperienceEntry)
    assert profile.experiences[0].company == "Tech Corp"

def test_canonical_profile_full_creation(full_profile_data):
    """Tests creation with a more complete dataset and extra fields."""
    profile = CanonicalProfile(**full_profile_data)
    assert profile.profile_id == "12345"
    assert profile.follower_count == 1500
    assert hasattr(profile, 'unknown_field_profile')
    assert profile.unknown_field_profile == "this should also be allowed"
    assert hasattr(profile.experiences[0], 'unknown_field_exp')
    assert profile.experiences[0].unknown_field_exp == "should be allowed"

def test_profile_serialization(full_profile_data):
    """Tests that the model can be serialized to a dict and back (round-trip)."""
    profile1 = CanonicalProfile(**full_profile_data)
    serialized_data = profile1.model_dump()
    
    # Recreate the model from the serialized data
    profile2 = CanonicalProfile(**serialized_data)
    assert profile1 == profile2

def test_profile_type_validation():
    """Tests that Pydantic enforces correct data types."""
    invalid_data = {"full_name": "Test", "follower_count": "a string, not an int"}
    with pytest.raises(ValidationError):
        CanonicalProfile(**invalid_data)

# --- CanonicalCompany Tests ---

def test_canonical_company_creation(basic_company_data):
    """Tests that a CanonicalCompany can be created with basic valid data."""
    company = CanonicalCompany(**basic_company_data)
    assert company.company_name == "Innovate LLC"
    assert str(company.website) == "https://innovatellc.com/"
    assert company.employee_count == 250

def test_company_with_extra_fields(basic_company_data):
    """Tests that extra, undefined fields are allowed."""
    data = {**basic_company_data, "new_unforeseen_field": [1, 2, 3]}
    company = CanonicalCompany(**data)
    assert hasattr(company, "new_unforeseen_field")
    assert company.new_unforeseen_field == [1, 2, 3]

def test_company_serialization(basic_company_data):
    """Tests the serialization and deserialization round-trip for Company."""
    company1 = CanonicalCompany(**basic_company_data)
    serialized_data = company1.model_dump()
    company2 = CanonicalCompany(**serialized_data)
    
    # Compare key fields since computed fields might affect direct equality
    assert company1.company_name == company2.company_name
    assert company1.website == company2.website
    assert company1.employee_count == company2.employee_count
    assert company1.domain == company2.domain  # Should be auto-extracted in both

def test_company_missing_required_field():
    """Tests that a validation error is raised if a required field is missing."""
    with pytest.raises(ValidationError):
        CanonicalCompany(website="https://example.com") # Missing company_name

def test_canonical_company_full_creation(full_company_data):
    """Tests creation of CanonicalCompany with comprehensive data including nested models."""
    company = CanonicalCompany(**full_company_data)
    
    # Test basic fields
    assert company.company_name == "PricewaterhouseCoopers"
    assert company.company_id == "123456"
    assert str(company.linkedin_url) == "https://linkedin.com/company/pwc"
    assert company.tagline == "Building trust in society and solving important problems"
    assert str(company.website) == "https://www.pwc.com/"
    assert company.domain == "pwc.com"
    assert company.year_founded == 1998
    assert company.employee_count == 284478
    assert company.employee_range == "10001+"
    assert company.follower_count == 2500000
    
    # Test industries list
    assert len(company.industries) == 3
    assert "Professional Services" in company.industries
    assert "Consulting" in company.industries
    
    # Test HQ location fields
    assert company.hq_city == "London"
    assert company.hq_region == "England"
    assert company.hq_country == "United Kingdom"
    assert company.hq_address_line1 == "1 Embankment Place"
    assert company.hq_postalcode == "WC2N 6RH"
    
    # Test contact info
    assert company.email == "contact@pwc.com"
    assert company.phone == "+44 20 7583 5000"
    
    # Test nested funding_info
    assert company.funding_info is not None
    assert isinstance(company.funding_info, CanonicalFundingInfo)
    assert company.funding_info.last_funding_round_type == "Private Equity"
    assert company.funding_info.last_funding_round_amount == "$50M"
    assert company.funding_info.last_funding_round_year == 2020
    
    # Test locations list
    assert len(company.locations) == 2
    assert isinstance(company.locations[0], CanonicalCompanyLocation)
    hq_location = company.locations[0]
    assert hq_location.is_headquarter is True
    assert hq_location.city == "London"
    assert hq_location.country == "United Kingdom"
    
    # Test affiliated companies
    assert len(company.affiliated_companies) == 1
    assert isinstance(company.affiliated_companies[0], CanonicalAffiliatedCompany)
    affiliate = company.affiliated_companies[0]
    assert affiliate.name == "PwC Digital Services"
    assert affiliate.company_id == "789012"
    
    # Test raw_data
    assert company.raw_data is not None
    assert company.raw_data["source"] == "cassidy"
    
    # Test extra field handling
    assert hasattr(company, "custom_field")
    assert company.custom_field == "should be allowed due to extra='allow'"

def test_company_minimal_creation(minimal_company_data):
    """Tests creation of CanonicalCompany with only required fields."""
    company = CanonicalCompany(**minimal_company_data)
    assert company.company_name == "Minimal Corp"
    
    # Test default values
    assert company.industries == []
    assert company.locations == []
    assert company.affiliated_companies == []
    assert company.company_id is None
    assert company.website is None
    
    # Test auto-generated timestamp
    assert company.timestamp is not None
    assert isinstance(company.timestamp, datetime)

def test_company_startup_scenario(startup_company_data):
    """Tests CanonicalCompany with startup-specific data patterns."""
    company = CanonicalCompany(**startup_company_data)
    
    assert company.company_name == "TechStartup Inc"
    assert company.employee_count == 45
    assert company.employee_range == "11-50"
    
    # Test funding info for startup
    assert company.funding_info is not None
    assert company.funding_info.last_funding_round_type == "Series A"
    assert company.funding_info.last_funding_round_amount == "$15M"
    assert company.funding_info.last_funding_round_year == 2024
    
    # Test single HQ location
    assert len(company.locations) == 1
    hq = company.locations[0]
    assert hq.is_headquarter is True
    assert hq.city == "San Francisco"
    assert hq.region == "CA"
    
    # Test industries
    assert "Technology" in company.industries
    assert "Artificial Intelligence" in company.industries

def test_company_url_validation():
    """Tests URL field validation in CanonicalCompany."""
    # Valid URLs should work
    valid_data = {
        "company_name": "Test Company",
        "website": "https://test.com",
        "linkedin_url": "https://linkedin.com/company/test",
        "logo_url": "https://cdn.test.com/logo.png"
    }
    company = CanonicalCompany(**valid_data)
    assert str(company.website) == "https://test.com/"
    assert str(company.linkedin_url) == "https://linkedin.com/company/test"
    assert str(company.logo_url) == "https://cdn.test.com/logo.png"
    
    # Invalid URLs should raise ValidationError
    invalid_data = {
        "company_name": "Test Company",
        "website": "not-a-url"
    }
    with pytest.raises(ValidationError):
        CanonicalCompany(**invalid_data)

def test_company_nested_model_validation():
    """Tests validation of nested models in CanonicalCompany."""
    company_data = {
        "company_name": "Test Company",
        "funding_info": {
            "last_funding_round_year": "invalid_year"  # Should be int
        }
    }
    
    with pytest.raises(ValidationError) as exc_info:
        CanonicalCompany(**company_data)
    
    # Check that the error is related to the nested model
    assert "funding_info" in str(exc_info.value)

def test_company_field_type_coercion():
    """Tests that Pydantic properly coerces compatible types."""
    company_data = {
        "company_name": "Test Company",
        "employee_count": "500",  # String that can be converted to int
        "year_founded": "1995",   # String that can be converted to int
        "industries": ["Technology", "Software"]  # Correct list format
    }
    
    company = CanonicalCompany(**company_data)
    assert company.employee_count == 500
    assert company.year_founded == 1995
    assert company.industries == ["Technology", "Software"]
    
    # Test that string industries would fail validation (as expected)
    invalid_data = {
        "company_name": "Test Company",
        "industries": "Technology,Software"  # String instead of list should fail
    }
    
    with pytest.raises(ValidationError) as exc_info:
        CanonicalCompany(**invalid_data)
    assert "industries" in str(exc_info.value)

def test_company_serialization_round_trip(full_company_data):
    """Tests full serialization round-trip for complex CanonicalCompany data."""
    # Create company from data
    company1 = CanonicalCompany(**full_company_data)
    
    # Serialize to dict
    serialized = company1.model_dump()
    
    # Recreate from serialized data
    company2 = CanonicalCompany(**serialized)
    
    # Compare key fields (timestamps might differ slightly)
    assert company1.company_name == company2.company_name
    assert company1.company_id == company2.company_id
    assert company1.employee_count == company2.employee_count
    assert len(company1.locations) == len(company2.locations)
    assert len(company1.affiliated_companies) == len(company2.affiliated_companies)
    
    # Test nested model serialization
    if company1.funding_info:
        assert company1.funding_info.last_funding_round_type == company2.funding_info.last_funding_round_type
        assert company1.funding_info.last_funding_round_amount == company2.funding_info.last_funding_round_amount

def test_company_optional_fields_handling():
    """Tests handling of None/null values in optional fields."""
    company_data = {
        "company_name": "Test Company",
        "tagline": None,
        "description": None,
        "website": None,
        "year_founded": None,
        "employee_count": None,
        "funding_info": None
    }
    
    company = CanonicalCompany(**company_data)
    assert company.company_name == "Test Company"
    assert company.tagline is None
    assert company.description is None
    assert company.website is None
    assert company.year_founded is None
    assert company.employee_count is None
    assert company.funding_info is None

def test_canonical_funding_info_model():
    """Tests the CanonicalFundingInfo nested model independently."""
    funding_data = {
        "crunchbase_url": "https://crunchbase.com/org/test-company",
        "last_funding_round_type": "Series B",
        "last_funding_round_amount": "$25M",
        "last_funding_round_currency": "USD",
        "last_funding_round_year": 2023,
        "last_funding_round_month": 6,
        "last_funding_round_investor_count": 5,
        "custom_funding_field": "extra data allowed"
    }
    
    funding = CanonicalFundingInfo(**funding_data)
    assert funding.last_funding_round_type == "Series B"
    assert funding.last_funding_round_amount == "$25M"
    assert funding.last_funding_round_year == 2023
    assert funding.last_funding_round_investor_count == 5
    assert hasattr(funding, "custom_funding_field")

def test_canonical_company_location_model():
    """Tests the CanonicalCompanyLocation nested model independently."""
    location_data = {
        "is_headquarter": True,
        "full_address": "123 Main St, Anytown, CA 90210",
        "line1": "123 Main St",
        "city": "Anytown",
        "region": "CA",
        "country": "United States",
        "zipcode": "90210",
        "timezone": "PST"  # Extra field
    }
    
    location = CanonicalCompanyLocation(**location_data)
    assert location.is_headquarter is True
    assert location.city == "Anytown"
    assert location.zipcode == "90210"
    assert hasattr(location, "timezone")

def test_canonical_affiliated_company_model():
    """Tests the CanonicalAffiliatedCompany nested model independently."""
    affiliate_data = {
        "name": "Subsidiary Corp",
        "linkedin_url": "https://linkedin.com/company/subsidiary",
        "company_id": "sub123",
        "relationship": "subsidiary"  # Extra field
    }
    
    affiliate = CanonicalAffiliatedCompany(**affiliate_data)
    assert affiliate.name == "Subsidiary Corp"
    assert str(affiliate.linkedin_url) == "https://linkedin.com/company/subsidiary"
    assert affiliate.company_id == "sub123"
    assert hasattr(affiliate, "relationship")

# --- Enhanced CanonicalCompany Features Tests ---

def test_company_validators():
    """Tests the custom field validators in CanonicalCompany."""
    # Test company name cleaning
    company_data = {
        "company_name": "  Test   Company  ",  # Multiple spaces
        "email": "Contact@EXAMPLE.COM",  # Mixed case
        "industries": ["Tech", "Software", "Tech"],  # Duplicates
    }
    
    company = CanonicalCompany(**company_data)
    assert company.company_name == "Test Company"  # Cleaned
    assert company.email == "contact@example.com"  # Lowercased
    assert company.industries == ["Tech", "Software"]  # Deduplicated
    
    # Test validation errors
    with pytest.raises(ValidationError, match="Company name cannot be empty"):
        CanonicalCompany(company_name="   ")
    
    with pytest.raises(ValidationError, match="Invalid email format"):
        CanonicalCompany(company_name="Test", email="invalid-email")
    
    with pytest.raises(ValidationError, match="Employee count cannot be negative"):
        CanonicalCompany(company_name="Test", employee_count=-5)
    
    with pytest.raises(ValidationError, match="Year founded must be between"):
        CanonicalCompany(company_name="Test", year_founded=1500)  # Too old

def test_company_computed_fields():
    """Tests computed fields in CanonicalCompany."""
    company_data = {
        "company_name": "Test Startup",
        "employee_count": 25,
        "year_founded": 2020,
        "specialties": "AI, Machine Learning, Data Science",
        "hq_city": "San Francisco",
        "hq_country": "USA"
    }
    
    company = CanonicalCompany(**company_data)
    
    # Test computed fields
    assert company.display_name == "Test Startup"
    assert company.company_age == 2025 - 2020  # Current year - founded year
    assert company.size_category == "Small"  # 25 employees
    assert company.specialties_list == ["AI", "Machine Learning", "Data Science"]
    
    # Test headquarters computed field
    hq = company.headquarters
    assert hq is not None
    assert hq.city == "San Francisco"
    assert hq.country == "USA"
    assert hq.is_headquarter is True

def test_company_domain_extraction():
    """Tests automatic domain extraction from website."""
    company_data = {
        "company_name": "Test Company",
        "website": "https://www.example.com/path"
    }
    
    company = CanonicalCompany(**company_data)
    assert company.domain == "example.com"  # www. removed
    
    # Test domain consistency validation
    company_data2 = {
        "company_name": "Test Company",
        "website": "https://newdomain.com",
        "domain": "olddomain.com"  # Inconsistent
    }
    
    company2 = CanonicalCompany(**company_data2)
    # Should prefer website domain
    assert company2.domain == "newdomain.com"

def test_company_utility_methods():
    """Tests utility methods in CanonicalCompany."""
    company_data = {
        "company_name": "Test Startup",
        "company_id": "12345",
        "website": "https://test.com",
        "employee_count": 45,
        "year_founded": 2020,
        "industries": ["Technology", "AI"],
        "funding_info": {
            "last_funding_round_type": "Series A",
            "last_funding_round_amount": "$5M",
            "last_funding_round_year": 2024
        },
        "locations": [
            {
                "city": "San Francisco",
                "country": "USA",
                "is_headquarter": True
            },
            {
                "city": "New York",
                "country": "USA",
                "is_headquarter": False
            }
        ]
    }
    
    company = CanonicalCompany(**company_data)
    
    # Test summary dict
    summary = company.to_summary_dict()
    assert summary["company_name"] == "Test Startup"
    assert summary["size_category"] == "Small"
    assert summary["company_age"] == 5  # 2025 - 2020
    
    # Test primary industry
    assert company.get_primary_industry() == "Technology"
    
    # Test funding info check
    assert company.has_funding_info() is True
    
    # Test startup detection
    assert company.is_startup() is True  # Small, young, has Series A funding
    
    # Test location search
    sf_location = company.get_location_by_city("San Francisco")
    assert sf_location is not None
    assert sf_location.is_headquarter is True
    
    ny_location = company.get_location_by_city("New York")
    assert ny_location is not None
    assert ny_location.is_headquarter is False
    
    # Test string representation
    str_repr = str(company)
    assert "Test Startup" in str_repr
    assert "test.com" in str_repr
    assert "45 employees" in str_repr

def test_company_size_categories():
    """Tests size categorization logic."""
    test_cases = [
        (5, "Startup"),
        (25, "Small"),
        (150, "Medium"),
        (500, "Large"),
        (2000, "Enterprise"),
        (None, "Unknown")
    ]
    
    for employee_count, expected_category in test_cases:
        company = CanonicalCompany(
            company_name="Test Company",
            employee_count=employee_count
        )
        assert company.size_category == expected_category

def test_startup_detection_logic():
    """Tests the startup detection algorithm."""
    # Large company - not startup
    large_company = CanonicalCompany(
        company_name="Big Corp",
        employee_count=500,
        year_founded=2000
    )
    assert large_company.is_startup() is False
    
    # Old company - not startup
    old_company = CanonicalCompany(
        company_name="Old Corp",
        employee_count=30,
        year_founded=2000  # 25 years old
    )
    assert old_company.is_startup() is False
    
    # Young, small company with startup funding - is startup
    startup = CanonicalCompany(
        company_name="New Startup",
        employee_count=20,
        year_founded=2022,
        funding_info={
            "last_funding_round_type": "Seed",
            "last_funding_round_year": 2024
        }
    )
    assert startup.is_startup() is True
    
    # Small and young but no clear data - likely startup
    maybe_startup = CanonicalCompany(
        company_name="Maybe Startup",
        employee_count=15,
        year_founded=2020
    )
    assert maybe_startup.is_startup() is True

# --- Edge Case Tests ---

def test_empty_and_null_fields(basic_profile_data):
    """Tests that optional fields can be None or omitted without error."""
    # Add a field with a None value
    data = {**basic_profile_data, "about": None}
    profile = CanonicalProfile(**data)
    assert profile.about is None
    
    # Check a field that was never provided
    assert profile.city is None
