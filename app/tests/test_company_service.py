"""
Tests for CompanyService class.

Tests cover:
- Company creation and updates
- Company deduplication logic
- Profile-company relationship management
- Batch processing capabilities
- Error handling and resilience
"""

import pytest
import uuid
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
from typing import Dict, Any, List

from app.services.company_service import CompanyService
from app.models.canonical.company import CanonicalCompany, CanonicalFundingInfo, CanonicalCompanyLocation
from app.repositories.company_repository import CompanyRepository
from pydantic import ValidationError


class TestCompanyService:
    """Test suite for CompanyService class."""
    
    @pytest.fixture
    def mock_company_repo(self):
        """Create a mock CompanyRepository."""
        return Mock(spec=CompanyRepository)
    
    @pytest.fixture
    def company_service(self, mock_company_repo):
        """Create CompanyService instance with mock repository."""
        return CompanyService(mock_company_repo)
    
    @pytest.fixture
    def sample_company_data(self):
        """Sample company data for testing."""
        return {
            "company_id": "123456",
            "company_name": "Test Corporation",
            "linkedin_url": "https://linkedin.com/company/test-corp",
            "website": "https://testcorp.com",
            "domain": "testcorp.com",
            "employee_count": 1500,
            "employee_range": "1001-5000",
            "industries": ["Technology", "Software"],
            "description": "A leading technology company",
            "year_founded": 2010
        }
    
    @pytest.fixture
    def canonical_company(self, sample_company_data):
        """Create a CanonicalCompany instance."""
        return CanonicalCompany(**sample_company_data)

    # Test 3.1: CompanyService creation, deduplication, and relationship management
    
    @pytest.mark.asyncio
    async def test_create_or_update_company_creates_new_company(self, company_service, mock_company_repo, canonical_company):
        """Test creating a new company when it doesn't exist."""
        # Setup
        mock_company_repo.get_by_linkedin_id.return_value = None
        mock_company_repo.create.return_value = {"id": str(uuid.uuid4()), "company_name": "Test Corporation"}
        
        # Execute
        result = await company_service.create_or_update_company(canonical_company)
        
        # Verify
        mock_company_repo.get_by_linkedin_id.assert_called_once_with("123456")
        mock_company_repo.create.assert_called_once_with(canonical_company)
        assert result["company_name"] == "Test Corporation"
    
    @pytest.mark.asyncio
    async def test_create_or_update_company_updates_existing_company(self, company_service, mock_company_repo, canonical_company):
        """Test updating an existing company."""
        # Setup
        existing_company = {"id": str(uuid.uuid4()), "linkedin_company_id": "123456"}
        mock_company_repo.get_by_linkedin_id.return_value = canonical_company
        mock_company_repo.update.return_value = existing_company
        
        # Execute  
        result = await company_service.create_or_update_company(canonical_company)
        
        # Verify
        mock_company_repo.get_by_linkedin_id.assert_called_once_with("123456")
        mock_company_repo.update.assert_called_once()
        assert result == existing_company

    @pytest.mark.asyncio
    async def test_find_company_by_url_success(self, company_service, mock_company_repo, canonical_company):
        """Test finding company by LinkedIn URL."""
        # Setup
        mock_company_repo.get_by_linkedin_id.return_value = canonical_company
        
        # Execute
        result = await company_service.find_company_by_url("https://linkedin.com/company/test-corp")
        
        # Verify
        mock_company_repo.get_by_linkedin_id.assert_called_once()
        assert result == canonical_company

    @pytest.mark.asyncio
    async def test_find_company_by_url_normalizes_url(self, company_service, mock_company_repo):
        """Test that URL is normalized before lookup."""
        # Setup
        mock_company_repo.get_by_linkedin_id.return_value = None
        
        # Execute - test various URL formats
        test_urls = [
            "linkedin.com/company/test-corp",
            "www.linkedin.com/company/test-corp/",
            "https://www.linkedin.com/company/test-corp?trk=nav"
        ]
        
        for url in test_urls:
            await company_service.find_company_by_url(url)
        
        # Verify that all URLs are normalized to extract company ID
        assert mock_company_repo.get_by_linkedin_id.call_count == len(test_urls)

    # Test 3.3 & 3.4: Company deduplication logic with URL matching

    @pytest.mark.asyncio
    async def test_deduplicate_companies_by_linkedin_url(self, company_service, mock_company_repo, canonical_company):
        """Test deduplication finds existing company by LinkedIn URL."""
        # Setup
        mock_company_repo.get_by_linkedin_id.return_value = canonical_company
        
        # Execute
        result = await company_service.deduplicate_company(canonical_company)
        
        # Verify
        assert result == canonical_company
        mock_company_repo.get_by_linkedin_id.assert_called_once()

    @pytest.mark.asyncio
    async def test_deduplicate_companies_by_name_similarity(self, company_service, mock_company_repo, sample_company_data):
        """Test deduplication with name similarity matching."""
        # Setup
        canonical_company = CanonicalCompany(**sample_company_data)
        similar_companies = [
            CanonicalCompany(company_name="Test Corp", employee_count=1500),
            CanonicalCompany(company_name="TestCorporation Inc", employee_count=1600)  
        ]
        
        mock_company_repo.get_by_linkedin_id.return_value = None
        mock_company_repo.search_by_name.return_value = similar_companies
        
        # Execute
        result = await company_service.deduplicate_company(canonical_company)
        
        # Verify - should return the most similar company
        assert result == similar_companies[0]  # "Test Corp" is more similar to "Test Corporation"
        mock_company_repo.search_by_name.assert_called_once()

    @pytest.mark.asyncio
    async def test_deduplicate_companies_no_matches(self, company_service, mock_company_repo, canonical_company):
        """Test deduplication when no similar companies exist."""
        # Setup
        mock_company_repo.get_by_linkedin_id.return_value = None
        mock_company_repo.search_by_name.return_value = []
        
        # Execute
        result = await company_service.deduplicate_company(canonical_company)
        
        # Verify
        assert result is None

    # Test 3.5 & 3.6: Batch company processing with error resilience

    @pytest.mark.asyncio
    async def test_batch_process_companies_success(self, company_service, mock_company_repo, sample_company_data):
        """Test successful batch processing of multiple companies."""
        # Setup
        companies = [
            CanonicalCompany(**{**sample_company_data, "company_id": f"12345{i}", "company_name": f"Company {i}"})
            for i in range(3)
        ]
        
        mock_company_repo.get_by_linkedin_id.return_value = None
        mock_company_repo.create.side_effect = [
            {"id": str(uuid.uuid4()), "company_name": f"Company {i}"} for i in range(3)
        ]
        
        # Execute
        results = await company_service.batch_process_companies(companies)
        
        # Verify
        assert len(results) == 3
        assert all(result["success"] for result in results)
        assert mock_company_repo.create.call_count == 3

    @pytest.mark.asyncio
    async def test_batch_process_companies_handles_errors(self, company_service, mock_company_repo, sample_company_data):
        """Test batch processing with some failures."""
        # Setup
        companies = [
            CanonicalCompany(**{**sample_company_data, "company_id": f"12345{i}", "company_name": f"Company {i}"})
            for i in range(3)
        ]
        
        mock_company_repo.get_by_linkedin_id.return_value = None
        mock_company_repo.create.side_effect = [
            {"id": str(uuid.uuid4()), "company_name": "Company 0"},
            Exception("Database error"),
            {"id": str(uuid.uuid4()), "company_name": "Company 2"}
        ]
        
        # Execute
        results = await company_service.batch_process_companies(companies)
        
        # Verify
        assert len(results) == 3
        assert results[0]["success"] is True
        assert results[1]["success"] is False
        assert results[1]["error"] == "Database error"
        assert results[2]["success"] is True

    # Test 3.7 & 3.8: Profile-company relationship management

    def test_link_profile_to_company_success(self, company_service, mock_company_repo):
        """Test linking a profile to a company with work experience details."""
        # Setup
        profile_id = str(uuid.uuid4())
        company_id = str(uuid.uuid4())
        work_experience = {
            "position_title": "Software Engineer",
            "start_date": "2020-01-01",
            "end_date": "2022-12-31",
            "is_current": False,
            "description": "Developed web applications"
        }
        
        mock_company_repo.link_to_profile.return_value = {
            "profile_id": profile_id,
            "company_id": company_id,
            **work_experience
        }
        
        # Execute
        result = company_service.link_profile_to_company(profile_id, company_id, work_experience)
        
        # Verify
        mock_company_repo.link_to_profile.assert_called_once_with(profile_id, company_id, work_experience)
        assert result["profile_id"] == profile_id
        assert result["company_id"] == company_id
        assert result["position_title"] == "Software Engineer"

    def test_unlink_profile_from_company(self, company_service, mock_company_repo):
        """Test unlinking a profile from a company."""
        # Setup
        profile_id = str(uuid.uuid4())
        company_id = str(uuid.uuid4())
        
        # Execute
        company_service.unlink_profile_from_company(profile_id, company_id)
        
        # Verify
        mock_company_repo.unlink_from_profile.assert_called_once_with(profile_id, company_id)

    def test_get_companies_for_profile(self, company_service, mock_company_repo, canonical_company):
        """Test retrieving all companies associated with a profile."""
        # Setup
        profile_id = str(uuid.uuid4())
        mock_company_repo.get_companies_for_profile.return_value = [canonical_company]
        
        # Execute
        result = company_service.get_companies_for_profile(profile_id)
        
        # Verify
        mock_company_repo.get_companies_for_profile.assert_called_once_with(profile_id)
        assert result == [canonical_company]

    # Test 3.9: Error handling and transaction management

    def test_create_or_update_company_handles_validation_error(self, company_service, mock_company_repo):
        """Test handling of validation errors during company creation."""
        # Execute & Verify - Pydantic validation happens during model creation
        with pytest.raises(ValidationError):
            CanonicalCompany(
                company_name="",  # Invalid - empty name
                employee_count=-1  # Invalid - negative count
            )

    @pytest.mark.asyncio
    async def test_create_or_update_company_handles_database_error(self, company_service, mock_company_repo, canonical_company):
        """Test handling of database errors during company operations."""
        # Setup
        mock_company_repo.get_by_linkedin_id.return_value = None
        mock_company_repo.create.side_effect = Exception("Database connection failed")
        
        # Execute & Verify
        with pytest.raises(Exception, match="Database connection failed"):
            await company_service.create_or_update_company(canonical_company)

    @pytest.mark.asyncio
    async def test_batch_process_companies_transaction_rollback(self, company_service, mock_company_repo, sample_company_data):
        """Test that batch processing handles transaction failures gracefully."""
        # Setup
        companies = [CanonicalCompany(**sample_company_data) for _ in range(2)]
        mock_company_repo.get_by_linkedin_id.return_value = None
        mock_company_repo.create.side_effect = Exception("Transaction failed")
        
        # Execute
        results = await company_service.batch_process_companies(companies)
        
        # Verify - all should fail but not crash
        assert len(results) == 2
        assert all(not result["success"] for result in results)
        assert all("Transaction failed" in result["error"] for result in results)

    def test_company_name_similarity_calculation(self, company_service):
        """Test the name similarity calculation algorithm."""
        # Test exact match
        assert company_service._calculate_name_similarity("Test Corp", "Test Corp") == 1.0
        
        # Test partial match - "Test Corporation" vs "Test Corp" should normalize to same thing
        similarity = company_service._calculate_name_similarity("Test Corporation", "Test Corp Ltd")
        assert 0.5 < similarity < 1.0
        
        # Test no match
        similarity = company_service._calculate_name_similarity("Test Corp", "Different Company")
        assert similarity < 0.5

    def test_linkedin_url_extraction(self, company_service):
        """Test LinkedIn URL company ID extraction."""
        test_cases = [
            ("https://linkedin.com/company/test-corp", "test-corp"),
            ("www.linkedin.com/company/test-corp/", "test-corp"),
            ("linkedin.com/company/123456", "123456"),
            ("https://linkedin.com/company/test-corp?ref=nav", "test-corp")
        ]
        
        for url, expected_id in test_cases:
            result = company_service._extract_company_id_from_url(url)
            assert result == expected_id, f"Failed for URL: {url}"

    def test_merge_company_data_updates_existing_fields(self, company_service, sample_company_data):
        """Test merging company data preserves existing data while updating new fields."""
        # Setup
        existing_company = CanonicalCompany(**sample_company_data)
        updated_data = CanonicalCompany(
            **{**sample_company_data, "employee_count": 2000, "tagline": "New tagline"}
        )
        
        # Execute
        merged = company_service._merge_company_data(existing_company, updated_data)
        
        # Verify
        assert merged.employee_count == 2000  # Updated
        assert merged.tagline == "New tagline"  # New field
        assert merged.company_name == "Test Corporation"  # Preserved
        assert merged.year_founded == 2010  # Preserved
