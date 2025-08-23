"""
Unit tests for LinkedInDataPipeline company processing methods
Created for Task 1 analysis to understand and validate existing behavior
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.linkedin_pipeline import LinkedInDataPipeline
from app.cassidy.models import LinkedInProfile, CompanyProfile, ExperienceEntry


class TestLinkedInPipelineCompanyMethods:
    """Tests for LinkedInDataPipeline company processing methods"""
    
    @pytest.fixture
    def pipeline(self):
        """Create LinkedInDataPipeline instance with mocked dependencies"""
        with patch('app.services.linkedin_pipeline.CassidyClient'), \
             patch('app.services.linkedin_pipeline.SupabaseClient'), \
             patch('app.services.linkedin_pipeline.EmbeddingService'):
            return LinkedInDataPipeline()
    
    @pytest.fixture
    def sample_profile(self):
        """Create sample LinkedIn profile with company data"""
        experience = [
            ExperienceEntry(
                title="Senior Developer",
                company="Tech Corp",
                company_linkedin_url="https://linkedin.com/company/tech-corp"
            ),
            ExperienceEntry(
                title="Junior Developer", 
                company="Start Corp",
                company_linkedin_url="https://linkedin.com/company/start-corp"
            )
        ]
        
        return LinkedInProfile(
            full_name="John Doe",
            profile_id="johndoe",
            company="Current Corp",
            company_linkedin_url="https://linkedin.com/company/current-corp",
            experiences=experience
        )

    def test_extract_company_urls_basic(self, pipeline, sample_profile):
        """Test _extract_company_urls with basic profile data"""
        
        urls = pipeline._extract_company_urls(sample_profile)
        
        # Should extract current company (from current_company property) + 2 experience companies
        assert len(urls) == 3
        assert "https://linkedin.com/company/current-corp" in urls
        assert "https://linkedin.com/company/tech-corp" in urls  
        assert "https://linkedin.com/company/start-corp" in urls

    def test_extract_company_urls_deduplication(self, pipeline):
        """Test _extract_company_urls removes duplicates"""
        
        # Create profile with duplicate company URLs
        experience = [
            ExperienceEntry(
                title="Role 1",
                company="Same Corp", 
                company_linkedin_url="https://linkedin.com/company/same-corp"  # Duplicate
            ),
            ExperienceEntry(
                title="Role 2",
                company="Other Corp",
                company_linkedin_url="https://linkedin.com/company/other-corp"
            )
        ]
        
        profile = LinkedInProfile(
            full_name="Test User",
            profile_id="testuser",
            company="Same Corp",
            company_linkedin_url="https://linkedin.com/company/same-corp",
            experiences=experience
        )
        
        urls = pipeline._extract_company_urls(profile)
        
        # Should have only 2 unique URLs despite 3 entries
        assert len(urls) == 2
        assert "https://linkedin.com/company/same-corp" in urls
        assert "https://linkedin.com/company/other-corp" in urls
        
        # Verify same-corp appears only once
        assert urls.count("https://linkedin.com/company/same-corp") == 1

    def test_extract_company_urls_empty_profile(self, pipeline):
        """Test _extract_company_urls with empty profile data"""
        
        profile = LinkedInProfile(
            full_name="Empty User",
            profile_id="emptyuser",
            company=None,
            experiences=[]
        )
        
        urls = pipeline._extract_company_urls(profile)
        assert urls == []

    def test_extract_company_urls_processes_all_companies(self, pipeline):
        """Test _extract_company_urls processes all companies (no artificial limit)"""
        
        # Create profile with 7 companies (1 current + 6 experience)
        experience = [
            ExperienceEntry(
                title=f"Role {i}",
                company=f"Company {i}",
                company_linkedin_url=f"https://linkedin.com/company/company-{i}"
            ) for i in range(1, 7)  # Creates 6 experience entries
        ]
        
        profile = LinkedInProfile(
            full_name="Experienced User", 
            profile_id="expuser",
            company="Current Corp",
            company_linkedin_url="https://linkedin.com/company/current-corp",
            experiences=experience
        )
        
        urls = pipeline._extract_company_urls(profile)
        
        # Should process all 7 companies (no limit applied)
        assert len(urls) == 7
        
        # Should preserve order: current company first
        assert urls[0] == "https://linkedin.com/company/current-corp"
        
        # Should include all experience companies
        for i in range(1, 7):
            expected_url = f"https://linkedin.com/company/company-{i}"
            assert expected_url in urls

    @pytest.mark.asyncio
    async def test_fetch_companies_success(self, pipeline):
        """Test _fetch_companies with successful API calls"""
        
        # Mock successful company fetches
        mock_company1 = CompanyProfile(company_name="Company 1", company_id="1")
        mock_company2 = CompanyProfile(company_name="Company 2", company_id="2")
        
        # Create async mock for fetch_company
        async def mock_fetch_company(url):
            if "company-1" in url:
                return mock_company1
            else:
                return mock_company2
        
        pipeline.cassidy_client.fetch_company = Mock(side_effect=mock_fetch_company)
        
        urls = [
            "https://linkedin.com/company/company-1",
            "https://linkedin.com/company/company-2"
        ]
        
        with patch('asyncio.sleep'):  # Skip actual sleep delays
            companies = await pipeline._fetch_companies(urls)
        
        assert len(companies) == 2
        assert companies[0] == mock_company1  
        assert companies[1] == mock_company2
        
        # Verify API called for each URL
        assert pipeline.cassidy_client.fetch_company.call_count == 2

    @pytest.mark.asyncio  
    async def test_fetch_companies_partial_failure(self, pipeline):
        """Test _fetch_companies with some API failures"""
        
        # Mock one success and one failure
        mock_company = CompanyProfile(company_name="Success Corp", company_id="1")
        
        async def mock_fetch_side_effect(url):
            if "success" in url:
                return mock_company
            else:
                raise Exception("API Error")
        
        pipeline.cassidy_client.fetch_company.side_effect = mock_fetch_side_effect
        
        urls = [
            "https://linkedin.com/company/success-corp", 
            "https://linkedin.com/company/failure-corp"
        ]
        
        with patch('asyncio.sleep'):  # Skip actual sleep delays
            companies = await pipeline._fetch_companies(urls)
        
        # Should return only successful fetch
        assert len(companies) == 1
        assert companies[0] == mock_company

    @pytest.mark.asyncio
    async def test_fetch_companies_rate_limiting(self, pipeline):
        """Test _fetch_companies includes rate limiting delays"""
        
        mock_company = CompanyProfile(company_name="Test Corp", company_id="1")
        
        # Create async mock for fetch_company
        async def mock_fetch_company(url):
            return mock_company
        
        pipeline.cassidy_client.fetch_company = Mock(side_effect=mock_fetch_company)
        
        urls = ["https://linkedin.com/company/test-corp"]
        
        with patch('asyncio.sleep') as mock_sleep:
            companies = await pipeline._fetch_companies(urls)
            
            # Should call sleep once per URL for rate limiting
            assert mock_sleep.call_count == 1
            mock_sleep.assert_called_with(1)  # 1 second delay

    @pytest.mark.asyncio
    async def test_fetch_companies_empty_list(self, pipeline):
        """Test _fetch_companies with empty URL list"""
        
        companies = await pipeline._fetch_companies([])
        assert companies == []
        
        # Should not call API at all
        assert pipeline.cassidy_client.fetch_company.call_count == 0
    
    def test_extract_company_urls_large_profile(self, pipeline):
        """Test _extract_company_urls with large number of companies (50+)"""
        
        # Create profile with 50 experience companies + 1 current = 51 total
        experience = [
            ExperienceEntry(
                title=f"Role {i}",
                company=f"Company {i}",
                company_linkedin_url=f"https://linkedin.com/company/company-{i}"
            ) for i in range(1, 51)  # Creates 50 experience entries
        ]
        
        profile = LinkedInProfile(
            full_name="Executive User", 
            profile_id="execuser",
            company="Current Corp",
            company_linkedin_url="https://linkedin.com/company/current-corp",
            experiences=experience
        )
        
        urls = pipeline._extract_company_urls(profile)
        
        # Should process all 51 companies (no limit)
        assert len(urls) == 51
        
        # Should preserve order: current company first
        assert urls[0] == "https://linkedin.com/company/current-corp"
        
        # Should include all experience companies
        for i in range(1, 51):
            expected_url = f"https://linkedin.com/company/company-{i}"
            assert expected_url in urls
    
    def test_extract_company_urls_skips_missing_linkedin_urls(self, pipeline):
        """Test _extract_company_urls properly skips companies without LinkedIn URLs"""
        
        # Create profile with mix of companies - some with LinkedIn URLs, some without
        experience = [
            ExperienceEntry(
                title="Role 1",
                company="Company With URL",
                company_linkedin_url="https://linkedin.com/company/company-with-url"
            ),
            ExperienceEntry(
                title="Role 2",
                company="Company Without URL",
                company_linkedin_url=None  # No LinkedIn URL
            ),
            ExperienceEntry(
                title="Role 3",
                company="Company With Empty URL",
                company_linkedin_url=""  # Empty LinkedIn URL
            ),
            ExperienceEntry(
                title="Role 4",
                company="Another Company With URL",
                company_linkedin_url="https://linkedin.com/company/another-company"
            )
        ]
        
        profile = LinkedInProfile(
            full_name="Mixed User", 
            profile_id="mixeduser",
            company="Current Corp",
            company_linkedin_url="https://linkedin.com/company/current-corp",
            experiences=experience
        )
        
        urls = pipeline._extract_company_urls(profile)
        
        # Should only include companies with valid LinkedIn URLs (1 current + 2 with URLs = 3)
        assert len(urls) == 3
        
        expected_urls = [
            "https://linkedin.com/company/current-corp",
            "https://linkedin.com/company/company-with-url",
            "https://linkedin.com/company/another-company"
        ]
        
        for url in expected_urls:
            assert url in urls
        
        # Should not include companies without LinkedIn URLs
        for url in urls:
            assert url.startswith("https://linkedin.com/company/")
            assert len(url) > len("https://linkedin.com/company/")
