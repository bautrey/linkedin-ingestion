# Technical Specification

This is the technical specification for the spec detailed in @agent-os/specs/2025-07-27-critical-workflow-fix/spec.md

> Created: 2025-07-27
> Version: 1.0.0

## Technical Requirements

### Workflow Integration Fix
- **Current Issue**: `main.py` line 204 calls `self.cassidy_client.fetch_profile(linkedin_url)` directly
- **Required Change**: Replace with `LinkedInWorkflow.process_profile()` method call
- **Include Companies**: Default `ProfileIngestionRequest(include_companies=True)`
- **Maintain API Compatibility**: Keep existing REST endpoint behavior for clients

### Delete Functionality
- **Database Method**: Add `delete_profile(profile_id: str)` method to SupabaseClient
- **REST Endpoint**: Implement `DELETE /api/v1/profiles/{id}` in ProfileController
- **Cascade Behavior**: Handle related company data and relationship cleanup
- **Response Format**: Return 204 No Content on success, 404 if not found

### Default Company Inclusion
- **Model Update**: Add `include_companies: bool = True` to ProfileCreateRequest
- **Backward Compatibility**: Existing requests without the field default to True
- **Opt-out Option**: Allow `include_companies=False` for lightweight ingestion
- **Documentation**: Update OpenAPI schema with new field

### Smart Profile Management
- **Duplicate Detection**: Check LinkedIn URL before creation using existing `get_profile_by_url()` method
- **Update Logic**: If profile exists, offer update by default rather than 409 conflict
- **Create New Flag**: Add `force_create: bool = False` option to override update behavior
- **Response Enhancement**: Include `existing_profile_id` in conflict responses

### Enhanced Error Handling
- **Replace 500 Errors**: Convert database constraint violations to appropriate HTTP status codes
- **Meaningful Messages**: Provide actionable error descriptions with suggested solutions
- **Error Response Model**: Standardize error format with `error_code`, `message`, and `details` fields
- **Logging Integration**: Maintain detailed logging while providing clean client responses

## Approach Options

**Option A: Minimal Changes**
- Pros: Quick implementation, low risk
- Cons: Doesn't address root architectural issues

**Option B: Comprehensive Workflow Integration** (Selected)
- Pros: Fixes root cause, ensures data completeness, maintains architectural integrity
- Cons: More extensive changes, requires thorough testing
- **Rationale**: The workflow bypass is the fundamental issue causing incomplete data. Fixing it properly ensures long-term system reliability.

**Option C: Hybrid Approach with Feature Flags**
- Pros: Allows gradual rollout, fallback options
- Cons: Increased complexity, potential confusion

**Rationale**: Option B addresses the core problem while maintaining the existing API surface. The workflow system was designed for complete data collection, and bypassing it defeats the system's purpose.

## External Dependencies

- **No New Libraries Required**: All functionality can be implemented using existing FastAPI, Pydantic, and Supabase dependencies
- **Workflow System**: Existing `LinkedInWorkflow` class needs to be integrated properly
- **Database Schema**: Current schema supports all required functionality

## Implementation Details

### File Changes Required
- **main.py**: Update ProfileController.create_profile() method (line ~204)
- **app/models/**: Add delete functionality and update ProfileCreateRequest
- **app/database/supabase_client.py**: Add delete_profile() method
- **app/workflows/**: Ensure LinkedInWorkflow.process_profile() handles include_companies correctly

### Testing Requirements
- **Unit Tests**: Mock LinkedInWorkflow.process_profile() calls
- **Integration Tests**: Test complete workflow with real LinkedIn URLs
- **Error Handling Tests**: Verify proper status codes for all scenarios
- **Regression Tests**: Ensure existing functionality remains intact

### Deployment Considerations
- **Backward Compatibility**: Existing API clients continue to work without changes
- **Data Migration**: No database schema changes required
- **Performance Impact**: LinkedInWorkflow may be slower than direct client calls, but provides complete data
- **Monitoring**: Track workflow completion rates and error patterns
