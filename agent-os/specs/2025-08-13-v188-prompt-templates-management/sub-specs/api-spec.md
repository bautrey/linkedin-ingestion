# API Specification

> Spec: V1.88 Prompt Templates Management System
> Document: API Specification
> Created: 2025-08-13

## API Overview

The Prompt Templates Management API provides RESTful endpoints for creating, reading, updating, and deleting evaluation prompt templates. All endpoints follow the existing authentication and error handling patterns.

## Authentication

All endpoints require the same API key authentication as existing endpoints:

```http
x-api-key: li_HieZz-IjBp0uE7d-rZkRE0qyy12r5_ZJS_FR4jMvv0I
```

## Base URL

Production: `https://smooth-mailbox-production.up.railway.app/api/v1`

## Endpoints

### 1. List Templates

Get all active prompt templates, optionally filtered by category.

```http
GET /api/v1/templates
GET /api/v1/templates?category=CTO
GET /api/v1/templates?include_inactive=true
```

**Query Parameters:**
- `category` (optional): Filter by template category (e.g., "CTO", "CIO", "CISO")
- `include_inactive` (optional): Include inactive templates (default: false)

**Response:**
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "templates": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "name": "Fortium CTO Evaluation",
      "category": "CTO", 
      "description": "Standard evaluation criteria for CTO candidates",
      "version": 1,
      "is_active": true,
      "created_at": "2025-08-13T12:00:00Z",
      "updated_at": "2025-08-13T12:00:00Z",
      "metadata": {}
    }
  ],
  "count": 1
}
```

### 2. Get Template by ID

Retrieve a specific template by its UUID.

```http
GET /api/v1/templates/{template_id}
```

**Path Parameters:**
- `template_id` (required): UUID of the template

**Response:**
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "Fortium CTO Evaluation",
  "category": "CTO",
  "description": "Standard evaluation criteria for CTO candidates", 
  "prompt_text": "You are evaluating a candidate for a Chief Technology Officer (CTO) position...",
  "version": 1,
  "is_active": true,
  "created_at": "2025-08-13T12:00:00Z",
  "updated_at": "2025-08-13T12:00:00Z",
  "metadata": {}
}
```

**Error Responses:**
```http
HTTP/1.1 404 Not Found
Content-Type: application/json

{
  "error": "Template not found",
  "message": "No template found with ID: 123e4567-e89b-12d3-a456-426614174000"
}
```

### 3. Create Template

Create a new prompt template.

```http
POST /api/v1/templates
```

**Request Body:**
```json
{
  "name": "Custom CTO Evaluation",
  "category": "CTO", 
  "description": "Custom evaluation for senior technical roles",
  "prompt_text": "You are evaluating a candidate...",
  "is_active": true,
  "metadata": {
    "tags": ["technical", "leadership"],
    "difficulty": "advanced"
  }
}
```

**Response:**
```http
HTTP/1.1 201 Created
Content-Type: application/json

{
  "id": "456e7890-e89b-12d3-a456-426614174001",
  "name": "Custom CTO Evaluation", 
  "category": "CTO",
  "description": "Custom evaluation for senior technical roles",
  "prompt_text": "You are evaluating a candidate...",
  "version": 1,
  "is_active": true,
  "created_at": "2025-08-13T12:30:00Z",
  "updated_at": "2025-08-13T12:30:00Z",
  "metadata": {
    "tags": ["technical", "leadership"],
    "difficulty": "advanced"
  }
}
```

**Error Responses:**
```http
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "error": "Validation error",
  "message": "Template name is required",
  "details": {
    "field": "name",
    "code": "required"
  }
}
```

### 4. Update Template

Update an existing template.

```http
PUT /api/v1/templates/{template_id}
```

**Path Parameters:**
- `template_id` (required): UUID of the template to update

**Request Body:**
```json
{
  "name": "Updated CTO Evaluation",
  "description": "Updated evaluation criteria",
  "prompt_text": "Updated prompt text...",
  "is_active": true,
  "metadata": {
    "updated_reason": "Added new criteria"
  }
}
```

**Response:**
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "Updated CTO Evaluation",
  "category": "CTO",
  "description": "Updated evaluation criteria",
  "prompt_text": "Updated prompt text...", 
  "version": 1,
  "is_active": true,
  "created_at": "2025-08-13T12:00:00Z",
  "updated_at": "2025-08-13T13:00:00Z",
  "metadata": {
    "updated_reason": "Added new criteria"
  }
}
```

### 5. Delete Template

Soft delete a template (sets is_active to false).

```http
DELETE /api/v1/templates/{template_id}
```

**Path Parameters:**
- `template_id` (required): UUID of the template to delete

**Response:**
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "message": "Template successfully deleted",
  "template_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

### 6. Enhanced Scoring with Template

Modified scoring endpoint to accept template_id instead of raw prompt.

```http
POST /api/v1/profiles/{profile_id}/score
```

**Path Parameters:**
- `profile_id` (required): UUID of the profile to score

**Request Body (Option 1 - Template ID):**
```json
{
  "template_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

**Request Body (Option 2 - Raw Prompt - Backward Compatibility):**
```json
{
  "prompt": "You are evaluating a candidate..."
}
```

**Response:**
```http
HTTP/1.1 202 Accepted
Content-Type: application/json

{
  "job_id": "789e0123-e89b-12d3-a456-426614174002",
  "status": "processing",
  "profile_id": "435ccbf7-6c5e-4e2d-bdc3-052a244d7121",
  "template_id": "123e4567-e89b-12d3-a456-426614174000",
  "created_at": "2025-08-13T14:00:00Z"
}
```

## Data Models

### PromptTemplate

```typescript
interface PromptTemplate {
  id: string;                    // UUID
  name: string;                  // Template name
  category: string;              // Category (CTO, CIO, CISO, etc.)
  description?: string;          // Optional description
  prompt_text: string;           // The actual prompt content
  version: number;               // Version number (default: 1)
  is_active: boolean;            // Whether template is active (default: true)
  created_at: string;            // ISO 8601 timestamp
  updated_at: string;            // ISO 8601 timestamp  
  metadata: Record<string, any>; // Additional structured data
}
```

### TemplateListResponse

```typescript
interface TemplateListResponse {
  templates: PromptTemplate[];
  count: number;
}
```

### CreateTemplateRequest

```typescript
interface CreateTemplateRequest {
  name: string;                          // Required
  category: string;                      // Required
  description?: string;                  // Optional
  prompt_text: string;                   // Required
  is_active?: boolean;                   // Optional (default: true)
  metadata?: Record<string, any>;        // Optional
}
```

### UpdateTemplateRequest

```typescript
interface UpdateTemplateRequest {
  name?: string;                         // Optional
  description?: string;                  // Optional
  prompt_text?: string;                  // Optional
  is_active?: boolean;                   // Optional
  metadata?: Record<string, any>;        // Optional
  // Note: category and version cannot be updated
}
```

### Enhanced Scoring Request

```typescript
interface ScoringRequest {
  template_id?: string;                  // Either template_id OR prompt
  prompt?: string;                       // Either template_id OR prompt
}
```

## Error Handling

### Standard Error Response

```typescript
interface ErrorResponse {
  error: string;                         // Error type
  message: string;                       // Human-readable message
  details?: Record<string, any>;         // Additional error context
}
```

### HTTP Status Codes

- `200 OK` - Successful operation
- `201 Created` - Resource created successfully
- `400 Bad Request` - Validation error or malformed request
- `401 Unauthorized` - Missing or invalid API key
- `404 Not Found` - Resource not found
- `409 Conflict` - Resource conflict (e.g., duplicate name)
- `422 Unprocessable Entity` - Validation error with detailed field information
- `500 Internal Server Error` - Server error

### Common Error Scenarios

1. **Missing API Key**
```http
HTTP/1.1 401 Unauthorized
{
  "error": "Authentication required",
  "message": "Missing or invalid API key"
}
```

2. **Validation Error**
```http
HTTP/1.1 400 Bad Request
{
  "error": "Validation error",
  "message": "Template name cannot be empty",
  "details": {
    "field": "name",
    "code": "required"
  }
}
```

3. **Template Not Found**
```http
HTTP/1.1 404 Not Found
{
  "error": "Template not found", 
  "message": "No template found with ID: 123e4567-e89b-12d3-a456-426614174000"
}
```

## Integration Notes

### Backward Compatibility

The enhanced scoring endpoint maintains backward compatibility:
- Existing clients using `prompt` field continue to work
- New clients can use `template_id` field
- Both approaches produce identical scoring job results

### Template Resolution

When using `template_id` in scoring requests:
1. System retrieves template by ID
2. Validates template is active
3. Uses template's `prompt_text` for LLM scoring
4. Stores both `template_id` and resolved prompt in scoring job

### Caching Strategy

Templates are relatively static and suitable for caching:
- Cache active templates by category for list operations
- Cache individual templates by ID for scoring operations
- Invalidate cache on template updates/deletions

## Production Deployment Notes

### Health Check Integration

Extend existing `/health` endpoint to include template system:

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "services": {
    "database": "healthy",
    "template_system": "healthy"
  },
  "timestamp": "2025-08-13T12:00:00Z"
}
```

### Monitoring

Track these metrics for template system:
- Template retrieval latency
- Template creation/update frequency
- Template usage in scoring requests
- Template system error rates
