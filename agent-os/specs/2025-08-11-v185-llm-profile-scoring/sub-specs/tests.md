# Tests Specification

This is the tests coverage details for the spec detailed in @agent-os/specs/2025-08-11-v185-llm-profile-scoring/spec.md

> Created: 2025-08-11
> Version: 1.0.0

## Test Coverage

### Unit Tests

**LLMScoringService**
- Test OpenAI client initialization with various API key configurations
- Test profile data serialization to text format for LLM analysis
- Test prompt formatting and parameter validation
- Test LLM response parsing for valid JSON responses
- Test error handling for malformed JSON responses
- Test retry logic for transient OpenAI API failures
- Test rate limiting and token usage tracking
- Test response validation against different prompt schemas

**ScoringJob Models**
- Test ScoringRequest validation with valid/invalid prompts
- Test ScoringResponse serialization and deserialization
- Test ScoringJob status transitions and state management
- Test database field validation and constraints
- Test timestamp handling and timezone consistency

**Database Operations**
- Test scoring job creation with valid profile references
- Test job status updates and completion tracking
- Test job cleanup and retention policies
- Test concurrent job limits per profile enforcement
- Test database constraint violations and error handling

### Integration Tests

**API Endpoints**
- Test POST /api/v1/profiles/{id}/score with valid requests
- Test scoring job creation and immediate status response
- Test GET /api/v1/scoring-jobs/{id} for all job status types
- Test POST /api/v1/scoring-jobs/{id}/retry for failed jobs
- Test authentication and authorization for all endpoints
- Test rate limiting enforcement and error responses
- Test cross-profile access control validation

**LLM Integration Workflow**
- Test complete scoring flow from request to LLM response
- Test asynchronous job processing and status updates
- Test job polling until completion
- Test multiple concurrent scoring jobs
- Test job failure recovery and retry mechanisms
- Test different OpenAI model configurations (GPT-3.5, GPT-4)

**Error Scenarios**
- Test scoring requests for non-existent profiles
- Test malformed evaluation prompts and validation errors
- Test OpenAI API failures and fallback behavior
- Test network timeouts and connection errors
- Test invalid API key handling and error responses
- Test database connection failures during job processing

### Feature Tests

**Complete Scoring Workflow**
- Test end-to-end scoring with CIO/CTO evaluation prompt
- Test JSON response parsing for complex scoring structures
- Test profile data transformation accuracy
- Test job completion notification and result retrieval
- Test multiple evaluation criteria on same profile
- Test scoring result caching and retrieval

**Performance and Reliability**
- Test scoring job processing under high load
- Test API response times for job status checks
- Test database query performance with large job volumes
- Test memory usage during profile data processing
- Test OpenAI API rate limit handling

### Mocking Requirements

**OpenAI API Mock**
- Mock successful LLM responses with valid JSON structures
- Mock various error responses (rate limit, invalid key, timeout)
- Mock different response times to test async behavior
- Mock token usage and cost calculation
- Mock different model responses (GPT-3.5 vs GPT-4)
- Mock malformed JSON responses for error testing

**Database Mocking**
- Mock Supabase client for job CRUD operations
- Mock database constraint violations
- Mock connection failures and recovery scenarios
- Mock concurrent access patterns for job processing
- Mock job cleanup and retention policy execution

**Profile Data Mocking**
- Mock LinkedIn profile retrieval from existing database
- Mock various profile completeness levels (minimal vs full data)
- Mock profile access control and permission scenarios
- Mock profile not found and deleted profile scenarios

## Test Data Requirements

### Sample Evaluation Prompts
- CIO/CTO/CISO evaluation prompt (from specification context)
- Generic seniority assessment prompt
- Industry expertise evaluation prompt
- Invalid prompts for error testing (empty, malformed JSON)

### Profile Test Data
- Complete executive profiles with extensive experience
- Minimal profiles for edge case testing
- Profiles with various industry backgrounds
- Profiles with different tenure patterns and career trajectories

### Expected LLM Responses
- Valid JSON responses matching prompt specifications
- Edge case responses (empty scores, maximum values)
- Malformed responses for error handling tests
- Responses with missing required fields

## Performance Benchmarks

### Response Time Targets
- Job creation: < 200ms
- Job status check: < 100ms
- Complete scoring workflow: < 30 seconds
- Database queries: < 50ms

### Reliability Targets
- Job completion success rate: > 95%
- API endpoint availability: > 99.5%
- LLM response parsing accuracy: > 98%
- Retry success rate for transient failures: > 85%
