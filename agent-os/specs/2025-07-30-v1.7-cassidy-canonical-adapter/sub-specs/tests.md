# Tests Specification

This is the tests coverage details for the spec detailed in @agent-os/specs/2025-07-30-v1.7-cassidy-canonical-adapter/spec.md

> Created: 2025-07-30
> Version: 1.0.0

## Test Coverage

### Unit Tests

**CassidyAdapter**
- Test successful transformation of complete Cassidy response to CanonicalProfile
- Test successful transformation of nested education data from Cassidy format
- Test successful transformation of nested experience data from Cassidy format
- Test successful transformation of nested company data from Cassidy format
- Test raising IncompleteDataError when essential profile fields are missing
- Test raising IncompleteDataError when essential company fields are missing
- Test handling of optional fields that may be missing from Cassidy response
- Test transformation of edge cases (empty arrays, null values, missing nested objects)

**Error Exception Classes**
- Test IncompleteDataError contains appropriate error message and missing field information
- Test IncompleteDataError inheritance from appropriate base exception

### Integration Tests

**Ingestion Workflow with Adapter**
- Test complete ingestion workflow using CassidyAdapter with real-world Cassidy response format
- Test ingestion workflow gracefully handles IncompleteDataError and logs appropriate warnings
- Test that existing API endpoints continue to work unchanged after adapter integration
- Test that canonical models are properly created and saved to database through adapter

**Adapter Integration with LinkedInWorkflow**
- Test LinkedInWorkflow.process_profile() method uses CassidyAdapter instead of direct Cassidy processing
- Test workflow error handling when adapter raises IncompleteDataError
- Test workflow continues to create profiles and companies through adapter transformation

### Mocking Requirements

- **Cassidy API Response**: Mock complete Cassidy API responses with all required fields for successful transformation testing
- **Incomplete Cassidy Responses**: Mock Cassidy responses missing essential fields to test IncompleteDataError handling
- **Database Operations**: Mock Supabase operations to isolate adapter testing from database dependencies
