# API Specification

This is the API specification for the spec detailed in @agent-os/specs/2025-07-27-critical-workflow-fix/spec.md

> Created: 2025-07-27
> Version: 1.0.0

## Enhanced Endpoints

### DELETE /api/v1/profiles/{id}

**Purpose:** Delete a LinkedIn profile and associated data from the system
**Parameters:** 
- `id` (path): Profile ID (UUID format)
- `x-api-key` (header): API authentication key

**Response:**
- **204 No Content**: Profile successfully deleted
- **404 Not Found**: Profile not found
- **403 Forbidden**: Invalid API key

**Example Request:**
```http
DELETE /api/v1/profiles/123e4567-e89b-12d3-a456-426614174000
x-api-key: li_HieZz-IjBp0uE7d-rZkRE0qyy12r5_ZJS_FR4jMvv0I
```

**Example Response (Success):**
```http
HTTP/1.1 204 No Content
```

**Example Response (Not Found):**
```http
HTTP/1.1 404 Not Found
Content-Type: application/json

{
  "error_code": "PROFILE_NOT_FOUND",
  "message": "Profile with ID 123e4567-e89b-12d3-a456-426614174000 not found",
  "details": {
    "profile_id": "123e4567-e89b-12d3-a456-426614174000",
    "suggestion": "Check profile ID or use GET /api/v1/profiles to list available profiles"
  }
}
```

## Enhanced POST /api/v1/profiles

**Purpose:** Create new LinkedIn profile with enhanced workflow integration and duplicate handling
**Parameters:**
- `linkedin_url` (body): LinkedIn profile URL
- `include_companies` (body, optional): Whether to fetch company data (default: true)
- `force_create` (body, optional): Force creation even if profile exists (default: false)

**Enhanced Responses:**
- **200 OK**: Profile created successfully (includes full workflow data)
- **409 Conflict**: Profile already exists (with update suggestion)
- **400 Bad Request**: Invalid LinkedIn URL or parameters
- **403 Forbidden**: Invalid API key

**Example Request (Enhanced):**
```json
{
  "linkedin_url": "https://linkedin.com/in/gregorypascuzzi",
  "include_companies": true,
  "force_create": false
}
```

**Example Response (Success with Complete Data):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "linkedin_url": "https://linkedin.com/in/gregorypascuzzi",
  "name": "Gregory Pascuzzi",
  "experience": [
    {
      "company": "Tech Corp",
      "title": "Senior Engineer",
      "company_profile": {
        "id": "comp_456",
        "name": "Tech Corp",
        "industry": "Technology",
        "size": "500-1000"
      }
    }
  ],
  "created_at": "2025-07-27T13:47:00Z",
  "workflow_completed": true,
  "companies_fetched": 3
}
```

**Example Response (Conflict with Suggestion):**
```json
{
  "error_code": "PROFILE_EXISTS",
  "message": "Profile already exists for this LinkedIn URL",
  "details": {
    "existing_profile_id": "123e4567-e89b-12d3-a456-426614174000",
    "linkedin_url": "https://linkedin.com/in/gregorypascuzzi",
    "suggestion": "Use PUT /api/v1/profiles/{id} to update or set force_create=true to create duplicate",
    "last_updated": "2025-07-26T10:30:00Z"
  }
}
```

## Error Response Model

**Standardized Error Format:**
```json
{
  "error_code": "ERROR_TYPE",
  "message": "Human-readable error description",
  "details": {
    "field_specific_info": "value",
    "suggestion": "Actionable guidance for resolution"
  }
}
```

**Common Error Codes:**
- `PROFILE_NOT_FOUND`: Profile doesn't exist
- `PROFILE_EXISTS`: Duplicate profile detected
- `INVALID_LINKEDIN_URL`: URL format or accessibility issues
- `WORKFLOW_FAILED`: LinkedIn workflow processing error
- `INVALID_API_KEY`: Authentication failure
- `RATE_LIMIT_EXCEEDED`: Too many requests

## Controller Changes

### ProfileController Enhancements

**create_profile() method:**
- Integration with LinkedInWorkflow.process_profile()
- Duplicate detection and smart handling
- Enhanced error responses with actionable guidance
- Default company inclusion with opt-out option

**delete_profile() method (NEW):**
- Profile deletion with cascade cleanup
- Proper HTTP status codes
- Security validation with API key check

**Error Handling:**
- Convert database exceptions to appropriate HTTP status codes
- Provide meaningful error messages with suggestions
- Maintain detailed server-side logging while cleaning client responses
