# Batch Enhanced Profile Ingestion API Endpoint

## Overview

This document describes the new batch enhanced profile ingestion endpoint that was implemented as part of task 2.1.5 (API Endpoint Implementation).

## Endpoint Details

- **URL**: `POST /api/v1/profiles/batch-enhanced`
- **Authentication**: Requires valid API key in `X-API-Key` header
- **Content-Type**: `application/json`

## Request Format

```json
{
  "profiles": [
    {
      "linkedin_url": "https://www.linkedin.com/in/username1/",
      "suggested_role": "CTO",
      "name": "Optional Name",
      "include_companies": true
    },
    {
      "linkedin_url": "https://www.linkedin.com/in/username2/", 
      "suggested_role": "CIO",
      "name": "Optional Name",
      "include_companies": true
    }
  ],
  "max_concurrent": 3
}
```

### Request Parameters

- `profiles` (required): Array of profile objects to ingest (min: 1, max: 10)
  - `linkedin_url` (required): Valid LinkedIn profile URL
  - `suggested_role` (required): One of "CTO", "CIO", or "CISO"
  - `name` (optional): Override name for the profile
  - `include_companies` (optional, default: true): Whether to include company processing
- `max_concurrent` (optional, default: 3): Concurrent processing limit (1-5)

## Response Format

```json
{
  "batch_id": "uuid-string",
  "total_requested": 2,
  "successful": 1,
  "failed": 1,
  "results": [
    {
      "id": "profile-id",
      "name": "Profile Name", 
      "url": "https://www.linkedin.com/in/username1/",
      "position": "Chief Technology Officer",
      "about": "Profile description...",
      "experience": [...],
      "education": [...],
      "certifications": [...],
      "companies_processed": [
        {
          "id": "company-id",
          "company_name": "Company Name",
          "...": "other company fields"
        }
      ],
      "pipeline_metadata": {
        "pipeline_id": "uuid",
        "companies_found": 3,
        "has_embeddings": true,
        "processing_time": "2023-12-07T10:30:00Z"
      },
      "created_at": "2023-12-07T10:30:00Z"
    },
    {
      "id": "",
      "name": "Failed: https://www.linkedin.com/in/username2/",
      "url": "https://www.linkedin.com/in/username2/",
      "position": "Processing Failed",
      "about": "Error: Profile not found",
      "pipeline_metadata": {
        "status": "failed",
        "errors": [
          {
            "error": "Profile not found",
            "details": "LinkedIn profile is private or does not exist"
          }
        ]
      },
      "created_at": "2023-12-07T10:30:00Z"
    }
  ],
  "started_at": "2023-12-07T10:30:00Z",
  "completed_at": "2023-12-07T10:30:15Z", 
  "processing_time_seconds": 15.3
}
```

## Features

### Enhanced Pipeline Integration

The endpoint uses the enhanced LinkedIn data pipeline (`LinkedInDataPipeline`) which provides:

- **Company Processing**: Automatically processes company information from work experience
- **Batch Processing**: Handles multiple profiles concurrently for efficiency
- **Error Handling**: Graceful handling of individual profile failures
- **Embeddings Generation**: Generates vector embeddings for profiles and companies
- **Database Storage**: Stores profiles and companies in Supabase with pgvector support

### Validation

- Maximum 10 profiles per batch to prevent overloading
- Maximum 5 concurrent processes to control resource usage
- LinkedIn URL validation
- Required role type validation
- API key authentication

### Error Handling

- Individual profile failures don't stop the batch
- Detailed error information for failed profiles
- Standardized error response format
- Comprehensive logging for debugging

## Usage Examples

### Successful Batch Request

```bash
curl -X POST "http://localhost:8000/api/v1/profiles/batch-enhanced" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "profiles": [
      {
        "linkedin_url": "https://www.linkedin.com/in/example1/",
        "suggested_role": "CTO"
      },
      {
        "linkedin_url": "https://www.linkedin.com/in/example2/", 
        "suggested_role": "CIO"
      }
    ],
    "max_concurrent": 2
  }'
```

### Error Responses

#### Validation Error (422)
```json
{
  "error_code": "VALIDATION_ERROR",
  "message": "Request validation failed",
  "details": {
    "endpoint": "/api/v1/profiles/batch-enhanced",
    "method": "POST",
    "total_errors": 1
  },
  "validation_errors": [
    {
      "field": "profiles",
      "message": "List must have at least 1 item",
      "invalid_value": [],
      "error_type": "too_short"
    }
  ]
}
```

#### Unauthorized (403)
```json
{
  "error_code": "UNAUTHORIZED", 
  "message": "Invalid or missing API key",
  "details": {
    "provided_key_length": 0,
    "expected_key_present": true
  }
}
```

## Performance Considerations

- **Batch Size**: Limited to 10 profiles to balance throughput and responsiveness
- **Concurrency**: Configurable up to 5 concurrent processes to prevent overloading external services
- **Timeouts**: Individual profile processing has timeouts to prevent hanging
- **Rate Limiting**: Respects LinkedIn and external API rate limits

## Testing

The endpoint includes comprehensive tests covering:

- Successful batch processing with mixed results
- Validation error scenarios
- Authentication requirements  
- Edge cases and error conditions

Test files:
- `tests/test_batch_endpoint_basic.py` - Basic functionality tests
- `tests/test_batch_enhanced_endpoint.py` - Comprehensive integration tests

## Implementation Details

### Models

- `BatchProfileCreateRequest`: Pydantic model for request validation
- `BatchProfileResponse`: Structured response with batch metadata
- `ProfileResponse`: Enhanced with pipeline metadata for batch results

### Controller Method

- `ProfileController.batch_create_profiles_enhanced()`: Main processing logic
- Uses `LinkedInDataPipeline.batch_ingest_profiles_with_companies()`
- Handles result aggregation and error formatting

### Database Integration

- Stores profiles using existing `SupabaseClient` methods
- Leverages existing profile and company storage patterns
- Maintains data consistency across batch operations

## Future Enhancements

- **Webhooks**: Async processing with webhook callbacks for long-running batches
- **Progress Tracking**: Real-time progress updates via WebSocket
- **Batch Status Endpoint**: Query batch processing status by batch_id
- **Retry Logic**: Automatic retry of failed profiles with exponential backoff
- **Analytics**: Batch processing metrics and success rate tracking
