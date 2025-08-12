# Technical Specification

This is the technical specification for the spec detailed in @agent-os/specs/2025-08-11-v185-llm-profile-scoring/spec.md

> Created: 2025-08-11
> Version: 1.0.0

## Technical Requirements

- **OpenAI Integration**: Direct API integration with OpenAI ChatGPT models (GPT-4, GPT-3.5-turbo) for profile evaluation
- **Flexible Prompt System**: Accept arbitrary evaluation prompts in request body without hardcoded prompt templates
- **JSON Response Parsing**: Robust parsing and validation of structured JSON responses from LLM API
- **Profile Data Serialization**: Convert existing LinkedIn profile models to comprehensive text format for LLM analysis
- **Error Handling**: Comprehensive error handling for API failures, invalid JSON responses, and malformed prompts
- **API Key Management**: Secure OpenAI API key storage and configuration via environment variables
- **Response Validation**: Schema validation for expected LLM response formats based on prompt requirements
- **Performance Optimization**: Request/response caching and rate limiting to manage OpenAI API costs

## Approach Options

**Option A:** Synchronous API Pattern
- Pros: Simple implementation, immediate response, easy error handling
- Cons: Potential timeout issues with slow LLM responses, blocking request handling

**Option B:** Asynchronous Job Pattern (Selected)
- Pros: Non-blocking, handles slow LLM responses, scalable, better user experience
- Cons: More complex implementation, requires job status tracking

**Rationale:** LLM API calls can take 5-30 seconds, making synchronous requests impractical for web API usage. Asynchronous pattern allows clients to poll for results and prevents request timeouts.

## External Dependencies

- **openai** (>=1.0.0) - Official OpenAI Python client for GPT API integration
- **Justification:** Required for ChatGPT API access, handles authentication, retries, and response formatting
- **pydantic** (existing) - Enhanced models for LLM request/response validation
- **Justification:** Extend existing validation patterns for complex LLM response schemas

## Architecture Components

### LLM Service Layer
- `LLMScoringService` - Core service for OpenAI API integration
- Prompt formatting and profile data preparation  
- Response parsing and validation
- Error handling and retry logic

### API Controller
- `POST /api/v1/profiles/{id}/score` - Initiate scoring request
- `GET /api/v1/scoring-jobs/{job_id}` - Check scoring job status
- Request validation and response formatting

### Data Models
- `ScoringRequest` - Input validation for prompt and parameters
- `ScoringResponse` - Structured response from LLM evaluation
- `ScoringJob` - Job status tracking for asynchronous processing

### Database Schema
- `scoring_jobs` table - Track asynchronous job status and results
- Indexes on profile_id and job_id for efficient querying
