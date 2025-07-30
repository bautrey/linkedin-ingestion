# Tests Specification

This is the tests coverage details for the spec detailed in @agent-os/specs/2025-07-30-v1.6-canonical-profile-models/spec.md

> Created: 2025-07-30
> Version: 1.0.0

## Test Coverage

### Unit Tests

**CanonicalProfile Model**
- Test valid profile creation with all required fields
- Test profile creation with optional fields
- Test LinkedIn URL validation (valid and invalid URLs)
- Test field type validation (string, datetime, etc.)
- Test model serialization to dict/JSON
- Test timestamp auto-generation on creation

**CanonicalCompany Model**
- Test valid company creation with required fields
- Test company creation with optional employment fields
- Test URL validation for company LinkedIn URLs and websites
- Test date validation for start_date and end_date
- Test model serialization to dict/JSON
- Test timestamp auto-generation on creation

### Integration Tests

**Model Compatibility**
- Test CanonicalProfile with work_history containing CanonicalCompany objects
- Test nested model validation (profile with multiple companies)
- Test model conversion from existing Cassidy models (preparation for v1.7)

### Validation Tests

**Field Validation**
- Test required field enforcement (full_name, company name)
- Test URL format validation with various valid/invalid URLs
- Test datetime field validation with various date formats
- Test empty string handling vs None for optional fields
- Test list field default behavior

### Mocking Requirements

- **External Services:** None required for this spec
- **Time-based Tests:** Mock `datetime.now()` for consistent timestamp testing
