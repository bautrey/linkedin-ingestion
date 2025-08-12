# API Specification

This is the API specification for the spec detailed in @agent-os/specs/2025-08-11-v185-llm-profile-scoring/spec.md

> Created: 2025-08-11
> Version: 1.0.0

## Endpoints

### POST /api/v1/profiles/{profile_id}/score

**Purpose:** Initiate LLM-based scoring evaluation for a LinkedIn profile
**Parameters:** 
- `profile_id` (path) - UUID of the profile to evaluate
- Request body with evaluation prompt and parameters

**Request Schema:**
```json
{
  "prompt": "string (required) - Complete evaluation prompt with instructions and response format",
  "model": "string (optional) - OpenAI model to use (default: 'gpt-3.5-turbo')",
  "max_tokens": "number (optional) - Maximum tokens in LLM response (default: 2000)",
  "temperature": "number (optional) - LLM creativity setting 0-1 (default: 0.1)"
}
```

**Response:** 
```json
{
  "job_id": "uuid",
  "status": "pending",
  "profile_id": "uuid", 
  "created_at": "ISO8601 timestamp",
  "estimated_completion": "ISO8601 timestamp"
}
```

**Errors:** 
- 400: Invalid profile_id or malformed request
- 404: Profile not found
- 429: Rate limit exceeded
- 500: Internal server error

### GET /api/v1/scoring-jobs/{job_id}

**Purpose:** Check the status and retrieve results of a scoring job
**Parameters:** 
- `job_id` (path) - UUID of the scoring job to check

**Response (Pending):**
```json
{
  "job_id": "uuid",
  "status": "pending" | "processing",
  "profile_id": "uuid",
  "created_at": "ISO8601 timestamp",
  "updated_at": "ISO8601 timestamp"
}
```

**Response (Completed):**
```json
{
  "job_id": "uuid", 
  "status": "completed",
  "profile_id": "uuid",
  "result": {
    "llm_response": "object - Raw LLM response",
    "parsed_score": "object - Structured scoring results",
    "model_used": "string",
    "tokens_used": "number"
  },
  "created_at": "ISO8601 timestamp",
  "completed_at": "ISO8601 timestamp"
}
```

**Response (Failed):**
```json
{
  "job_id": "uuid",
  "status": "failed", 
  "profile_id": "uuid",
  "error": {
    "code": "string - Error classification",
    "message": "string - Human-readable error description",
    "retryable": "boolean - Whether job can be retried"
  },
  "created_at": "ISO8601 timestamp",
  "failed_at": "ISO8601 timestamp"
}
```

**Errors:**
- 404: Job not found
- 500: Internal server error

### POST /api/v1/scoring-jobs/{job_id}/retry

**Purpose:** Retry a failed scoring job
**Parameters:**
- `job_id` (path) - UUID of the failed job to retry

**Response:**
```json
{
  "job_id": "uuid",
  "status": "pending",
  "retry_count": "number",
  "created_at": "ISO8601 timestamp"
}
```

**Errors:**
- 404: Job not found
- 400: Job not in failed state or retry limit exceeded
- 500: Internal server error

## Controllers

### ProfileScoringController

**Responsibilities:**
- Validate scoring requests and profile existence
- Create scoring jobs in database
- Initiate background LLM processing
- Handle request/response formatting

**Business Logic:**
- Verify profile exists and is accessible
- Validate evaluation prompt is not empty
- Check rate limits per profile/user
- Generate unique job IDs
- Queue job for background processing

**Error Handling:**
- Profile not found → 404 with helpful message
- Invalid prompt → 400 with validation details
- Rate limit exceeded → 429 with retry-after header
- Database errors → 500 with generic message

### ScoringJobController  

**Responsibilities:**
- Retrieve job status and results
- Handle job retry requests
- Format responses based on job status

**Business Logic:**
- Fetch job by ID with error handling
- Check job access permissions
- Format response based on job status (pending/completed/failed)
- Validate retry eligibility and limits

**Error Handling:**
- Job not found → 404 with job ID reference
- Access denied → 403 with generic message
- Invalid retry → 400 with retry limit details

## Authentication & Authorization

### API Key Authentication
- Standard x-api-key header validation
- Same authentication as existing profile endpoints
- Rate limiting applied per API key

### Access Control
- Users can only score profiles they have read access to
- Scoring jobs inherit profile access permissions
- Job results only accessible to job creator

## Rate Limiting

### Scoring Requests
- Maximum 10 scoring jobs per profile per hour
- Maximum 100 total scoring requests per API key per hour
- Failed jobs don't count against rate limits

### Job Status Checks
- Maximum 1000 job status requests per API key per hour
- No rate limiting on individual job polling (within reason)
