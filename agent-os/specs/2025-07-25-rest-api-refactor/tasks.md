# REST API Refactor - Implementation Tasks

> Spec: @agent-os/specs/2025-07-25-rest-api-refactor/spec.md
> Created: 2025-07-25
> Status: Ready for Implementation

## Parent Tasks

### [ ] Core Infrastructure Setup
**Estimated Time**: 45 minutes
**Dependencies**: None

#### Subtasks:
- [ ] Create ProfileController class with resource methods (list_profiles, get_profile, create_profile)
- [ ] Update FastAPI routing to use new REST endpoints (/api/v1/profiles, /api/v1/profiles/{id})
- [ ] Remove old action-based endpoints (/ingest, /recent)
- [ ] Create Pydantic response models (ProfileResponse, ProfileListResponse, PaginationMetadata, ErrorResponse)

### [ ] Search and Retrieval Logic
**Estimated Time**: 60 minutes
**Dependencies**: Core Infrastructure Setup

#### Subtasks:
- [ ] Implement LinkedIn URL exact search functionality in list_profiles()
- [ ] Add company name and person name partial search (case-insensitive)
- [ ] Implement pagination with limit/offset parameters
- [ ] Add individual profile retrieval by UUID in get_profile()
- [ ] Implement proper error handling (404 for not found, validation errors)

### [ ] Profile Creation and Database Updates
**Estimated Time**: 45 minutes
**Dependencies**: Search and Retrieval Logic

#### Subtasks:
- [ ] Implement profile creation in create_profile() method
- [ ] Add duplicate LinkedIn URL detection (409 conflict handling)
- [ ] Update database queries to support new search parameters
- [ ] Add query parameter validation and error responses
- [ ] Optimize database queries for pagination and partial matches

### [ ] Make.com Integration Update
**Estimated Time**: 30 minutes
**Dependencies**: Profile Creation and Database Updates

#### Subtasks:
- [ ] Update Make.com HTTP module to use POST /api/v1/profiles for ingestion
- [ ] Update Make.com search to use GET /api/v1/profiles?linkedin_url={url}
- [ ] Test end-to-end Make.com → LinkedIn API → FIT → JIRA workflow
- [ ] Verify response parsing and data format compatibility

## Implementation Notes

**Clean Refactor Approach**: This implementation completely replaces old endpoints with new REST-compliant endpoints. No backward compatibility maintained.

**API Key Authentication**: Preserved exactly as-is using X-API-Key header.

**Response Format**: New endpoints return equivalent data in REST-compliant format with proper HTTP status codes.

**Testing Strategy**: Manual testing of each endpoint, then end-to-end Make.com integration verification.

## Success Criteria

- [ ] All old endpoints (/ingest, /recent) removed
- [ ] New REST endpoints functional and following Google AIP-121
- [ ] LinkedIn URL search returns correct profile data
- [ ] Make.com integration works without errors
- [ ] All API responses use consistent JSON format with proper HTTP status codes

## Quick Start Commands for Implementation Session

```bash
# Test the new API endpoints
curl -H "X-API-Key: li_HieZz-IjBp0uE7d-rZkRE0qyy12r5_ZJS_FR4jMvv0I" \
  "https://smooth-mailbox-production.up.railway.app/api/v1/profiles?linkedin_url=https://linkedin.com/in/username"

# Test profile creation
curl -X POST -H "X-API-Key: li_HieZz-IjBp0uE7d-rZkRE0qyy12r5_ZJS_FR4jMvv0I" \
  -H "Content-Type: application/json" \
  -d '{"linkedin_url":"https://linkedin.com/in/test","name":"Test User"}' \
  "https://smooth-mailbox-production.up.railway.app/api/v1/profiles"
```

## Estimated Total Implementation Time: 3 hours

**Status**: ✅ Ready for focused implementation session
