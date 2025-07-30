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
    assert company1 == company2

def test_company_missing_required_field():
    """Tests that a validation error is raised if a required field is missing."""
    with pytest.raises(ValidationError):
        CanonicalCompany(website="https://example.com") # Missing company_name

# --- Edge Case Tests ---

def test_empty_and_null_fields(basic_profile_data):
    """Tests that optional fields can be None or omitted without error."""
    # Add a field with a None value
    data = {**basic_profile_data, "about": None}
    profile = CanonicalProfile(**data)
    assert profile.about is None
    
    # Check a field that was never provided
    assert profile.city is None
