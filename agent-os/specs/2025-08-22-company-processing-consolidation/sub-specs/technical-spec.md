# Technical Specification

This is the technical specification for the spec detailed in @agent-os/specs/2025-08-22-company-processing-consolidation/spec.md

> Created: 2025-08-22
> Version: 1.0.0

## Technical Requirements

### Code Analysis Requirements
- **LinkedInDataPipeline Analysis**: Identify all working methods in `app.services.linkedin_pipeline.LinkedInDataPipeline` related to company processing
- **ProfileController Analysis**: Document current company processing implementation in `ProfileController.create_profile`
- **Dependency Analysis**: Map all imports, method calls, and dependencies for both approaches
- **Working Components Identification**: Determine which elements from each approach should be preserved

### Implementation Requirements
- **Method Consolidation**: Merge working logic from `LinkedInDataPipeline._extract_company_urls()` and `LinkedInDataPipeline._fetch_companies()` into ProfileController helper methods
- **Error Handling Preservation**: Maintain all working error handling patterns from both approaches
- **Rate Limiting**: Preserve company fetching rate limiting (asyncio.sleep(1) between requests)
- **Company Service Integration**: Ensure proper CompanyService usage for database operations with deduplication

### Testing Requirements
- **Production Testing**: Test with real Cassidy API endpoints (only available in production)
- **Database Monitoring**: Implement queries to monitor company table additions during processing
- **Progress Tracking**: Add logging to track company processing stages (extraction, fetching, storage)
- **Rollback Plan**: Maintain ability to revert to LinkedInDataPipeline if needed during testing

### Performance Requirements
- **Processing Time Tracking**: Monitor profile creation time to ensure no regression
- **Memory Usage**: Ensure consolidated approach doesn't increase memory consumption
- **Database Connection Efficiency**: Maintain existing connection patterns

## Approach Options

**Option A: Gradual Replacement**
- Keep LinkedInDataPipeline intact
- Modify ProfileController to use its own methods
- Remove LinkedInDataPipeline calls after validation
- Pros: Safe rollback, incremental validation
- Cons: Temporary code duplication during transition

**Option B: Direct Consolidation** 
- Immediately remove LinkedInDataPipeline from ProfileController
- Consolidate all logic into ProfileController methods
- Test consolidated approach directly
- Pros: Clean single-step consolidation, no temporary duplication
- Cons: Higher risk, harder to isolate issues

**Option C: Hybrid Validation** (Selected)
- Keep LinkedInDataPipeline intact but unused
- Implement consolidated ProfileController methods
- Add comparison logging between approaches during testing
- Remove LinkedInDataPipeline after validation
- Pros: Safety with validation, clear migration path, ability to compare results
- Cons: Slightly more complex testing phase

**Rationale:** Option C provides the safest path with comprehensive validation. We can test the new consolidated approach while maintaining the ability to compare results and rollback if needed. This aligns with the requirement for production testing and progress monitoring.

## External Dependencies

**No new dependencies required** - All necessary components already exist:
- CompanyService for database operations
- CompanyRepository for data access  
- CanonicalCompany models for data structures
- CassidyClient for API calls
- AsyncIO for rate limiting

**Justification:** The consolidation uses existing, proven components from both approaches, ensuring reliability and maintaining current functionality.

## Implementation Strategy

### Phase 1: Analysis and Documentation
- Document current LinkedInDataPipeline company processing methods
- Document current ProfileController company processing implementation
- Identify optimal combination of working elements
- Create detailed migration plan

### Phase 2: Consolidated Implementation
- Implement unified helper methods in ProfileController
- Remove LinkedInDataPipeline initialization from ProfileController.__init__
- Add comprehensive logging for production testing
- Preserve error handling and rate limiting

### Phase 3: Production Validation
- Deploy consolidated approach to production
- Monitor database for company additions during processing
- Track processing times and success rates
- Compare results with expected outcomes

### Phase 4: Cleanup
- Remove unused LinkedInDataPipeline references
- Update unit tests to reflect new structure
- Document final consolidated architecture
