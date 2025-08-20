"""
Test suite for enhanced LinkedInDataPipeline with company processing
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from datetime import datetime
import uuid
from typing import List, Dict, Any

from app.services.linkedin_pipeline import LinkedInDataPipeline
from app.cassidy.models import LinkedInProfile, ExperienceEntry
from app.models.canonical.company import CanonicalCompany
from app.services.company_service import CompanyService
from app.repositories.company_repository import CompanyRepository


class TestEnhancedProfileIngestion:
    """Test enhanced profile ingestion with company processing"""

    @pytest.fixture
    def mock_supabase_client(self):
        """Mock Supabase client"""
        client = AsyncMock()
        client.client = Mock()
        return client

    @pytest.fixture
    def mock_cassidy_client(self):
        """Mock Cassidy client"""
        return AsyncMock()

    @pytest.fixture
    def mock_embedding_service(self):
        """Mock embedding service"""
        return AsyncMock()

    @pytest.fixture
    def mock_company_service(self):
        """Mock company service"""
        return Mock()

    @pytest.fixture
    def sample_linkedin_profile(self):
        """Sample LinkedIn profile with company data"""
        return LinkedInProfile(
            full_name="John Doe",
            headline="Software Engineer at TechCorp",
            company="TechCorp Inc.",
            company_linkedin_url="https://linkedin.com/company/techcorp",
            company_domain="techcorp.com",
            company_employee_count=5000,
            company_employee_range="1000-5000",
            company_industry="Technology",
            company_description="Leading tech company",
            company_website="https://techcorp.com",
            company_logo_url="https://techcorp.com/logo.png",
            company_year_founded="2010",
            location="San Francisco, CA",
            about="Experienced software engineer",
            experiences=[
                ExperienceEntry(
                    company="StartupCorp",
                    company_linkedin_url="https://linkedin.com/company/startupcorp",
                    company_logo_url="https://startupcorp.com/logo.png"
                ),
                ExperienceEntry(
                    company="OldCorp",
                    company_linkedin_url="https://linkedin.com/company/oldcorp"
                )
            ]
        )

    @pytest.fixture
    def pipeline(self, mock_supabase_client, mock_cassidy_client, mock_embedding_service, mock_company_service):
        """Enhanced LinkedIn pipeline with mocked dependencies"""
        with patch('app.services.linkedin_pipeline.SupabaseClient', return_value=mock_supabase_client), \
             patch('app.services.linkedin_pipeline.EmbeddingService', return_value=mock_embedding_service), \
             patch('app.services.linkedin_pipeline.CompanyRepository') as mock_repo_class, \
             patch('app.services.linkedin_pipeline.CompanyService', return_value=mock_company_service):
            
            pipeline = LinkedInDataPipeline()
            pipeline.cassidy_client = mock_cassidy_client
            pipeline.db_client = mock_supabase_client
            pipeline.embedding_service = mock_embedding_service
            pipeline.company_service = mock_company_service
            
            return pipeline

    @pytest.mark.asyncio
    async def test_extract_company_data_from_profile(self, pipeline, sample_linkedin_profile):
        """Test company data extraction from LinkedIn profile"""
        companies = pipeline._extract_company_data_from_profile(sample_linkedin_profile)
        
        # Should extract 3 companies: current + 2 from experience
        assert len(companies) == 3
        
        # Check current company
        current_company = companies[0]
        assert current_company.company_name == "TechCorp Inc."
        assert str(current_company.linkedin_url) == "https://linkedin.com/company/techcorp"
        assert current_company.domain == "techcorp.com"
        assert current_company.employee_count == 5000
        assert current_company.employee_range == "1000-5000"
        assert current_company.industries == ["Technology"]
        assert current_company.description == "Leading tech company"
        assert str(current_company.website) == "https://techcorp.com/"
        assert str(current_company.logo_url) == "https://techcorp.com/logo.png"
        assert current_company.year_founded == 2010
        
        # Check experience companies
        exp_companies = companies[1:]
        company_names = [c.company_name for c in exp_companies]
        assert "StartupCorp" in company_names
        assert "OldCorp" in company_names

    @pytest.mark.asyncio
    async def test_extract_company_data_deduplication(self, pipeline):
        """Test company data extraction with duplicate LinkedIn URLs"""
        # Profile with duplicate company URLs
        profile = LinkedInProfile(
            full_name="Jane Doe",
            company="TechCorp",
            company_linkedin_url="https://linkedin.com/company/techcorp",
            experiences=[
                ExperienceEntry(
                    company="TechCorp",
                    company_linkedin_url="https://linkedin.com/company/techcorp"  # Duplicate URL
                ),
                ExperienceEntry(
                    company="OtherCorp",
                    company_linkedin_url="https://linkedin.com/company/othercorp"
                )
            ]
        )
        
        companies = pipeline._extract_company_data_from_profile(profile)
        
        # Should only have 2 companies (duplicate removed)
        assert len(companies) == 2
        company_urls = [str(c.linkedin_url) for c in companies]
        assert "https://linkedin.com/company/techcorp" in company_urls
        assert "https://linkedin.com/company/othercorp" in company_urls

    @pytest.mark.asyncio
    async def test_ingest_profile_with_companies_success(self, pipeline, sample_linkedin_profile, mock_cassidy_client, mock_company_service):
        """Test successful enhanced profile ingestion with company processing"""
        # Setup mocks
        mock_cassidy_client.fetch_profile.return_value = sample_linkedin_profile
        mock_company_service.batch_process_companies.return_value = [
            {
                "success": True,
                "company_id": "comp_123",
                "company_name": "TechCorp Inc.",
                "action": "created"
            },
            {
                "success": True,
                "company_id": "comp_456",
                "company_name": "StartupCorp",
                "action": "updated"
            }
        ]
        
        pipeline.embedding_service.embed_profile.return_value = [0.1] * 1536
        pipeline.db_client.store_profile.return_value = "profile_789"
        
        # Execute
        result = await pipeline.ingest_profile_with_companies("https://linkedin.com/in/johndoe")
        
        # Assertions
        assert result["status"] == "completed"
        assert result["linkedin_url"] == "https://linkedin.com/in/johndoe"
        assert "pipeline_id" in result
        assert "started_at" in result
        assert "completed_at" in result
        
        # Check profile data
        assert result["profile"]["full_name"] == "John Doe"
        assert result["profile"]["company"] == "TechCorp Inc."
        
        # Check company processing
        assert len(result["companies"]) == 2
        assert result["companies"][0]["company_id"] == "comp_123"
        assert result["companies"][0]["company_name"] == "TechCorp Inc."
        assert result["companies"][0]["action"] == "created"
        assert result["companies"][1]["company_id"] == "comp_456"
        assert result["companies"][1]["company_name"] == "StartupCorp"
        assert result["companies"][1]["action"] == "updated"
        
        # Check storage
        assert result["storage_ids"]["profile"] == "profile_789"
        
        # Check embeddings
        assert result["embeddings"]["profile"] == 1536
        
        # Verify service calls
        mock_cassidy_client.fetch_profile.assert_called_once_with("https://linkedin.com/in/johndoe")
        mock_company_service.batch_process_companies.assert_called_once()
        pipeline.embedding_service.embed_profile.assert_called_once()
        pipeline.db_client.store_profile.assert_called_once()

    @pytest.mark.asyncio
    async def test_ingest_profile_with_companies_no_company_service(self, pipeline, sample_linkedin_profile, mock_cassidy_client):
        """Test enhanced profile ingestion without company service"""
        # Remove company service
        pipeline.company_service = None
        
        # Setup mocks
        mock_cassidy_client.fetch_profile.return_value = sample_linkedin_profile
        pipeline.embedding_service.embed_profile.return_value = [0.1] * 1536
        pipeline.db_client.store_profile.return_value = "profile_789"
        
        # Execute
        result = await pipeline.ingest_profile_with_companies("https://linkedin.com/in/johndoe")
        
        # Should succeed but without company processing
        assert result["status"] == "completed"
        assert len(result["companies"]) == 0
        assert len(result["errors"]) == 0

    @pytest.mark.asyncio
    async def test_ingest_profile_with_companies_service_error(self, pipeline, sample_linkedin_profile, mock_cassidy_client, mock_company_service):
        """Test enhanced profile ingestion with company service error"""
        # Setup mocks
        mock_cassidy_client.fetch_profile.return_value = sample_linkedin_profile
        mock_company_service.batch_process_companies.side_effect = Exception("Company service error")
        pipeline.embedding_service.embed_profile.return_value = [0.1] * 1536
        pipeline.db_client.store_profile.return_value = "profile_789"
        
        # Execute
        result = await pipeline.ingest_profile_with_companies("https://linkedin.com/in/johndoe")
        
        # Should succeed with error logged
        assert result["status"] == "completed"
        assert len(result["companies"]) == 0
        assert len(result["errors"]) == 1
        assert "Company processing failed" in result["errors"][0]["error"]
        
        # Profile should still be processed
        assert result["storage_ids"]["profile"] == "profile_789"

    @pytest.mark.asyncio
    async def test_ingest_profile_with_companies_no_embeddings(self, pipeline, sample_linkedin_profile, mock_cassidy_client, mock_company_service):
        """Test enhanced profile ingestion without embeddings"""
        # Setup mocks
        mock_cassidy_client.fetch_profile.return_value = sample_linkedin_profile
        mock_company_service.batch_process_companies.return_value = []
        pipeline.db_client.store_profile.return_value = "profile_789"
        
        # Execute with embeddings disabled
        result = await pipeline.ingest_profile_with_companies(
            "https://linkedin.com/in/johndoe",
            generate_embeddings=False
        )
        
        # Should succeed without embeddings
        assert result["status"] == "completed"
        assert "profile" not in result["embeddings"]
        
        # Embedding service should not be called
        pipeline.embedding_service.embed_profile.assert_not_called()

    @pytest.mark.asyncio
    async def test_ingest_profile_with_companies_no_storage(self, pipeline, sample_linkedin_profile, mock_cassidy_client, mock_company_service):
        """Test enhanced profile ingestion without database storage"""
        # Setup mocks
        mock_cassidy_client.fetch_profile.return_value = sample_linkedin_profile
        mock_company_service.batch_process_companies.return_value = []
        pipeline.embedding_service.embed_profile.return_value = [0.1] * 1536
        
        # Execute with storage disabled
        result = await pipeline.ingest_profile_with_companies(
            "https://linkedin.com/in/johndoe",
            store_in_db=False
        )
        
        # Should succeed without storage
        assert result["status"] == "completed"
        assert "profile" not in result["storage_ids"]
        
        # Storage should not be called
        pipeline.db_client.store_profile.assert_not_called()

    @pytest.mark.asyncio
    async def test_batch_ingest_profiles_with_companies(self, pipeline, sample_linkedin_profile, mock_cassidy_client, mock_company_service):
        """Test batch enhanced profile ingestion"""
        urls = [
            "https://linkedin.com/in/user1",
            "https://linkedin.com/in/user2",
            "https://linkedin.com/in/user3"
        ]
        
        # Setup mocks
        mock_cassidy_client.fetch_profile.return_value = sample_linkedin_profile
        mock_company_service.batch_process_companies.return_value = []
        pipeline.embedding_service.embed_profile.return_value = [0.1] * 1536
        pipeline.db_client.store_profile.return_value = "profile_id"
        
        # Execute batch processing
        results = await pipeline.batch_ingest_profiles_with_companies(urls, max_concurrent=2)
        
        # Assertions
        assert len(results) == 3
        
        for i, result in enumerate(results):
            assert result["status"] == "completed"
            assert result["linkedin_url"] == urls[i]
            assert "pipeline_id" in result
        
        # Verify all profiles were processed
        assert mock_cassidy_client.fetch_profile.call_count == 3

    @pytest.mark.asyncio
    async def test_batch_ingest_with_failures(self, pipeline, sample_linkedin_profile, mock_cassidy_client, mock_company_service):
        """Test batch enhanced profile ingestion with some failures"""
        urls = [
            "https://linkedin.com/in/user1",  # Success
            "https://linkedin.com/in/user2",  # Failure
            "https://linkedin.com/in/user3"   # Success
        ]
        
        # Setup mocks - second call fails
        def mock_fetch_profile(url):
            if url == "https://linkedin.com/in/user2":
                raise Exception("Profile fetch failed")
            return sample_linkedin_profile
        
        mock_cassidy_client.fetch_profile.side_effect = mock_fetch_profile
        mock_company_service.batch_process_companies.return_value = []
        pipeline.embedding_service.embed_profile.return_value = [0.1] * 1536
        pipeline.db_client.store_profile.return_value = "profile_id"
        
        # Execute batch processing
        results = await pipeline.batch_ingest_profiles_with_companies(urls)
        
        # Assertions
        assert len(results) == 3
        assert results[0]["status"] == "completed"
        assert results[1]["status"] == "failed"
        assert results[2]["status"] == "completed"
        
        # Check failure details
        assert len(results[1]["errors"]) == 1
        assert "Profile fetch failed" in results[1]["errors"][0]["error"]

    @pytest.mark.asyncio
    async def test_extract_company_data_missing_linkedin_url(self, pipeline):
        """Test company data extraction with missing LinkedIn URLs"""
        profile = LinkedInProfile(
            full_name="Jane Doe",
            company="TechCorp",
            company_linkedin_url=None,  # Missing LinkedIn URL
            experiences=[
                ExperienceEntry(
                    company="StartupCorp",
                    company_linkedin_url="https://linkedin.com/company/startupcorp"
                ),
                ExperienceEntry(
                    company="OldCorp",
                    company_linkedin_url=None  # Missing LinkedIn URL
                )
            ]
        )
        
        companies = pipeline._extract_company_data_from_profile(profile)
        
        # Should only extract companies with LinkedIn URLs
        assert len(companies) == 1
        assert companies[0].company_name == "StartupCorp"

    @pytest.mark.asyncio
    async def test_extract_company_data_validation_errors(self, pipeline):
        """Test company data extraction with validation errors"""
        profile = LinkedInProfile(
            full_name="Jane Doe",
            company="",  # Empty company name
            company_linkedin_url="https://linkedin.com/company/techcorp",
            experiences=[
                ExperienceEntry(
                    company="ValidCorp",
                    company_linkedin_url="https://linkedin.com/company/validcorp"
                )
            ]
        )
        
        companies = pipeline._extract_company_data_from_profile(profile)
        
        # Should only extract valid companies
        assert len(companies) == 1
        assert companies[0].company_name == "ValidCorp"

    @pytest.mark.asyncio
    async def test_ingest_profile_with_companies_cassidy_error(self, pipeline, mock_cassidy_client):
        """Test enhanced profile ingestion with Cassidy API error"""
        # Setup mock to raise error
        mock_cassidy_client.fetch_profile.side_effect = Exception("Cassidy API error")
        
        # Execute and expect error
        with pytest.raises(Exception, match="Cassidy API error"):
            await pipeline.ingest_profile_with_companies("https://linkedin.com/in/johndoe")

    @pytest.mark.asyncio
    async def test_ingest_profile_with_companies_storage_error(self, pipeline, sample_linkedin_profile, mock_cassidy_client, mock_company_service):
        """Test enhanced profile ingestion with storage error"""
        # Setup mocks
        mock_cassidy_client.fetch_profile.return_value = sample_linkedin_profile
        mock_company_service.batch_process_companies.return_value = []
        pipeline.embedding_service.embed_profile.return_value = [0.1] * 1536
        pipeline.db_client.store_profile.side_effect = Exception("Storage error")
        
        # Execute and expect error
        with pytest.raises(Exception, match="Storage error"):
            await pipeline.ingest_profile_with_companies("https://linkedin.com/in/johndoe")
