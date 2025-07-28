# Tests Specification

This is the tests coverage details for the spec detailed in @agent-os/specs/2025-07-28-v1.5-error-handling/spec.md

> Created: 2025-07-28
> Version: 1.0.0

## Test Coverage

### Unit Tests

**Custom Exceptions**
- Test custom exception classes for proper inheritance and message setting

### Integration Tests

**Error Response Structure**
- Test all endpoints return error responses in the correct JSON format
- Verify HTTP status codes for different error scenarios (400, 409, 422, 500)

**Validation Errors**
- Ensure Pydantic validation errors return clear field-level feedback in the response

### Mocking Requirements

- **LinkedIn API:** Mock expected error responses for invalid URL formats
- **Supabase Client:** Simulate scenarios where duplicate profiles are detected
