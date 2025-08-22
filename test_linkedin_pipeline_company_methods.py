#!/usr/bin/env python3
"""
Unit tests for LinkedInDataPipeline company processing methods
Part of Task 1.1 - Code Analysis and Documentation
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
import sys
import os

# Add the project to the path
sys.path.insert(0, '.')

@pytest.fixture
def linkedin_pipeline():
    """Create LinkedInDataPipeline instance with mocked dependencies"""
    from app.services.linkedin_pipeline import LinkedInDataPipeline
    
    # Mock the database and embedding service initialization
    with patch('app.services.linkedin_pipeline.SupabaseClient'):
        with patch('app.services.linkedin_pipeline.EmbeddingService'):
            pipeline = LinkedInDataPipeline()
            pipeline.cassidy_client = AsyncMock()
            return pipeline

@pytest.fixture
def mock_linkedin_profile():
    """Create mock LinkedIn profile with experience data"""
    mock_profile = Mock()
    
    # Mock current company
    mock_current_company = Mock()
    mock_current_company.linkedin_url = "https://www.linkedin.com/company/current-company"
    mock_profile.current_company = mock_current_company
    
    # Mock experience entries
    mock_exp1 = Mock()
    mock_exp1.company_linkedin_url = "https://www.linkedin.com/company/previous-company-1"
    
    mock_exp2 = Mock()
    mock_exp2.company_linkedin_url = "https://www.linkedin.com/company/previous-company-2"
    
    mock_exp3 = Mock()
    mock_exp3.company_linkedin_url = "https://www.linkedin.com/company/previous-company-1"  # Duplicate
    
    mock_profile.experience = [mock_exp1, mock_exp2, mock_exp3]
    
    return mock_profile

@pytest.fixture
def mock_company_profiles():
    """Create mock company profiles for Cassidy API responses"""
    companies = []
    
    for i, name in enumerate(["Current Company", "Previous Company 1", "Previous Company 2"]):
        company = Mock()
        company.company_name = name
        company.company_id = f"company_{i+1}"
        company.linkedin_url = f"https://www.linkedin.com/company/company-{i+1}"
        company.description = f"Description for {name}"
        company.website = f"https://company{i+1}.com"
        company.domain = f"company{i+1}.com"
        company.employee_count = (i+1) * 100
        company.employee_range = f"{(i+1)*100}-{(i+2)*100}"
        company.year_founded = 2000 + i
        company.industries = [f"Industry {i+1}"]
        company.hq_city = f"City {i+1}"
        company.hq_region = f"Region {i+1}"
        company.hq_country = f"Country {i+1}"
        company.logo_url = f"https://company{i+1}.com/logo.png"
        companies.append(company)
    
    return companies

class TestLinkedInPipelineExtractCompanyUrls:
    """Test LinkedInDataPipeline._extract_company_urls method"""
    
    def test_extract_company_urls_basic(self, linkedin_pipeline, mock_linkedin_profile):
        """Test basic company URL extraction"""
        urls = linkedin_pipeline._extract_company_urls(mock_linkedin_profile)
        
        assert isinstance(urls, list)
        assert len(urls) == 3  # Current + 2 unique from experience
        assert "https://www.linkedin.com/company/current-company" in urls
        assert "https://www.linkedin.com/company/previous-company-1" in urls
        assert "https://www.linkedin.com/company/previous-company-2" in urls
    
    def test_extract_company_urls_deduplication(self, linkedin_pipeline, mock_linkedin_profile):
        """Test that duplicate URLs are removed"""
        urls = linkedin_pipeline._extract_company_urls(mock_linkedin_profile)
        
        # Should not have duplicates despite mock_exp3 having same URL as mock_exp1
        url_set = set(urls)
        assert len(urls) == len(url_set), "URLs should be deduplicated"
    
    def test_extract_company_urls_no_current_company(self, linkedin_pipeline):
        """Test extraction when profile has no current company"""
        mock_profile = Mock()
        mock_profile.current_company = None
        
        mock_exp = Mock()
        mock_exp.company_linkedin_url = "https://www.linkedin.com/company/only-company"
        mock_profile.experience = [mock_exp]
        
        urls = linkedin_pipeline._extract_company_urls(mock_profile)
        
        assert len(urls) == 1
        assert urls[0] == "https://www.linkedin.com/company/only-company"
    
    def test_extract_company_urls_no_experience(self, linkedin_pipeline):
        """Test extraction when profile has no experience"""
        mock_profile = Mock()
        mock_current_company = Mock()
        mock_current_company.linkedin_url = "https://www.linkedin.com/company/only-current"
        mock_profile.current_company = mock_current_company
        mock_profile.experience = []
        
        urls = linkedin_pipeline._extract_company_urls(mock_profile)
        
        assert len(urls) == 1
        assert urls[0] == "https://www.linkedin.com/company/only-current"
    
    def test_extract_company_urls_limit_to_five(self, linkedin_pipeline):
        """Test that URL extraction is limited to 5 companies"""
        mock_profile = Mock()
        mock_profile.current_company = None
        
        # Create 10 experience entries
        mock_profile.experience = []
        for i in range(10):
            mock_exp = Mock()
            mock_exp.company_linkedin_url = f"https://www.linkedin.com/company/company-{i}"
            mock_profile.experience.append(mock_exp)
        
        urls = linkedin_pipeline._extract_company_urls(mock_profile)
        
        assert len(urls) <= 5, "Should limit to maximum 5 companies"

class TestLinkedInPipelineFetchCompanies:
    """Test LinkedInDataPipeline._fetch_companies method"""
    
    @pytest.mark.asyncio
    async def test_fetch_companies_basic(self, linkedin_pipeline, mock_company_profiles):
        """Test basic company fetching"""
        urls = [
            "https://www.linkedin.com/company/company-1",
            "https://www.linkedin.com/company/company-2"
        ]
        
        # Mock the cassidy client to return companies in order
        linkedin_pipeline.cassidy_client.fetch_company.side_effect = mock_company_profiles[:2]
        
        companies = await linkedin_pipeline._fetch_companies(urls)
        
        assert len(companies) == 2
        assert companies[0].company_name == "Current Company"
        assert companies[1].company_name == "Previous Company 1"
        assert linkedin_pipeline.cassidy_client.fetch_company.call_count == 2
    
    @pytest.mark.asyncio
    async def test_fetch_companies_with_rate_limiting(self, linkedin_pipeline, mock_company_profiles):
        """Test that rate limiting is applied between requests"""
        urls = [
            "https://www.linkedin.com/company/company-1",
            "https://www.linkedin.com/company/company-2"
        ]
        
        linkedin_pipeline.cassidy_client.fetch_company.side_effect = mock_company_profiles[:2]
        
        import time
        start_time = time.time()
        
        with patch('asyncio.sleep') as mock_sleep:
            companies = await linkedin_pipeline._fetch_companies(urls)
            
            # Should have called sleep between requests
            assert mock_sleep.call_count == 2  # Once per URL
            mock_sleep.assert_called_with(1)  # 1 second delay
    
    @pytest.mark.asyncio
    async def test_fetch_companies_error_handling(self, linkedin_pipeline, mock_company_profiles):
        """Test error handling when individual company fetches fail"""
        urls = [
            "https://www.linkedin.com/company/company-1",
            "https://www.linkedin.com/company/bad-company",
            "https://www.linkedin.com/company/company-2"
        ]
        
        # Mock first call success, second call failure, third call success
        linkedin_pipeline.cassidy_client.fetch_company.side_effect = [
            mock_company_profiles[0],
            Exception("Company not found"),
            mock_company_profiles[2]
        ]
        
        companies = await linkedin_pipeline._fetch_companies(urls)
        
        # Should return 2 companies (first and third), skipping the failed one
        assert len(companies) == 2
        assert companies[0].company_name == "Current Company"
        assert companies[1].company_name == "Previous Company 2"
    
    @pytest.mark.asyncio
    async def test_fetch_companies_empty_list(self, linkedin_pipeline):
        """Test fetching with empty URL list"""
        companies = await linkedin_pipeline._fetch_companies([])
        
        assert companies == []
        assert linkedin_pipeline.cassidy_client.fetch_company.call_count == 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
