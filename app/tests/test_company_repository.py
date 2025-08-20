"""
Tests for the CompanyRepository class.

This test suite covers database operations for the CanonicalCompany model including:
- CRUD operations (create, read, update, delete)
- Search and filtering operations  
- Data transformation between model and database formats
- Error handling and edge cases
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, ANY
from datetime import datetime, timezone
import uuid

from app.repositories.company_repository import CompanyRepository
from app.models.canonical.company import CanonicalCompany, CanonicalFundingInfo, CanonicalCompanyLocation


# --- Test Data Fixtures ---

@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client for testing."""
    client = Mock()
    client.table = Mock()
    client.rpc = Mock()
    return client

@pytest.fixture  
def company_repository(mock_supabase_client):
    """CompanyRepository instance with mocked Supabase client."""
    return CompanyRepository(mock_supabase_client)

@pytest.fixture
def sample_company():
    """Sample CanonicalCompany instance for testing."""
    return CanonicalCompany(
        company_id="123456",
        company_name="Test Company Inc",
        website="https://testcompany.com",
        domain="testcompany.com",
        employee_count=150,
        year_founded=2010,
        industries=["Technology", "Software"],
        hq_city="San Francisco",
        hq_country="United States",
        email="contact@testcompany.com",
        funding_info={
            "last_funding_round_type": "Series A",
            "last_funding_round_amount": "$10M",
            "last_funding_round_year": 2022
        }
    )

@pytest.fixture
def sample_db_row():
    """Sample database row data."""
    return {
        "id": str(uuid.uuid4()),
        "linkedin_company_id": "123456", 
        "company_name": "Test Company Inc",
        "description": "A test company",
        "website": "https://testcompany.com",
        "domain": "testcompany.com", 
        "employee_count": 150,
        "year_founded": 2010,
        "industries": ["Technology", "Software"],
        "hq_city": "San Francisco",
        "hq_country": "United States",
        "email": "contact@testcompany.com",
        "funding_info": {
            "last_funding_round_type": "Series A",
            "last_funding_round_amount": "$10M", 
            "last_funding_round_year": 2022
        },
        "locations": [],
        "affiliated_companies": [],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }


# --- Repository Creation Tests ---

def test_repository_initialization(mock_supabase_client):
    """Test CompanyRepository initialization."""
    repo = CompanyRepository(mock_supabase_client)
    assert repo.client == mock_supabase_client
    assert repo.table_name == "companies"


# --- CRUD Operation Tests ---

def test_create_company_success(company_repository, sample_company):
    """Test successful company creation."""
    # Mock successful database response
    mock_result = Mock()
    mock_result.data = [{"id": str(uuid.uuid4()), "company_name": "Test Company Inc"}]
    
    company_repository.client.table.return_value.insert.return_value.execute.return_value = mock_result
    
    # Test creation
    result = company_repository.create(sample_company)
    
    # Verify result
    assert result["company_name"] == "Test Company Inc"
    
    # Verify database calls
    company_repository.client.table.assert_called_with("companies")
    company_repository.client.table.return_value.insert.assert_called_once()

def test_create_company_failure(company_repository, sample_company):
    """Test company creation failure."""
    # Mock failed database response
    mock_result = Mock()
    mock_result.data = None
    
    company_repository.client.table.return_value.insert.return_value.execute.return_value = mock_result
    
    # Test creation failure
    with pytest.raises(Exception, match="Failed to create company record"):
        company_repository.create(sample_company)

def test_get_by_id_success(company_repository, sample_db_row):
    """Test successful get by ID."""
    # Mock successful database response
    mock_result = Mock()
    mock_result.data = [sample_db_row]
    
    company_repository.client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result
    
    # Test get by ID
    company_id = sample_db_row["id"]
    result = company_repository.get_by_id(company_id)
    
    # Verify result
    assert result is not None
    assert isinstance(result, CanonicalCompany)
    assert result.company_name == "Test Company Inc"
    
    # Verify database calls
    company_repository.client.table.return_value.select.assert_called_with("*")
    company_repository.client.table.return_value.select.return_value.eq.assert_called_with("id", company_id)

def test_get_by_id_not_found(company_repository):
    """Test get by ID when record not found."""
    # Mock empty database response
    mock_result = Mock()
    mock_result.data = []
    
    company_repository.client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result
    
    # Test get by ID
    result = company_repository.get_by_id("nonexistent-id")
    
    # Verify result
    assert result is None

def test_get_by_linkedin_id_success(company_repository, sample_db_row):
    """Test successful get by LinkedIn ID."""
    # Mock successful database response
    mock_result = Mock()
    mock_result.data = [sample_db_row]
    
    company_repository.client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result
    
    # Test get by LinkedIn ID
    result = company_repository.get_by_linkedin_id("123456")
    
    # Verify result
    assert result is not None
    assert isinstance(result, CanonicalCompany)
    assert result.company_id == "123456"

def test_update_company_success(company_repository, sample_company):
    """Test successful company update."""
    # Mock successful database response
    mock_result = Mock()
    mock_result.data = [{"id": str(uuid.uuid4()), "company_name": "Test Company Inc"}]
    
    company_repository.client.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_result
    
    # Test update
    company_id = str(uuid.uuid4())
    result = company_repository.update(company_id, sample_company)
    
    # Verify result
    assert result["company_name"] == "Test Company Inc"
    
    # Verify database calls
    company_repository.client.table.return_value.update.assert_called_once()

def test_upsert_by_linkedin_id_success(company_repository, sample_company):
    """Test successful upsert by LinkedIn ID."""
    # Mock successful database response
    mock_result = Mock()
    mock_result.data = [{"id": str(uuid.uuid4()), "company_name": "Test Company Inc"}]
    
    company_repository.client.table.return_value.upsert.return_value.execute.return_value = mock_result
    
    # Test upsert
    result = company_repository.upsert_by_linkedin_id(sample_company)
    
    # Verify result
    assert result["company_name"] == "Test Company Inc"
    
    # Verify database calls
    company_repository.client.table.return_value.upsert.assert_called_with(
        ANY, on_conflict="linkedin_company_id"
    )

def test_delete_company_success(company_repository):
    """Test successful company deletion."""
    # Mock successful database response
    mock_result = Mock()
    mock_result.data = [{"id": str(uuid.uuid4())}]
    
    company_repository.client.table.return_value.delete.return_value.eq.return_value.execute.return_value = mock_result
    
    # Test deletion
    company_id = str(uuid.uuid4())
    result = company_repository.delete(company_id)
    
    # Verify result
    assert result is True
    
    # Verify database calls
    company_repository.client.table.return_value.delete.return_value.eq.assert_called_with("id", company_id)


# --- Search and Query Tests ---

def test_search_by_name_success(company_repository, sample_db_row):
    """Test successful search by name."""
    # Mock successful database response
    mock_result = Mock()
    mock_result.data = [sample_db_row]
    
    company_repository.client.table.return_value.select.return_value.ilike.return_value.limit.return_value.execute.return_value = mock_result
    
    # Test search
    results = company_repository.search_by_name("Test Company")
    
    # Verify results
    assert len(results) == 1
    assert isinstance(results[0], CanonicalCompany)
    assert results[0].company_name == "Test Company Inc"
    
    # Verify database calls
    company_repository.client.table.return_value.select.return_value.ilike.assert_called_with(
        "company_name", "%Test Company%"
    )

def test_search_by_domain_exact_match(company_repository, sample_db_row):
    """Test search by domain with exact match."""
    # Mock successful database response
    mock_result = Mock()
    mock_result.data = [sample_db_row]
    
    company_repository.client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = mock_result
    
    # Test exact domain search
    results = company_repository.search_by_domain("testcompany.com", exact_match=True)
    
    # Verify results
    assert len(results) == 1
    assert isinstance(results[0], CanonicalCompany)
    
    # Verify database calls
    company_repository.client.table.return_value.select.return_value.eq.assert_called_with(
        "domain", "testcompany.com"
    )

def test_search_by_domain_partial_match(company_repository, sample_db_row):
    """Test search by domain with partial match."""
    # Mock successful database response
    mock_result = Mock()
    mock_result.data = [sample_db_row]
    
    company_repository.client.table.return_value.select.return_value.ilike.return_value.limit.return_value.execute.return_value = mock_result
    
    # Test partial domain search
    results = company_repository.search_by_domain("testcompany", exact_match=False)
    
    # Verify results
    assert len(results) == 1
    
    # Verify database calls
    company_repository.client.table.return_value.select.return_value.ilike.assert_called_with(
        "domain", "%testcompany%"
    )

def test_get_companies_by_location(company_repository, sample_db_row):
    """Test get companies by location."""
    # Mock successful database response
    mock_result = Mock()
    mock_result.data = [sample_db_row]
    
    # Mock the chained calls properly for location search (uses ilike, not eq)
    mock_chain = Mock()
    mock_chain.select.return_value = mock_chain
    mock_chain.ilike.return_value = mock_chain  # Location search uses ilike
    mock_chain.limit.return_value = mock_chain
    mock_chain.execute.return_value = mock_result
    company_repository.client.table.return_value = mock_chain
    
    # Test location search
    results = company_repository.get_companies_by_location(city="San Francisco", country="United States")
    
    # Verify results
    assert len(results) == 1
    assert isinstance(results[0], CanonicalCompany)

def test_get_companies_by_industry(company_repository, sample_db_row):
    """Test get companies by industry."""
    # Mock successful database response
    mock_result = Mock()
    mock_result.data = [sample_db_row]
    
    company_repository.client.table.return_value.select.return_value.contains.return_value.limit.return_value.execute.return_value = mock_result
    
    # Test industry search
    results = company_repository.get_companies_by_industry("Technology")
    
    # Verify results
    assert len(results) == 1
    
    # Verify database calls
    company_repository.client.table.return_value.select.return_value.contains.assert_called_with(
        "industries", ["Technology"]
    )


# --- Advanced Query Tests ---

def test_get_companies_by_size_category_with_function(company_repository):
    """Test get companies by size category using database function."""
    # Mock successful database function response
    mock_result = Mock()
    mock_result.data = [
        {"id": str(uuid.uuid4()), "company_name": "Small Co", "employee_count": 25, "size_category": "Small"}
    ]
    
    company_repository.client.rpc.return_value.execute.return_value = mock_result
    
    # Test size category query
    results = company_repository.get_companies_by_size_category("small", limit=10)
    
    # Verify results
    assert len(results) == 1
    assert results[0]["size_category"] == "Small"
    
    # Verify database calls
    company_repository.client.rpc.assert_called_with("get_companies_by_size_category", {
        "category": "small",
        "limit_count": 10
    })

def test_get_companies_by_size_category_fallback(company_repository):
    """Test get companies by size category using fallback when function fails."""
    # Mock failed database function call
    company_repository.client.rpc.side_effect = Exception("Function not found")
    
    # Mock successful fallback query
    mock_result = Mock()
    mock_result.data = [
        {"id": str(uuid.uuid4()), "company_name": "Small Co", "employee_count": 25}
    ]
    
    company_repository.client.table.return_value.select.return_value.gte.return_value.lt.return_value.limit.return_value.execute.return_value = mock_result
    
    # Test size category query with fallback
    results = company_repository.get_companies_by_size_category("small", limit=10)
    
    # Verify results
    assert len(results) == 1
    assert results[0]["size_category"] == "Small"

def test_get_startup_companies_with_function(company_repository):
    """Test get startup companies using database function."""
    # Mock successful database function response
    mock_result = Mock()
    mock_result.data = [
        {
            "id": str(uuid.uuid4()),
            "company_name": "Startup Co", 
            "employee_count": 15,
            "year_founded": 2020,
            "company_age": 5,
            "has_funding": True,
            "domain": "startup.com"
        }
    ]
    
    company_repository.client.rpc.return_value.execute.return_value = mock_result
    
    # Test startup query
    results = company_repository.get_startup_companies(limit=10)
    
    # Verify results
    assert len(results) == 1
    assert results[0]["company_name"] == "Startup Co"
    assert results[0]["has_funding"] is True
    
    # Verify database calls
    company_repository.client.rpc.assert_called_with("get_startup_companies", {
        "limit_count": 10
    })

def test_vector_similarity_search_success(company_repository):
    """Test vector similarity search."""
    # Mock successful database function response
    mock_result = Mock()
    mock_result.data = [
        {
            "id": str(uuid.uuid4()),
            "company_name": "Similar Co",
            "similarity": 0.85
        }
    ]
    
    company_repository.client.rpc.return_value.execute.return_value = mock_result
    
    # Test vector search
    query_embedding = [0.1] * 1536  # Mock embedding
    results = company_repository.vector_similarity_search(query_embedding, threshold=0.8, limit=5)
    
    # Verify results
    assert len(results) == 1
    assert results[0]["similarity"] == 0.85
    
    # Verify database calls
    company_repository.client.rpc.assert_called_with("match_companies", {
        "query_embedding": query_embedding,
        "match_threshold": 0.8,
        "match_count": 5
    })


# --- Data Transformation Tests ---

def test_model_to_db_format(company_repository, sample_company):
    """Test conversion from CanonicalCompany model to database format."""
    db_data = company_repository._model_to_db_format(sample_company)
    
    # Verify core mappings
    assert db_data["linkedin_company_id"] == "123456"
    assert db_data["company_name"] == "Test Company Inc"
    assert db_data["website"] == "https://testcompany.com/"
    assert db_data["domain"] == "testcompany.com"
    assert db_data["employee_count"] == 150
    assert db_data["year_founded"] == 2010
    assert db_data["industries"] == ["Technology", "Software"]
    assert db_data["hq_city"] == "San Francisco"
    assert db_data["email"] == "contact@testcompany.com"
    
    # Verify JSONB fields
    assert db_data["funding_info"]["last_funding_round_type"] == "Series A"
    assert db_data["locations"] == []
    assert db_data["affiliated_companies"] == []
    
    # Verify computed fields are excluded
    assert "display_name" not in db_data
    assert "company_age" not in db_data
    assert "size_category" not in db_data

def test_model_to_db_format_update(company_repository, sample_company):
    """Test conversion for update operations includes updated_at."""
    db_data = company_repository._model_to_db_format(sample_company, is_update=True)
    
    # Verify update-specific fields
    assert "updated_at" in db_data
    assert db_data["updated_at"] is not None

def test_db_to_model_format(company_repository, sample_db_row):
    """Test conversion from database row to CanonicalCompany model."""
    company = company_repository._db_to_model_format(sample_db_row)
    
    # Verify model creation
    assert isinstance(company, CanonicalCompany)
    assert company.company_id == "123456"
    assert company.company_name == "Test Company Inc"
    assert company.website is not None
    assert str(company.website) == "https://testcompany.com/"
    assert company.domain == "testcompany.com"
    assert company.employee_count == 150
    assert company.industries == ["Technology", "Software"]
    
    # Verify nested model creation
    assert company.funding_info is not None
    assert company.funding_info.last_funding_round_type == "Series A"

def test_db_to_model_format_validation_error(company_repository):
    """Test handling of validation errors during model conversion."""
    # Create invalid database row (missing required field)
    invalid_row = {"id": str(uuid.uuid4())}  # Missing company_name
    
    # Test validation error handling
    with pytest.raises(Exception):  # ValidationError wrapped in generic Exception
        company_repository._db_to_model_format(invalid_row)


# --- Error Handling Tests ---

def test_create_company_database_error(company_repository, sample_company):
    """Test handling of database errors during creation."""
    # Mock database error
    company_repository.client.table.return_value.insert.return_value.execute.side_effect = Exception("Database error")
    
    # Test error handling - the actual exception should be re-raised as-is
    with pytest.raises(Exception, match="Database error"):
        company_repository.create(sample_company)

def test_search_by_name_database_error(company_repository):
    """Test handling of database errors during search."""
    # Mock database error
    company_repository.client.table.return_value.select.return_value.ilike.return_value.limit.return_value.execute.side_effect = Exception("Database error")
    
    # Test error handling (should return empty list)
    results = company_repository.search_by_name("Test")
    assert results == []

def test_vector_similarity_search_database_error(company_repository):
    """Test handling of database errors during vector search."""
    # Mock database error
    company_repository.client.rpc.side_effect = Exception("Database error")
    
    # Test error handling (should return empty list)
    results = company_repository.vector_similarity_search([0.1] * 1536)
    assert results == []


# --- Edge Cases and Boundary Tests ---

def test_empty_search_results(company_repository):
    """Test handling of empty search results."""
    # Mock empty database response
    mock_result = Mock()
    mock_result.data = []
    
    company_repository.client.table.return_value.select.return_value.ilike.return_value.limit.return_value.execute.return_value = mock_result
    
    # Test empty results
    results = company_repository.search_by_name("NonexistentCompany")
    assert results == []

def test_model_with_minimal_data():
    """Test model conversion with minimal required data only."""
    minimal_company = CanonicalCompany(company_name="Minimal Co")
    
    # Test that minimal company can be created and converted
    assert minimal_company.company_name == "Minimal Co"
    assert minimal_company.industries == []
    assert minimal_company.locations == []

def test_model_with_none_values(company_repository):
    """Test handling of None values in model conversion."""
    db_row = {
        "linkedin_company_id": None,
        "company_name": "Test Co",
        "description": None,
        "website": None,
        "employee_count": None,
        "industries": [],
        "locations": [],
        "affiliated_companies": []
    }
    
    # Test conversion with None values
    company = company_repository._db_to_model_format(db_row)
    assert company.company_name == "Test Co"
    assert company.company_id is None
    assert company.description is None
