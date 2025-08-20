# Tests Specification

This is the tests coverage details for the spec detailed in @agent-os/specs/2025-08-20-v2.1-company-model-backend/spec.md

> Created: 2025-08-20
> Version: 1.0.0

## Test Coverage

### Unit Tests

**CanonicalCompany Model**
- Validate required fields (name must be non-empty)
- Validate optional fields (employee_count, linkedin_company_url)
- Validate data types (employee_count as integer, industries as list)
- Validate JSONB field serialization (locations, funding_info)
- Test field constraints (employee_count >= 0)

**Company Database Model**
- Test CRUD operations (create, read, update, delete)
- Validate unique constraints (linkedin_company_url uniqueness)
- Test database relationships (profile-company junction table)
- Validate database constraints (non-negative employee_count, non-empty name)
- Test index effectiveness for query performance

**CompanyService**
- Test company creation with valid data
- Test company creation with invalid data (error handling)
- Test company deduplication by LinkedIn URL
- Test company update operations
- Test profile-company relationship creation
- Test batch company operations during profile ingestion

**Profile-Company Relationship Model**
- Test work experience relationship creation
- Validate date consistency constraints (start_date <= end_date)
- Test unique relationship constraints prevention
- Test cascade deletion behavior
- Test current position flag functionality

### Integration Tests

**Enhanced Profile API Endpoints**
- GET /profiles/{id} without company data (default behavior)
- GET /profiles/{id} with include_companies=true
- GET /profiles list endpoint with company inclusion
- Test profile response format with embedded company objects
- Verify backward compatibility (existing responses unchanged)

**New Company API Endpoints**
- GET /companies/{id} for existing company
- GET /companies/{id} for non-existent company (404 error)
- GET /companies search with various filters
- GET /companies/{id}/profiles endpoint
- Test pagination on company search and profile listing

**Profile Ingestion with Company Data**
- Test complete profile ingestion flow with company data extraction
- Verify company creation during profile processing
- Test company deduplication during batch ingestion
- Test profile-company relationship establishment
- Test error handling when company data is malformed

**Database Integration**
- Test database migration execution (up and down)
- Verify all indexes are created correctly
- Test foreign key constraint enforcement
- Verify JSONB field storage and retrieval
- Test concurrent access and transaction handling

### Feature Tests

**End-to-End Company Data Flow**
- Ingest profile with multiple work experiences → verify companies created → retrieve profile with company data → validate complete company information
- Profile ingestion with duplicate companies → verify single company record → multiple profiles linked to same company
- Company update during re-ingestion → verify existing company enhanced with new data → profile relationships preserved

**Scoring Integration with Company Context**
- Score profile with company context disabled → verify basic scoring
- Score profile with company context enabled → verify rich company data included in prompt
- Compare scoring results with and without company context → validate scoring improvements
- Test scoring with profiles having multiple company experiences

**API Response Performance**
- Profile retrieval without company data → measure response time baseline
- Profile retrieval with company data → verify acceptable performance impact
- Large profile list with company data → test pagination and response sizes
- Concurrent API requests with company data inclusion

### Mocking Requirements

**Cassidy API Integration**
- Mock Cassidy company data responses with realistic company information
- Mock various company data formats (complete data, partial data, missing fields)
- Mock Cassidy error scenarios (company not found, API timeout)
- Mock company data extraction from profile work experience sections

**Database Operations**
- Mock database connection failures during company operations
- Mock unique constraint violations during company creation
- Mock foreign key constraint violations during relationship creation
- Mock transaction rollback scenarios during batch company processing

**External Service Dependencies**
- Mock LinkedIn company URL validation
- Mock industry classification lookups
- Mock geographic location data processing
- Mock employee count range calculations

## Test Data Requirements

### Sample Company Data
```json
{
  "large_enterprise": {
    "name": "PricewaterhouseCoopers",
    "linkedin_company_url": "https://linkedin.com/company/pwc",
    "employee_count": 284478,
    "employee_range": "10001+",
    "industries": ["Professional Services", "Consulting"],
    "specialties": "Assurance, Tax, Advisory, Consulting",
    "funding_info": null,
    "locations": [
      {"country": "United States", "city": "New York", "region": "NY"}
    ],
    "description": "Building trust in society and solving important problems."
  },
  "startup": {
    "name": "TechStartup Inc",
    "linkedin_company_url": "https://linkedin.com/company/techstartup",
    "employee_count": 45,
    "employee_range": "11-50", 
    "industries": ["Technology", "Software"],
    "specialties": "AI, Machine Learning, Data Analytics",
    "funding_info": {
      "total_funding": "$15M",
      "last_round": "Series A",
      "investors": ["Venture Capital Firm"]
    },
    "locations": [
      {"country": "United States", "city": "San Francisco", "region": "CA"}
    ],
    "description": "Innovative AI solutions for modern businesses."
  }
}
```

### Profile Test Data with Work Experience
```json
{
  "multi_company_executive": {
    "linkedin_profile_url": "https://linkedin.com/in/executive",
    "full_name": "Senior Executive",
    "work_experience": [
      {
        "position_title": "Chief Technology Officer",
        "company_name": "PricewaterhouseCoopers",
        "company_linkedin_url": "https://linkedin.com/company/pwc",
        "start_date": "2020-01-01",
        "end_date": null,
        "is_current": true
      },
      {
        "position_title": "VP of Engineering", 
        "company_name": "TechStartup Inc",
        "company_linkedin_url": "https://linkedin.com/company/techstartup",
        "start_date": "2018-01-01",
        "end_date": "2019-12-31",
        "is_current": false
      }
    ]
  }
}
```

## Performance Testing

### Load Testing Scenarios
- **Profile Ingestion with Companies**: Test ingestion of 100 profiles with 2-5 companies each
- **Company Data Retrieval**: Test simultaneous retrieval of 50 profiles with full company data
- **Company Search Performance**: Test company search with various filter combinations
- **Database Query Optimization**: Measure join query performance for profile+company data

### Memory and Resource Testing
- **Large Company Objects**: Test handling of companies with extensive location and funding data
- **Batch Company Processing**: Test memory usage during large batch company creation
- **JSONB Field Performance**: Measure query performance on industries and locations fields
- **Connection Pool Utilization**: Test database connection usage under load

## Error Scenarios Testing

### Data Validation Errors
- Company creation with negative employee count → validate proper error response
- Company creation with empty name → validate constraint enforcement
- Work experience with invalid date range → validate date consistency checks
- Profile-company linking with non-existent IDs → validate foreign key enforcement

### API Error Handling
- Profile retrieval with include_companies for deleted companies → graceful degradation
- Company search with invalid parameters → proper error messages
- Concurrent company updates → test optimistic locking
- Large response size limits → test response truncation and pagination

### Integration Error Recovery
- Profile ingestion with partial company data → verify profile creation success despite company issues
- Database connection loss during company operations → verify transaction rollback
- Cassidy API timeout during company data extraction → verify graceful error handling
- Company deduplication conflicts → verify conflict resolution strategies

## Regression Testing

### Backward Compatibility Tests
- Verify all existing profile API responses remain unchanged when include_companies=false
- Test existing profile ingestion flow continues working without company enhancements
- Validate existing scoring functionality unaffected by company integration
- Confirm no performance degradation in basic profile operations

### Database Migration Testing
- Test migration execution on empty database
- Test migration execution on database with existing profile data
- Test migration rollback functionality
- Verify data integrity after migration completion

### API Version Compatibility
- Test API responses match documented schemas
- Verify optional parameter behavior (include_companies defaults to false)
- Test new endpoints don't conflict with existing routes
- Validate error response format consistency

## Test Environment Setup

### Database Testing Setup
```sql
-- Test database with sample data
CREATE DATABASE linkedin_ingestion_test;

-- Populate with representative profile and company data
INSERT INTO profiles (id, linkedin_profile_url, full_name, work_experience) VALUES...
INSERT INTO companies (id, name, linkedin_company_url, employee_count) VALUES...
INSERT INTO profile_companies (profile_id, company_id, position_title) VALUES...
```

### Mock Service Configuration
```python
# Mock Cassidy responses for company data
@pytest.fixture
def mock_cassidy_company_response():
    return {
        "company_name": "PricewaterhouseCoopers",
        "employee_count": 284478,
        "employee_range": "10001+",
        "industries": ["Professional Services"],
        "specialties": "Assurance, Tax, Advisory, Consulting"
    }

# Mock database operations for isolated testing
@pytest.fixture 
def mock_company_service():
    service = Mock(spec=CompanyService)
    service.create_or_update_company.return_value = sample_company
    return service
```

## Success Criteria

### Test Coverage Metrics
- **Unit Test Coverage**: Minimum 95% line coverage for new company-related code
- **Integration Test Coverage**: All new API endpoints covered with positive and negative test cases
- **Feature Test Coverage**: Complete end-to-end workflows tested with realistic data

### Performance Benchmarks
- **Profile with Company Data Retrieval**: Less than 200ms response time for single profile
- **Company Search**: Less than 500ms response time for filtered company searches
- **Profile Ingestion**: Less than 2 seconds for profile with 5 companies
- **Database Queries**: All company-related queries under 100ms execution time

### Quality Standards
- **Zero Test Failures**: All tests pass consistently in CI/CD environment
- **Error Handling**: All error scenarios produce appropriate user-facing messages
- **Data Integrity**: No data corruption during concurrent operations
- **Backward Compatibility**: No breaking changes to existing API behavior
