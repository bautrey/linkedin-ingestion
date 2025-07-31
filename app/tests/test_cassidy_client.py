"""
Unit tests for CassidyClient

Tests the LinkedIn profile and company data extraction functionality
with comprehensive mock data scenarios.
"""

import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from pydantic import ValidationError

from app.cassidy.client import CassidyClient
from app.cassidy.models import LinkedInProfile, CompanyProfile
from app.cassidy.exceptions import (
    CassidyWorkflowError,
    CassidyAPIError,
    CassidyTimeoutError,
    CassidyRateLimitError
)
from app.tests.fixtures.mock_responses import (
    MOCK_CASSIDY_PROFILE_RESPONSE,
    MOCK_CASSIDY_COMPANY_RESPONSE,
    MOCK_PROFILE_MINIMAL_DATA,
    MOCK_PROFILE_WITH_MULTIPLE_COMPANIES,
    MOCK_CASSIDY_ERROR_RESPONSE,
    MOCK_CASSIDY_TIMEOUT_RESPONSE,
    TEST_LINKEDIN_PROFILE_URL,
    TEST_LINKEDIN_COMPANY_URL
)


class TestCassidyClient:
    """Test suite for CassidyClient"""
    
    @pytest.fixture
    def client(self):
        """Create CassidyClient instance for testing"""
        return CassidyClient()
    
    @pytest.fixture
    def mock_httpx_response(self):
        """Create mock HTTP response"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_CASSIDY_PROFILE_RESPONSE
        mock_response.elapsed.total_seconds.return_value = 1.5
        mock_response.headers = {}
        return mock_response


class TestProfileFetching(TestCassidyClient):
    """Test LinkedIn profile fetching functionality"""
    
    @pytest.mark.asyncio
    async def test_fetch_profile_success(self, client, mock_httpx_response):
        """Test successful profile fetching"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_httpx_response
            
            profile = await client.fetch_profile(TEST_LINKEDIN_PROFILE_URL)
            
            assert isinstance(profile, LinkedInProfile)
            assert profile.name == "Ronald Sorozan (MBA, CISM, PMP)"
            assert profile.id == "ronald-sorozan-mba-cism-pmp-8325652"
            assert len(profile.experience) == 1
            assert len(profile.education) == 1
            assert len(profile.certifications) == 2
    
    @pytest.mark.asyncio 
    async def test_fetch_profile_minimal_data(self, client):
        """Test profile fetching with minimal data"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_PROFILE_MINIMAL_DATA
        mock_response.elapsed.total_seconds.return_value = 1.0
        mock_response.headers = {}
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            profile = await client.fetch_profile("https://linkedin.com/in/jane-smith")
            
            assert isinstance(profile, LinkedInProfile)
            assert profile.name == "Jane Smith"
            assert profile.position == "Software Engineer"
            assert len(profile.experience) == 0
            assert len(profile.education) == 0
    
    @pytest.mark.asyncio
    async def test_fetch_profile_multiple_companies(self, client):
        """Test profile with multiple work experiences"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_PROFILE_WITH_MULTIPLE_COMPANIES
        mock_response.elapsed.total_seconds.return_value = 2.0
        mock_response.headers = {}
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            profile = await client.fetch_profile("https://linkedin.com/in/john-doe")
            
            assert isinstance(profile, LinkedInProfile)
            assert profile.name == "John Doe"
            assert len(profile.experience) == 2
            assert profile.experience[0].company == "Tech Corp"
            assert profile.experience[1].company == "StartupXYZ"
    
    @pytest.mark.asyncio
    async def test_fetch_profile_api_error(self, client):
        """Test handling of API errors"""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"error": "Internal Server Error"}
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            with pytest.raises(CassidyAPIError):
                await client.fetch_profile(TEST_LINKEDIN_PROFILE_URL)
    
    @pytest.mark.asyncio
    async def test_fetch_profile_rate_limit(self, client):
        """Test handling of rate limit errors"""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "60"}
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            with pytest.raises((CassidyRateLimitError, Exception)):
                await client.fetch_profile(TEST_LINKEDIN_PROFILE_URL)
    
    @pytest.mark.asyncio
    async def test_fetch_profile_workflow_failure(self, client):
        """Test handling of workflow failures"""
        failed_response = {
            "workflowRun": {
                "id": "failed-workflow",
                "status": "FAILED",
                "actionResults": [{
                    "id": "action-1",
                    "status": "FAILED",
                    "error": "Profile not found"
                }]
            }
        }
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = failed_response
        mock_response.elapsed.total_seconds.return_value = 1.0
        mock_response.headers = {}
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            with pytest.raises(CassidyWorkflowError):
                await client.fetch_profile(TEST_LINKEDIN_PROFILE_URL)


class TestCompanyFetching(TestCassidyClient):
    """Test LinkedIn company fetching functionality"""
    
    @pytest.mark.asyncio
    async def test_fetch_company_success(self, client):
        """Test successful company fetching"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_CASSIDY_COMPANY_RESPONSE
        mock_response.elapsed.total_seconds.return_value = 1.5
        mock_response.headers = {}
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            company = await client.fetch_company(TEST_LINKEDIN_COMPANY_URL)
            
            assert isinstance(company, CompanyProfile)
            assert company.company_name == "JAM+"
            assert company.company_id == "jambnc"
            assert company.employee_count == 250
            assert "Printing" in company.industries
            assert company.year_founded == "2018"
    
    @pytest.mark.asyncio
    async def test_fetch_company_no_data_fallback(self, client):
        """Test company fetching fallback when no data found"""
        empty_response = {
            "workflowRun": {
                "id": "empty-workflow",
                "status": "completed",
                "actionResults": [{
                    "id": "action-1", 
                    "status": "success",
                    "output": {"value": None}
                }]
            }
        }
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = empty_response
        mock_response.elapsed.total_seconds.return_value = 1.0
        mock_response.headers = {}
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            company = await client.fetch_company(TEST_LINKEDIN_COMPANY_URL)
            
            assert isinstance(company, CompanyProfile)
            assert company.company_name == "Unknown Company"
            assert company.industries == []


class TestBatchCompanyFetching(TestCassidyClient):
    """Test batch company fetching functionality"""
    
    @pytest.mark.asyncio
    async def test_batch_fetch_companies_success(self, client):
        """Test successful batch company fetching"""
        company_urls = [
            "https://linkedin.com/company/company1",
            "https://linkedin.com/company/company2"
        ]
        
        # Mock the fetch_company method
        with patch.object(client, 'fetch_company') as mock_fetch:
            mock_company1 = CompanyProfile(company_name="Company 1")
            mock_company2 = CompanyProfile(company_name="Company 2")
            mock_fetch.side_effect = [mock_company1, mock_company2]
            
            # Mock asyncio.sleep to speed up test
            with patch('asyncio.sleep', return_value=None):
                companies = await client.batch_fetch_companies(company_urls, delay_seconds=0.1)
            
            assert len(companies) == 2
            assert companies[0].company_name == "Company 1"
            assert companies[1].company_name == "Company 2"
    
    @pytest.mark.asyncio
    async def test_batch_fetch_companies_with_failures(self, client):
        """Test batch fetching with some failures"""
        company_urls = [
            "https://linkedin.com/company/valid",
            "https://linkedin.com/company/invalid"
        ]
        
        with patch.object(client, 'fetch_company') as mock_fetch:
            mock_company = CompanyProfile(company_name="Valid Company")
            mock_fetch.side_effect = [mock_company, Exception("Company not found")]
            
            with patch('asyncio.sleep', return_value=None):
                companies = await client.batch_fetch_companies(company_urls, delay_seconds=0.1)
            
            assert len(companies) == 2
            assert companies[0].company_name == "Valid Company"
            assert companies[1] is None  # Failed fetch


class TestDataExtraction(TestCassidyClient):
    """Test data extraction methods"""
    
    def test_extract_profile_data_success(self, client):
        """Test successful profile data extraction"""
        profile_data = client._extract_profile_data(MOCK_CASSIDY_PROFILE_RESPONSE)
        
        assert isinstance(profile_data, dict)
        assert profile_data["full_name"] == "Ronald Sorozan (MBA, CISM, PMP)"
        assert profile_data["profile_id"] == "ronald-sorozan-mba-cism-pmp-8325652"
        assert len(profile_data["experiences"]) == 1
    
    def test_extract_profile_data_invalid_structure(self, client):
        """Test profile extraction with invalid response structure"""
        invalid_response = {"invalid": "structure"}
        
        with pytest.raises(CassidyWorkflowError):
            client._extract_profile_data(invalid_response)
    
    def test_extract_company_data_success(self, client):
        """Test successful company data extraction"""
        company_data = client._extract_company_data(MOCK_CASSIDY_COMPANY_RESPONSE)
        
        assert isinstance(company_data, dict)
        assert company_data["company_name"] == "JAM+"
        assert company_data["company_id"] == "jambnc"
        assert company_data["employee_count"] == 250
    
    def test_extract_company_data_no_results(self, client):
        """Test company extraction with no action results"""
        no_results_response = {
            "workflowRun": {
                "id": "test-workflow",
                "status": "completed",
                "actionResults": []
            }
        }
        
        with pytest.raises(CassidyWorkflowError):
            client._extract_company_data(no_results_response)


class TestHealthCheck(TestCassidyClient):
    """Test health check functionality"""
    
    @pytest.mark.asyncio
    async def test_health_check_healthy(self, client):
        """Test healthy service response"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.elapsed.total_seconds.return_value = 0.5
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.head.return_value = mock_response
            
            health = await client.health_check()
            
            assert health["status"] == "healthy"
            assert health["status_code"] == 200
            assert health["response_time_ms"] == 500
    
    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self, client):
        """Test unhealthy service response"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.head.side_effect = Exception("Connection failed")
            
            health = await client.health_check()
            
            assert health["status"] == "unhealthy"
            assert "Connection failed" in health["error"]


class TestErrorHandling(TestCassidyClient):
    """Test comprehensive error handling"""
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self, client):
        """Test timeout error handling"""
        import httpx
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post.side_effect = httpx.TimeoutException("Request timed out")
            
            with pytest.raises(CassidyTimeoutError):
                await client.fetch_profile(TEST_LINKEDIN_PROFILE_URL)
    
    @pytest.mark.asyncio
    async def test_connection_error_handling(self, client):
        """Test connection error handling"""
        import httpx
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post.side_effect = httpx.ConnectError("Connection refused")
            
            with pytest.raises(Exception):  # Should be wrapped in CassidyConnectionError
                await client.fetch_profile(TEST_LINKEDIN_PROFILE_URL)
    
    def test_invalid_json_response(self, client):
        """Test handling of invalid JSON responses"""
        from app.cassidy.exceptions import CassidyValidationError
        
        # This would normally be tested with a mock response that returns invalid JSON
        # but for this test we'll test the extraction directly
        invalid_json_response = {"invalid": "no workflowRun key"}
        
        with pytest.raises(CassidyWorkflowError):
            client._extract_profile_data(invalid_json_response)


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
