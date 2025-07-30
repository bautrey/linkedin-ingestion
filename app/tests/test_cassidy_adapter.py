"""
Tests for Cassidy-to-Canonical Adapter

This module tests the adapter infrastructure that transforms Cassidy API responses
into our internal canonical models, focusing on the IncompleteDataError exception
and core transformation logic.
"""

import pytest
from typing import Dict, Any, List
from unittest.mock import Mock, patch

from app.adapters.exceptions import IncompleteDataError
from app.adapters.cassidy_adapter import CassidyAdapter
from app.models.canonical import (
    CanonicalProfile,
    CanonicalExperienceEntry,
    CanonicalEducationEntry
)


class TestIncompleteDataError:
    """Test the IncompleteDataError exception class."""
    
    def test_incomplete_data_error_creation(self):
        """Test that IncompleteDataError can be created with missing fields."""
        missing_fields = ["full_name", "linkedin_url"]
        error = IncompleteDataError(missing_fields)
        
        assert error.missing_fields == missing_fields
        assert "full_name" in str(error)
        assert "linkedin_url" in str(error)
        
    def test_incomplete_data_error_single_field(self):
        """Test IncompleteDataError with a single missing field."""
        missing_fields = ["profile_id"]
        error = IncompleteDataError(missing_fields)
        
        assert error.missing_fields == missing_fields
        assert len(error.missing_fields) == 1
        assert error.missing_fields[0] == "profile_id"
        
    def test_incomplete_data_error_empty_list(self):
        """Test IncompleteDataError with empty missing fields list."""
        error = IncompleteDataError([])
        
        assert error.missing_fields == []
        assert "No missing fields specified" in str(error)
        
    def test_incomplete_data_error_message_format(self):
        """Test that error message is properly formatted."""
        missing_fields = ["full_name", "headline", "linkedin_url"]
        error = IncompleteDataError(missing_fields)
        
        error_str = str(error)
        assert "Missing essential profile fields" in error_str
        for field in missing_fields:
            assert field in error_str


class TestCassidyAdapterInfrastructure:
    """Test the basic infrastructure of the CassidyAdapter class."""
    
    @pytest.fixture
    def adapter(self):
        """Create a CassidyAdapter instance for testing."""
        return CassidyAdapter()
        
    def test_adapter_creation(self, adapter):
        """Test that CassidyAdapter can be instantiated."""
        assert isinstance(adapter, CassidyAdapter)
        assert hasattr(adapter, 'transform')
        
    def test_adapter_has_required_methods(self, adapter):
        """Test that adapter has all required transformation methods."""
        required_methods = [
            'transform',
            '_transform_experience',
            '_transform_education',
            '_transform_company'
        ]
        
        for method_name in required_methods:
            assert hasattr(adapter, method_name)
            assert callable(getattr(adapter, method_name))


class TestCassidyAdapterCoreTransformation:
    """Test the core transformation logic from Cassidy response to CanonicalProfile."""

    @pytest.fixture
    def adapter(self):
        """Create a CassidyAdapter instance for testing."""
        return CassidyAdapter()

    def test_transform_complete_profile(self, adapter):
        """Test transforming a complete Cassidy profile to CanonicalProfile."""
        cassidy_profile = {
            "profile_id": "ronald-sorozan-mba-cism-pmp-8325652",
            "full_name": "Ronald Sorozan",
            "linkedin_url": "https://www.linkedin.com/in/ronald-sorozan-mba-cism-pmp-8325652/",
            "experiences": [
                {
                    "title": "Global Chief Information Officer",
                    "company": "JAM+",
                    "start_year": 2021,
                    "end_year": "Present"
                }
            ],
            "educations": [
                {
                    "school": "Drexel University's LeBow College of Business",
                    "degree": "MBA"
                }
            ]
        }

        profile = adapter.transform(cassidy_profile)

        assert profile.profile_id == "ronald-sorozan-mba-cism-pmp-8325652"
        assert profile.full_name == "Ronald Sorozan"
        assert str(profile.linkedin_url) == "https://www.linkedin.com/in/ronald-sorozan-mba-cism-pmp-8325652/"
        assert len(profile.experiences) == 1
        assert profile.experiences[0].title == "Global Chief Information Officer"
        assert profile.experiences[0].company == "JAM+"
        assert profile.experiences[0].start_year == 2021
        assert profile.experiences[0].end_year is None  # "Present" should be converted to None
        assert len(profile.educations) == 1
        assert profile.educations[0].school == "Drexel University's LeBow College of Business"

    def test_transform_incomplete_profile_raises_error(self, adapter):
        """Test transforming an incomplete Cassidy profile raises IncompleteDataError."""
        incomplete_profile = {
            "full_name": "Incomplete Profile",
            # omitting essential field 'linkedin_url'
        }

        with pytest.raises(IncompleteDataError):
            adapter.transform(incomplete_profile)

    def test_experience_field_conversion(self, adapter):
        """Test that experience field conversion handles different data types correctly."""
        # Test "Present" conversion to None
        assert adapter._convert_experience_field("end_year", "Present") is None
        assert adapter._convert_experience_field("end_year", "Current") is None
        assert adapter._convert_experience_field("end_year", "now") is None
        
        # Test numeric string conversion
        assert adapter._convert_experience_field("start_year", "2021") == 2021
        assert adapter._convert_experience_field("end_year", "2023") == 2023
        
        # Test invalid string conversion
        assert adapter._convert_experience_field("start_year", "invalid") is None
        
        # Test non-year fields pass through unchanged
        assert adapter._convert_experience_field("title", "Software Engineer") == "Software Engineer"
        assert adapter._convert_experience_field("company", "Tech Corp") == "Tech Corp"


class TestCassidyAdapterNestedTransformation:
    """Test the nested data transformation logic for experiences, education, and companies."""

    @pytest.fixture
    def adapter(self):
        """Create a CassidyAdapter instance for testing."""
        return CassidyAdapter()

    def test_transform_experience_complete(self, adapter):
        """Test transforming a complete experience entry."""
        experience_data = {
            "title": "Senior Software Engineer",
            "company": "Tech Corp",
            "company_linkedin_url": "https://www.linkedin.com/company/tech-corp/",
            "company_logo_url": "https://example.com/logo.png",
            "location": "San Francisco, CA",
            "start_year": 2020,
            "start_month": 3,
            "end_year": "Present",
            "end_month": None,
            "date_range": "Mar 2020 - Present",
            "duration": "3 yrs 10 mos",
            "description": "Led development of cloud infrastructure",
            "is_current": True,
            "job_type": "Full-time",
            "skills": "Python, AWS, Kubernetes",
            "company_id": "tech-corp"
        }

        experience = adapter._transform_experience(experience_data)

        assert experience.title == "Senior Software Engineer"
        assert experience.company == "Tech Corp"
        assert str(experience.company_linkedin_url) == "https://www.linkedin.com/company/tech-corp/"
        assert experience.location == "San Francisco, CA"
        assert experience.start_year == 2020
        assert experience.start_month == 3
        assert experience.end_year is None  # "Present" converted to None
        assert experience.date_range == "Mar 2020 - Present"
        assert experience.duration == "3 yrs 10 mos"
        assert experience.description == "Led development of cloud infrastructure"
        assert experience.is_current is True
        assert experience.job_type == "Full-time"
        assert experience.skills == "Python, AWS, Kubernetes"
        assert experience.company_id == "tech-corp"

    def test_transform_experience_minimal(self, adapter):
        """Test transforming an experience with minimal data."""
        experience_data = {
            "title": "Intern",
            "company": "Startup Inc"
        }

        experience = adapter._transform_experience(experience_data)

        assert experience.title == "Intern"
        assert experience.company == "Startup Inc"
        assert experience.company_linkedin_url is None
        assert experience.start_year is None
        assert experience.end_year is None

    def test_transform_experiences_list(self, adapter):
        """Test transforming a list of experience entries."""
        experiences_data = [
            {
                "title": "Senior Engineer",
                "company": "Current Corp",
                "start_year": 2022,
                "end_year": "Present"
            },
            {
                "title": "Junior Engineer",
                "company": "Previous Corp",
                "start_year": 2020,
                "end_year": 2022
            }
        ]

        experiences = adapter._transform_experiences(experiences_data)

        assert len(experiences) == 2
        assert experiences[0].title == "Senior Engineer"
        assert experiences[0].company == "Current Corp"
        assert experiences[0].end_year is None  # Current position
        assert experiences[1].title == "Junior Engineer"
        assert experiences[1].company == "Previous Corp"
        assert experiences[1].end_year == 2022  # Past position

    def test_transform_education_complete(self, adapter):
        """Test transforming a complete education entry."""
        education_data = {
            "school": "Stanford University",
            "degree": "Master of Science",
            "field_of_study": "Computer Science",
            "start_year": 2018,
            "end_year": 2020,
            "date_range": "2018 - 2020",
            "activities": "Computer Science Club, Hackathons",
            "school_linkedin_url": "https://www.linkedin.com/school/stanford-university/",
            "school_id": "stanford-university"
        }

        education = adapter._transform_education(education_data)

        assert education.school == "Stanford University"
        assert education.degree == "Master of Science"
        assert education.field_of_study == "Computer Science"
        assert education.start_year == 2018
        assert education.end_year == 2020
        assert education.date_range == "2018 - 2020"
        assert education.activities == "Computer Science Club, Hackathons"
        assert str(education.school_linkedin_url) == "https://www.linkedin.com/school/stanford-university/"
        assert education.school_id == "stanford-university"

    def test_transform_education_minimal(self, adapter):
        """Test transforming an education with minimal data."""
        education_data = {
            "school": "Local College",
            "degree": "Bachelor's"
        }

        education = adapter._transform_education(education_data)

        assert education.school == "Local College"
        assert education.degree == "Bachelor's"
        assert education.field_of_study is None
        assert education.start_year is None
        assert education.end_year is None

    def test_transform_educations_list(self, adapter):
        """Test transforming a list of education entries."""
        educations_data = [
            {
                "school": "Stanford University",
                "degree": "MS",
                "field_of_study": "Computer Science"
            },
            {
                "school": "UC Berkeley",
                "degree": "BS",
                "field_of_study": "Mathematics"
            }
        ]

        educations = adapter._transform_educations(educations_data)

        assert len(educations) == 2
        assert educations[0].school == "Stanford University"
        assert educations[0].degree == "MS"
        assert educations[0].field_of_study == "Computer Science"
        assert educations[1].school == "UC Berkeley"
        assert educations[1].degree == "BS"
        assert educations[1].field_of_study == "Mathematics"

    def test_transform_company_complete(self, adapter):
        """Test transforming a complete company profile."""
        company_data = {
            "company_id": "tech-corp-123",
            "company_name": "Tech Corp",
            "linkedin_url": "https://www.linkedin.com/company/tech-corp/",
            "tagline": "Innovative Technology Solutions",
            "description": "We build cutting-edge software solutions",
            "website": "https://www.techcorp.com",
            "domain": "techcorp.com",
            "logo_url": "https://example.com/logo.png",
            "year_founded": 2010,
            "industries": ["Technology", "Software"],
            "specialties": "Cloud Computing, AI, Machine Learning",
            "employee_count": 1500,
            "employee_range": "1001-5000",
            "follower_count": 25000,
            "hq_address_line1": "123 Tech Street",
            "hq_address_line2": "Suite 100",
            "hq_city": "San Francisco",
            "hq_region": "California",
            "hq_country": "US",
            "hq_postalcode": "94105",
            "hq_full_address": "123 Tech Street, Suite 100, San Francisco, CA 94105",
            "email": "contact@techcorp.com",
            "phone": "+1-555-123-4567"
        }

        company = adapter._transform_company(company_data)

        assert company.company_id == "tech-corp-123"
        assert company.company_name == "Tech Corp"
        assert str(company.linkedin_url) == "https://www.linkedin.com/company/tech-corp/"
        assert company.tagline == "Innovative Technology Solutions"
        assert company.description == "We build cutting-edge software solutions"
        assert str(company.website) == "https://www.techcorp.com/"
        assert company.domain == "techcorp.com"
        assert company.year_founded == 2010
        assert company.industries == ["Technology", "Software"]
        assert company.specialties == "Cloud Computing, AI, Machine Learning"
        assert company.employee_count == 1500
        assert company.employee_range == "1001-5000"
        assert company.follower_count == 25000
        assert company.hq_city == "San Francisco"
        assert company.hq_region == "California"
        assert company.hq_country == "US"
        assert company.email == "contact@techcorp.com"
        assert company.phone == "+1-555-123-4567"

    def test_transform_company_missing_required_field(self, adapter):
        """Test that company transformation raises error when required field is missing."""
        company_data = {
            "company_id": "tech-corp-123",
            # Missing required 'company_name' field
            "description": "Some description"
        }

        with pytest.raises(IncompleteDataError) as exc_info:
            adapter._transform_company(company_data)
            
        error = exc_info.value
        assert "company_name" in error.missing_fields

    def test_transform_company_with_nested_data(self, adapter):
        """Test transforming company with nested funding info, locations, and affiliated companies."""
        company_data = {
            "company_name": "Tech Corp",
            "funding_info": {
                "crunchbase_url": "https://www.crunchbase.com/organization/tech-corp",
                "last_funding_round_type": "Series B",
                "last_funding_round_amount": "$50M",
                "last_funding_round_currency": "USD",
                "last_funding_round_year": 2022,
                "last_funding_round_month": 6,
                "last_funding_round_investor_count": 3
            },
            "locations": [
                {
                    "is_headquarter": True,
                    "full_address": "123 Main St, San Francisco, CA 94105",
                    "line1": "123 Main St",
                    "city": "San Francisco",
                    "region": "California",
                    "country": "US",
                    "zipcode": "94105"
                }
            ],
            "affiliated_companies": [
                {
                    "name": "Tech Subsidiary",
                    "linkedin_url": "https://www.linkedin.com/company/tech-subsidiary/",
                    "company_id": "tech-subsidiary-123"
                }
            ]
        }

        company = adapter._transform_company(company_data)

        assert company.company_name == "Tech Corp"
        assert company.funding_info is not None
        assert company.funding_info.last_funding_round_type == "Series B"
        assert company.funding_info.last_funding_round_amount == "$50M"
        assert len(company.locations) == 1
        assert company.locations[0].is_headquarter is True
        assert company.locations[0].city == "San Francisco"
        assert len(company.affiliated_companies) == 1
        assert company.affiliated_companies[0].name == "Tech Subsidiary"


class TestCassidyAdapterValidation:
    """Test the validation logic that detects incomplete data."""
    
    @pytest.fixture
    def adapter(self):
        """Create a CassidyAdapter instance for testing."""
        return CassidyAdapter()
        
    def test_validate_essential_fields_missing_all(self, adapter):
        """Test validation when all essential fields are missing."""
        cassidy_data = {}
        
        with pytest.raises(IncompleteDataError) as exc_info:
            adapter._validate_essential_fields(cassidy_data)
            
        error = exc_info.value
        # Should detect missing profile_id, full_name, and linkedin_url
        assert "profile_id" in error.missing_fields
        assert "full_name" in error.missing_fields  
        assert "linkedin_url" in error.missing_fields
        
    def test_validate_essential_fields_partial_missing(self, adapter):
        """Test validation when some essential fields are missing."""
        cassidy_data = {
            "profile_id": "test123",
            "full_name": "Test User"
            # linkedin_url is missing
        }
        
        with pytest.raises(IncompleteDataError) as exc_info:
            adapter._validate_essential_fields(cassidy_data)
            
        error = exc_info.value
        assert "linkedin_url" in error.missing_fields
        assert "profile_id" not in error.missing_fields  # This should be present
        assert "full_name" not in error.missing_fields   # This should be present
        
    def test_validate_essential_fields_all_present(self, adapter):
        """Test validation when all essential fields are present."""
        cassidy_data = {
            "profile_id": "test123",
            "full_name": "Test User",
            "linkedin_url": "https://www.linkedin.com/in/testuser/"
        }
        
        # Should not raise an exception
        adapter._validate_essential_fields(cassidy_data)
        
    def test_validate_essential_fields_empty_strings(self, adapter):
        """Test validation treats empty strings as missing."""
        cassidy_data = {
            "profile_id": "",
            "full_name": "Test User",
            "linkedin_url": "https://www.linkedin.com/in/testuser/"
        }
        
        with pytest.raises(IncompleteDataError) as exc_info:
            adapter._validate_essential_fields(cassidy_data)
            
        error = exc_info.value
        assert "profile_id" in error.missing_fields
        
    def test_validate_essential_fields_none_values(self, adapter):
        """Test validation treats None values as missing."""
        cassidy_data = {
            "profile_id": "test123",
            "full_name": None,
            "linkedin_url": "https://www.linkedin.com/in/testuser/"
        }
        
        with pytest.raises(IncompleteDataError) as exc_info:
            adapter._validate_essential_fields(cassidy_data)
            
        error = exc_info.value
        assert "full_name" in error.missing_fields


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
