# Tests Specification

This is the tests coverage details for the spec detailed in @agent-os/specs/2025-08-22-company-processing-consolidation/spec.md

> Created: 2025-08-22
> Version: 1.0.0

## Test Coverage

### Unit Tests

**ProfileController**
- Test _extract_company_urls_from_profile method with mock LinkedIn profile data
- Test _fetch_companies_from_cassidy method with mock Cassidy client responses
- Test create_profile method consolidation logic with mocked dependencies
- Test error handling for company processing failures

**Helper Methods**
- Test company URL extraction from various profile experience formats
- Test company deduplication logic
- Test rate limiting behavior (asyncio.sleep calls)
- Test error recovery and continuation when individual companies fail

### Integration Tests

**Company Processing Flow**
- Test end-to-end profile creation with company processing enabled
- Test ProfileController without LinkedInDataPipeline dependencies
- Test CompanyService integration with ProfileController methods
- Test database storage of companies during profile creation

**Error Scenarios**
- Test behavior when Cassidy API fails for company fetching
- Test behavior when company processing fails but profile creation continues
- Test rollback scenarios if consolidated approach fails

### Production Tests (Primary Focus)

**Real Cassidy API Integration**
- Test ProfileController.create_profile with real LinkedIn URLs in production
- Monitor database company table for new entries during processing
- Track processing completion times and success rates
- Validate company data accuracy compared to LinkedIn source

**Database Monitoring Tests**
- Query company table before/during/after profile processing
- Monitor profile_companies relationship table updates
- Track CompanyService deduplication behavior
- Verify data consistency across related tables

### Mocking Requirements

**Development Environment**
- **Cassidy Client**: Mock fetch_company responses with realistic company data
- **Time-based tests**: Mock asyncio.sleep for rate limiting tests
- **Database operations**: Mock CompanyService and CompanyRepository for unit tests

**Production Environment**
- **No mocking**: Use real Cassidy API and database for validation
- **Monitoring queries**: Real database queries to track progress
- **Logging verification**: Real logs to confirm processing steps

## Production Testing Strategy

### Pre-deployment Validation
- Unit tests with comprehensive mocking must pass
- Integration tests with test database must pass
- Code analysis documentation complete

### Production Testing Approach
- Deploy consolidated approach to production environment
- Test with 3-5 real LinkedIn profiles with known company experience
- Monitor database in real-time during processing:
  ```sql
  -- Monitor company additions
  SELECT COUNT(*) FROM companies WHERE created_at > '2025-08-22T20:00:00Z';
  
  -- Monitor profile-company relationships
  SELECT COUNT(*) FROM profile_companies WHERE created_at > '2025-08-22T20:00:00Z';
  
  -- Check latest processed profile
  SELECT id, name, created_at FROM profiles ORDER BY created_at DESC LIMIT 1;
  ```

### Success Criteria
- ProfileController.create_profile completes without LinkedInDataPipeline calls
- Companies are successfully extracted and stored in database
- Processing times remain within acceptable ranges (< 2 minutes per profile)
- No data loss or corruption compared to previous approach

### Rollback Testing
- Verify ability to revert to LinkedInDataPipeline if consolidated approach fails
- Test data consistency during rollback scenarios
- Validate that no partial data remains from failed consolidation attempts
