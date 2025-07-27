# Spec Requirements Document

> Spec: Critical Workflow & API Integration Fixes
> Created: 2025-07-27
> Status: Planning

## Overview

Fix fundamental workflow bypass issues in the LinkedIn Ingestion Service REST API and enhance API functionality to ensure complete profile data collection. The current REST API bypasses the LinkedInWorkflow.process_profile() system, resulting in incomplete profile data with empty experience/education/certifications arrays.

## User Stories

### Complete Profile Data Collection

As a system integration developer, I want the REST API to collect complete LinkedIn profile data including full work experience with company details, so that downstream systems receive comprehensive candidate intelligence for accurate evaluation and matching.

**Detailed Workflow**: When a profile is ingested via POST /api/v1/profiles, the system should use the LinkedInWorkflow.process_profile() method with include_companies=True to ensure all experience entries trigger company profile fetching, providing complete candidate context.

### Reliable Profile Management

As a business development analyst, I want the system to handle duplicate profiles gracefully and provide delete functionality, so that I can maintain clean data and update profiles when needed without encountering system errors.

**Detailed Workflow**: The system should detect existing profiles by LinkedIn URL, offer update options by default, and provide DELETE endpoints for data management and testing scenarios.

### Enhanced Error Handling

As a system integrator, I want meaningful error responses with actionable guidance, so that I can quickly understand and resolve integration issues without extensive debugging.

**Detailed Workflow**: Common scenarios like duplicate profiles should return elegant 200/409 responses with clear guidance, not 500 errors that require log analysis to understand.

## Spec Scope

1. **Workflow Integration Fix** - Update REST API create_profile() method to use LinkedInWorkflow.process_profile() instead of bypassing to cassidy_client.fetch_profile()
2. **Delete Functionality** - Add DELETE /api/v1/profiles/{id} endpoint and corresponding database methods
3. **Default Company Inclusion** - Change ProfileCreateRequest to include companies by default with optional opt-out flag
4. **Smart Profile Management** - Implement duplicate detection with graceful update-or-create logic
5. **Enhanced Error Handling** - Replace 500 errors with appropriate status codes and meaningful error messages

## Out of Scope

- Complete UI overhaul for profile management
- Advanced batch processing optimization
- Third-party integrations beyond current Make.com setup
- Performance tuning beyond fixing the workflow bypass

## Expected Deliverable

1. Gregory Pascuzzi's profile can be re-ingested successfully with full experience history and associated company profiles for each role
2. DELETE endpoints function correctly for data management and testing
3. Duplicate profile scenarios return elegant responses with update options rather than 500 errors

## Spec Documentation

- Tasks: @agent-os/specs/2025-07-27-critical-workflow-fix/tasks.md
- Technical Specification: @agent-os/specs/2025-07-27-critical-workflow-fix/sub-specs/technical-spec.md
- API Specification: @agent-os/specs/2025-07-27-critical-workflow-fix/sub-specs/api-spec.md
- Tests Specification: @agent-os/specs/2025-07-27-critical-workflow-fix/sub-specs/tests.md
