"""
Tests for enhanced profile ingestion pipeline with company data extraction.

Tests cover:
- Company data extraction from Cassidy responses
- Integration with CompanyService during profile ingestion
- Error handling for company processing
- Complete profile ingestion flow with companies
"""

import pytest
import uuid
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timezone
from typing import Dict, Any, List

from app.services.linkedin_pipeline import LinkedInDataPipeline
from app.services.company_service import CompanyService
from app.cassidy.models import LinkedInProfile, CompanyProfile, ExperienceEntry
from app.models.canonical.company import CanonicalCompany
from app.repositories.company_repository import CompanyRepository


class TestEnhancedProfileIngestion:
    """Test suite for enhanced profile ingestion with company integration."""
    
    @pytest.fixture
    def mock_company_service(self):
        """Create a mock CompanyService."""
        return Mock(spec=CompanyService)
    
    @pytest.fixture
    def mock_company_repo(self):
        """Create a mock CompanyRepository."""
        return Mock(spec=CompanyRepository)
    
    @pytest.fixture
    def linkedin_pipeline(self, mock_company_service):
        """Create LinkedInDataPipeline with mocked dependencies."""
        pipeline = LinkedInDataPipeline()
        # Inject our mock company service
        pipeline.company_service = mock_company_service
        return pipeline
    
    @pytest.fixture
    def sample_linkedin_profile(self):
        """Sample LinkedIn profile with company data."""
        return LinkedInProfile(
            profile_id="12345",
            full_name="John Doe",
            linkedin_url="https://linkedin.com/in/john-doe",
            headline="Senior Developer at TechCorp",
            company="TechCorp",
            job_title="Senior Developer",
            company_linkedin_url="https://linkedin.com/company/techcorp",
            company_domain="techcorp.com",
            company_employee_count=1500,
            company_employee_range="1001-5000",
            experiences=[
                ExperienceEntry(
                    title="Senior Developer",
                    company="TechCorp",
                    company_linkedin_url="https://linkedin.com/company/techcorp",
                    is_current=True,
                    start_year=2020,
                    start_month=1
                ),
                ExperienceEntry(
                    title="Junior Developer", 
                    company="StartupInc",
                    company_linkedin_url="https://linkedin.com/company/startupinc",
                    is_current=False,
                    start_year=2018,
                    start_month=6,
                    end_year=2019,
                    end_month=12
                )
            ]
        )
    
    @pytest.fixture
    def sample_company_profiles(self):
        """Sample company profiles from Cassidy."""
        return [
            CompanyProfile(
                company_id="techcorp",
                company_name="TechCorp",
                linkedin_url="https://linkedin.com/company/techcorp",
                domain="techcorp.com",
                employee_count=1500,
                employee_range="1001-5000",
                industries=["Technology", "Software"],
                description="Leading technology company"
            ),
            CompanyProfile(
                company_id="startupinc", 
                company_name="StartupInc",
                linkedin_url="https://linkedin.com/company/startupinc",
                domain="startupinc.com",
                employee_count=25,
                employee_range="11-50",
                industries=["Technology", "Startups"],
                description="Innovative startup company"
            )
        ]

    # Test 4.1: Enhanced profile ingestion pipeline with company data extraction

    @patch('app.services.linkedin_pipeline.LinkedInDataPipeline._has_db_config')
    @patch('app.services.linkedin_pipeline.LinkedInDataPipeline._has_openai_config')
    async def test_profile_ingestion_extracts_company_data(self, mock_openai_config, mock_db_config, 
                                                         linkedin_pipeline, sample_linkedin_profile, 
                                                         sample_company_profiles, mock_company_service):
        """Test that profile ingestion extracts and processes company data."""
        # Setup
        mock_db_config.return_value = True
        mock_openai_config.return_value = False
        
        # Mock Cassidy client
        linkedin_pipeline.cassidy_client = AsyncMock()
        linkedin_pipeline.cassidy_client.fetch_profile.return_value = sample_linkedin_profile
        linkedin_pipeline.cassidy_client.fetch_company.side_effect = sample_company_profiles
        
        # Mock database client
        linkedin_pipeline.db_client = AsyncMock()
        linkedin_pipeline.db_client.store_profile.return_value = str(uuid.uuid4())
        
        # Mock company service
        mock_company_service.batch_process_companies.return_value = [
            {"success": True, "action": "created", "company_id": str(uuid.uuid4()), "company_name": "TechCorp"},
            {"success": True, "action": "created", "company_id": str(uuid.uuid4()), "company_name": "StartupInc"}
        ]
        
        # Execute
        result = await linkedin_pipeline.ingest_profile_with_companies(
            "https://linkedin.com/in/john-doe"
        )
        
        # Verify
        assert result["status"] == "completed"
        assert len(result["companies"]) == 2
        assert result["companies"][0]["company_name"] == "TechCorp"
        assert result["companies"][1]["company_name"] == "StartupInc"
        
        # Verify company service was called
        mock_company_service.batch_process_companies.assert_called_once()
        companies_processed = mock_company_service.batch_process_companies.call_args[0][0]
        assert len(companies_processed) == 2

    # Test 4.3: Company data parsing with validation and error handling

    async def test_extract_company_data_from_profile(self, linkedin_pipeline, sample_linkedin_profile):
        """Test extraction of company data from LinkedIn profile."""
        # Execute
        company_data_list = linkedin_pipeline._extract_company_data_from_profile(sample_linkedin_profile)
        
        # Verify
        assert len(company_data_list) == 2  # Current company + one from experience
        
        # Check current company data
        current_company = company_data_list[0]
        assert current_company.company_name == "TechCorp"
        assert current_company.domain == "techcorp.com"
        assert current_company.employee_count == 1500
        
        # Check experience company data
        exp_company = company_data_list[1]  
        assert exp_company.company_name == "StartupInc"

    async def test_extract_company_data_handles_missing_data(self, linkedin_pipeline):
        """Test extraction handles profiles with missing company data gracefully."""
        # Setup profile with minimal data
        minimal_profile = LinkedInProfile(
            profile_id="12345",
            full_name="John Doe",
            linkedin_url="https://linkedin.com/in/john-doe",
            experiences=[]
        )
        
        # Execute
        company_data_list = linkedin_pipeline._extract_company_data_from_profile(minimal_profile)
        
        # Verify
        assert len(company_data_list) == 0  # No companies to extract

    async def test_extract_company_data_deduplicates_companies(self, linkedin_pipeline):
        """Test that company extraction deduplicates companies by LinkedIn URL."""
        # Setup profile with duplicate companies
        profile = LinkedInProfile(
            profile_id="12345",
            full_name="John Doe",
            linkedin_url="https://linkedin.com/in/john-doe",
            company="TechCorp",
            company_linkedin_url="https://linkedin.com/company/techcorp",
            experiences=[
                ExperienceEntry(
                    title="Senior Developer",
                    company="TechCorp", 
                    company_linkedin_url="https://linkedin.com/company/techcorp",  # Same as current
                    is_current=True
                ),
                ExperienceEntry(
                    title="Developer",
                    company="TechCorp",
                    company_linkedin_url="https://linkedin.com/company/techcorp",  # Duplicate
                    is_current=False
                )
            ]
        )
        
        # Execute
        company_data_list = linkedin_pipeline._extract_company_data_from_profile(profile)
        
        # Verify - should deduplicate to one company
        assert len(company_data_list) == 1
        assert company_data_list[0].company_name == "TechCorp"

    # Test 4.5 & 4.6: Error handling for malformed/missing company data

    @patch('app.services.linkedin_pipeline.LinkedInDataPipeline._has_db_config')
    async def test_profile_ingestion_handles_company_processing_errors(self, mock_db_config,
                                                                     linkedin_pipeline, sample_linkedin_profile,
                                                                     mock_company_service):
        """Test that profile ingestion continues when company processing fails."""
        # Setup
        mock_db_config.return_value = True
        
        # Mock Cassidy client
        linkedin_pipeline.cassidy_client = AsyncMock()
        linkedin_pipeline.cassidy_client.fetch_profile.return_value = sample_linkedin_profile
        
        # Mock database client
        linkedin_pipeline.db_client = AsyncMock()
        linkedin_pipeline.db_client.store_profile.return_value = str(uuid.uuid4())
        
        # Mock company service to fail
        mock_company_service.batch_process_companies.side_effect = Exception("Company service error")
        
        # Execute - should not raise exception
        result = await linkedin_pipeline.ingest_profile_with_companies(
            "https://linkedin.com/in/john-doe"
        )
        
        # Verify profile was still processed
        assert result["status"] == "completed"
        assert result["profile"] is not None
        assert "errors" in result
        assert len(result["errors"]) == 1
        assert "company service error" in result["errors"][0]["error"].lower()

    async def test_company_data_validation_handles_invalid_data(self, linkedin_pipeline):
        """Test that company data validation handles invalid or malformed data."""
        # Setup profile with invalid company data
        invalid_profile = LinkedInProfile(
            profile_id="12345",
            full_name="John Doe",
            linkedin_url="https://linkedin.com/in/john-doe",
            company="",  # Empty company name
            company_employee_count=-1,  # Invalid employee count
            experiences=[
                ExperienceEntry(
                    title="Developer",
                    company=None,  # None company
                    is_current=True
                )
            ]
        )
        
        # Execute
        company_data_list = linkedin_pipeline._extract_company_data_from_profile(invalid_profile)
        
        # Verify - should filter out invalid data
        assert len(company_data_list) == 0  # No valid companies extracted

    # Test 4.7: Integration tests for complete flow

    @patch('app.services.linkedin_pipeline.LinkedInDataPipeline._has_db_config')
    @patch('app.services.linkedin_pipeline.LinkedInDataPipeline._has_openai_config')
    async def test_complete_profile_ingestion_with_companies_integration(self, mock_openai_config, mock_db_config,
                                                                       linkedin_pipeline, sample_linkedin_profile,
                                                                       mock_company_service):
        """Test complete profile ingestion flow including company creation and linking."""
        # Setup
        mock_db_config.return_value = True
        mock_openai_config.return_value = False
        
        profile_id = str(uuid.uuid4())
        company_ids = [str(uuid.uuid4()), str(uuid.uuid4())]
        
        # Mock Cassidy client
        linkedin_pipeline.cassidy_client = AsyncMock()
        linkedin_pipeline.cassidy_client.fetch_profile.return_value = sample_linkedin_profile
        
        # Mock database client
        linkedin_pipeline.db_client = AsyncMock()
        linkedin_pipeline.db_client.store_profile.return_value = profile_id
        
        # Mock company service
        mock_company_service.batch_process_companies.return_value = [
            {"success": True, "action": "created", "company_id": company_ids[0], "company_name": "TechCorp"},
            {"success": True, "action": "updated", "company_id": company_ids[1], "company_name": "StartupInc"}
        ]
        
        # Execute
        result = await linkedin_pipeline.ingest_profile_with_companies(
            "https://linkedin.com/in/john-doe"
        )
        
        # Verify complete flow
        assert result["status"] == "completed"
        assert result["storage_ids"]["profile"] == profile_id
        assert len(result["companies"]) == 2
        assert result["companies"][0]["company_id"] == company_ids[0]
        assert result["companies"][1]["company_id"] == company_ids[1]
        
        # Verify all services were called
        linkedin_pipeline.cassidy_client.fetch_profile.assert_called_once()
        linkedin_pipeline.db_client.store_profile.assert_called_once()
        mock_company_service.batch_process_companies.assert_called_once()

    # Test 4.8: CompanyService integration during processing

    async def test_profile_ingestion_calls_company_service_correctly(self, linkedin_pipeline, sample_linkedin_profile,
                                                                   mock_company_service):
        """Test that profile ingestion calls CompanyService with correct parameters."""
        # Setup
        linkedin_pipeline.cassidy_client = AsyncMock()
        linkedin_pipeline.cassidy_client.fetch_profile.return_value = sample_linkedin_profile
        linkedin_pipeline.db_client = None  # Skip database storage
        
        # Execute
        result = await linkedin_pipeline.ingest_profile_with_companies(
            "https://linkedin.com/in/john-doe"
        )
        
        # Verify CompanyService was called with correct data
        mock_company_service.batch_process_companies.assert_called_once()
        companies_arg = mock_company_service.batch_process_companies.call_args[0][0]
        
        # Should have extracted companies from profile
        assert len(companies_arg) >= 1
        assert isinstance(companies_arg[0], CanonicalCompany)

    # Test 4.9: Realistic company data scenarios

    async def test_profile_ingestion_with_complex_company_scenarios(self, linkedin_pipeline, mock_company_service):
        """Test profile ingestion with complex, realistic company data scenarios."""
        # Setup complex profile with various company scenarios
        complex_profile = LinkedInProfile(
            profile_id="12345",
            full_name="Jane Smith",
            linkedin_url="https://linkedin.com/in/jane-smith", 
            company="Microsoft",
            job_title="Principal Engineer",
            company_linkedin_url="https://linkedin.com/company/microsoft",
            company_employee_count=221000,
            experiences=[
                # Current role at Microsoft
                ExperienceEntry(
                    title="Principal Engineer",
                    company="Microsoft", 
                    company_linkedin_url="https://linkedin.com/company/microsoft",
                    is_current=True,
                    start_year=2020
                ),
                # Previous role at Google
                ExperienceEntry(
                    title="Senior Software Engineer",
                    company="Google",
                    company_linkedin_url="https://linkedin.com/company/google", 
                    is_current=False,
                    start_year=2017,
                    end_year=2020
                ),
                # Startup experience
                ExperienceEntry(
                    title="Lead Developer",
                    company="TechStartup",
                    company_linkedin_url="https://linkedin.com/company/techstartup",
                    is_current=False,
                    start_year=2015,
                    end_year=2017
                ),
                # Experience without company URL (should be skipped)
                ExperienceEntry(
                    title="Developer",
                    company="Unknown Corp",
                    is_current=False,
                    start_year=2014,
                    end_year=2015
                )
            ]
        )
        
        # Setup
        linkedin_pipeline.cassidy_client = AsyncMock()
        linkedin_pipeline.cassidy_client.fetch_profile.return_value = complex_profile
        linkedin_pipeline.db_client = None  # Skip database storage
        
        mock_company_service.batch_process_companies.return_value = [
            {"success": True, "action": "updated", "company_name": "Microsoft"},
            {"success": True, "action": "updated", "company_name": "Google"},
            {"success": True, "action": "created", "company_name": "TechStartup"}
        ]
        
        # Execute
        result = await linkedin_pipeline.ingest_profile_with_companies(
            "https://linkedin.com/in/jane-smith"
        )
        
        # Verify
        assert result["status"] == "completed"
        mock_company_service.batch_process_companies.assert_called_once()
        
        # Should have processed 3 companies (Microsoft, Google, TechStartup)
        # Unknown Corp should be filtered out due to missing LinkedIn URL
        companies_processed = mock_company_service.batch_process_companies.call_args[0][0]
        assert len(companies_processed) == 3
        
        company_names = [c.company_name for c in companies_processed]
        assert "Microsoft" in company_names
        assert "Google" in company_names
        assert "TechStartup" in company_names
        assert "Unknown Corp" not in company_names

    async def test_batch_profile_ingestion_with_companies(self, linkedin_pipeline, sample_linkedin_profile,
                                                        mock_company_service):
        """Test batch profile ingestion includes company processing."""
        # Setup
        profiles = [sample_linkedin_profile] * 3  # Process 3 identical profiles
        
        linkedin_pipeline.cassidy_client = AsyncMock()
        linkedin_pipeline.cassidy_client.fetch_profile.side_effect = profiles
        linkedin_pipeline.db_client = None
        
        mock_company_service.batch_process_companies.return_value = [
            {"success": True, "action": "created", "company_name": "TechCorp"}
        ]
        
        # Execute
        results = await linkedin_pipeline.batch_ingest_profiles_with_companies([
            "https://linkedin.com/in/user1",
            "https://linkedin.com/in/user2",
            "https://linkedin.com/in/user3"
        ])
        
        # Verify
        assert len(results) == 3
        assert all(r["status"] == "completed" for r in results)
        
        # Company service should be called for each profile
        assert mock_company_service.batch_process_companies.call_count == 3
