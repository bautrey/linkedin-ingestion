# API Specification

This is the API specification for the spec detailed in @agent-os/specs/2025-07-25-rest-api-refactor/spec.md

> Created: 2025-07-25
> Version: 1.0.0

## Resource-Oriented Endpoints

### GET /api/v1/profiles

**Purpose:** List profiles with flexible filtering and search capabilities
**Authentication:** API key required in `X-API-Key` header
**Method:** GET

**Query Parameters:**
- `linkedin_url` (string, optional): Exact LinkedIn profile URL to search for
- `company` (string, optional): Filter profiles by company name (partial match)
- `name` (string, optional): Filter profiles by person name (partial match)
- `limit` (integer, optional): Maximum results to return (default: 50, max: 100)
- `offset` (integer, optional): Number of results to skip for pagination (default: 0)

**Response Format:**
```json
{
  "profiles": [
    {
      "id": "uuid",
      "linkedin_url": "string",
      "name": "string", 
      "headline": "string",
      "company": "string",
      "location": "string",
      "created_at": "iso8601_timestamp",
      "updated_at": "iso8601_timestamp"
    }
  ],
  "pagination": {
    "total": "integer",
    "limit": "integer", 
    "offset": "integer",
    "has_more": "boolean"
  }
}
```

**HTTP Status Codes:**
- `200 OK`: Successful retrieval
- `400 Bad Request`: Invalid query parameters
- `401 Unauthorized`: Missing or invalid API key
- `500 Internal Server Error`: Server error

### GET /api/v1/profiles/{id}

**Purpose:** Retrieve a specific profile by its unique identifier
**Authentication:** API key required in `X-API-Key` header
**Method:** GET

**Path Parameters:**
- `id` (string, required): Unique profile identifier (UUID format)

**Response Format:**
```json
{
  "id": "uuid",
  "linkedin_url": "string",
  "name": "string",
  "headline": "string", 
  "company": "string",
  "location": "string",
  "created_at": "iso8601_timestamp",
  "updated_at": "iso8601_timestamp"
}
```

**HTTP Status Codes:**
- `200 OK`: Profile found and returned
- `401 Unauthorized`: Missing or invalid API key
- `404 Not Found`: Profile ID does not exist
- `500 Internal Server Error`: Server error

### POST /api/v1/profiles

**Purpose:** Create a new profile from LinkedIn data (ingestion)
**Authentication:** API key required in `X-API-Key` header
**Method:** POST

**Request Body:**
```json
{
  "linkedin_url": "string (required)",
  "name": "string (required)",
  "headline": "string (optional)",
  "company": "string (optional)",  
  "location": "string (optional)"
}
```

**Response Format:**
```json
{
  "id": "uuid",
  "linkedin_url": "string",
  "name": "string",
  "headline": "string",
  "company": "string", 
  "location": "string",
  "created_at": "iso8601_timestamp",
  "updated_at": "iso8601_timestamp"
}
```

**HTTP Status Codes:**
- `201 Created`: Profile successfully created
- `400 Bad Request`: Invalid request body or missing required fields
- `401 Unauthorized`: Missing or invalid API key
- `409 Conflict`: Profile with same LinkedIn URL already exists
- `500 Internal Server Error`: Server error


## Error Response Format

All endpoints return consistent error responses:

```json
{
  "error": {
    "code": "string",
    "message": "string", 
    "details": "object (optional)"
  }
}
```

## Authentication

All endpoints require API key authentication via the `X-API-Key` header:

```
X-API-Key: your-api-key-here
```

Missing or invalid API keys return `401 Unauthorized` with error details.

## Controller Implementation

**ProfileController** (resource-oriented controller)
- `list_profiles()`: Handle GET /api/v1/profiles
- `get_profile()`: Handle GET /api/v1/profiles/{id}
- `create_profile()`: Handle POST /api/v1/profiles
