# Tests Specification

This is the tests coverage details for the spec detailed in @agent-os/specs/2025-07-25-rest-api-refactor/spec.md

> Created: 2025-07-25
> Version: 1.0.0

## Test Coverage

### Unit Tests

**ProfileController**
- Test list_profiles with various query parameter combinations
- Test list_profiles pagination logic (limit/offset handling)
- Test get_profile with valid and invalid profile IDs
- Test create_profile with valid and invalid data
- Test authentication validation for all methods
- Test error response formatting consistency


**ProfileService** (business logic layer)
- Test profile filtering by LinkedIn URL (exact match)
- Test profile filtering by company name (partial match)
- Test profile filtering by person name (partial match)
- Test profile creation with duplicate LinkedIn URL handling
- Test pagination calculation logic
- Test profile retrieval by ID

**Authentication Middleware**
- Test API key validation logic
- Test unauthorized access handling
- Test malformed API key handling

### Integration Tests

**New REST Endpoints**
- Test GET /api/v1/profiles with no filters returns all profiles
- Test GET /api/v1/profiles with linkedin_url filter returns exact match
- Test GET /api/v1/profiles with company filter returns partial matches
- Test GET /api/v1/profiles with name filter returns partial matches
- Test GET /api/v1/profiles with pagination parameters
- Test GET /api/v1/profiles/{id} with valid profile ID
- Test GET /api/v1/profiles/{id} with invalid profile ID returns 404
- Test POST /api/v1/profiles creates new profile successfully
- Test POST /api/v1/profiles with duplicate LinkedIn URL returns 409

**Authentication Integration**
- Test all endpoints reject requests without API key
- Test all endpoints reject requests with invalid API key
- Test all endpoints accept requests with valid API key

### Feature Tests

**LinkedIn URL Search Workflow**
- Test end-to-end scenario: ingest profile, search by LinkedIn URL, retrieve full profile
- Test search returns empty result when LinkedIn URL not found
- Test search with URL encoding variations

**Make.com Integration Workflow**
- Test that Make.com can successfully call new GET /api/v1/profiles with linkedin_url parameter
- Test that response format allows Make.com to extract required profile data
- Test that updated Make.com integration works with new REST endpoints

**API Consistency Workflow**
- Test that all endpoints return consistent error response format
- Test that all endpoints use same authentication mechanism
- Test that all successful responses include required fields

### Mocking Requirements

**External Services:**
- No external service mocking required (internal API refactor only)

**Database Mocking:**
- **Profile Database:** Mock profile creation, retrieval, and filtering operations
- **Strategy:** Use in-memory SQLite or test database with controlled fixtures

**Authentication Mocking:**
- **API Key Validation:** Mock authentication service responses for valid/invalid keys
- **Strategy:** Create test API keys and mock validation logic

## Test Data Fixtures

**Profile Test Data:**
```json
[
  {
    "id": "test-profile-1",
    "linkedin_url": "https://linkedin.com/in/john-doe",
    "name": "John Doe",
    "headline": "Software Engineer",
    "company": "Tech Corp",
    "location": "San Francisco"
  },
  {
    "id": "test-profile-2", 
    "linkedin_url": "https://linkedin.com/in/jane-smith",
    "name": "Jane Smith",
    "headline": "Product Manager",
    "company": "Innovation Inc",
    "location": "New York"
  }
]
```

**API Key Test Data:**
- Valid API key: `test-api-key-valid`
- Invalid API key: `test-api-key-invalid`

## Performance Tests

**Endpoint Response Times**
- Test GET /api/v1/profiles responds within 500ms with 100 profiles
- Test GET /api/v1/profiles with filters responds within 200ms
- Test POST /api/v1/profiles responds within 300ms

**Pagination Performance**
- Test pagination with large datasets (1000+ profiles)
- Test offset performance with high offset values

## Regression Tests

**Make.com Integration Update**
- Test that updated Make.com integration works correctly with new REST endpoints
- Test that LinkedIn URL search functionality works as expected in Make.com workflow
- Test that authentication continues to work after API refactor
