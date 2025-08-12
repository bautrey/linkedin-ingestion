# Spec Requirements Document

> Spec: V1.85 LLM-Based Profile Scoring
> Created: 2025-08-11
> Status: Planning

## Overview

Implement a flexible AI-driven profile scoring system that accepts custom evaluation prompts and applies them to LinkedIn profile data using OpenAI's API. This system will replace the removed V1.8 keyword-based scoring approach with a more powerful and adaptable LLM-driven evaluation framework.

## User Stories

### Primary User: Internal System Integration

As a **Fortium system developer**, I want to submit any custom evaluation prompt along with profile data, so that I can get structured AI-driven assessments for various candidate evaluation criteria (CIO/CTO fit, seniority levels, industry expertise, etc.).

The developer can send profile data with evaluation prompts (like the CIO/CTO/CISO evaluation prompt) and receive structured JSON responses with scores, breakdowns, and rationale, enabling dynamic and adaptable candidate assessment workflows.

### Secondary User: Business Development Analyst

As a **BD analyst**, I want to use different evaluation frameworks on the same candidate profiles, so that I can assess candidates against various client requirements without manual re-analysis.

The analyst can apply different scoring criteria to existing profiles, getting tailored assessments for specific client engagements or role requirements.

## Spec Scope

1. **LLM Integration API** - OpenAI API integration with configurable model selection and prompt handling
2. **Flexible Scoring Endpoint** - REST endpoint accepting profile data + custom evaluation prompts
3. **Structured Response Processing** - Parse and validate LLM JSON responses according to prompt specifications
4. **Profile Data Transformation** - Convert stored profile data into LLM-friendly text format for analysis
5. **Error Handling & Fallbacks** - Robust handling of LLM API failures, invalid responses, and prompt errors

## Out of Scope

- Hardcoded scoring algorithms or fixed evaluation criteria
- Profile data modification or storage (uses existing profile data)
- Real-time streaming responses (single API call pattern)
- Multi-profile batch scoring (single profile per request)
- Custom LLM model training or fine-tuning

## Expected Deliverable

1. **Functional Scoring API** - `/api/v1/profiles/{id}/score` endpoint that accepts evaluation prompts and returns structured AI assessments
2. **Configurable LLM Integration** - Working OpenAI API integration with proper error handling and response validation
3. **Complete Test Coverage** - Comprehensive tests including LLM API mocking, error scenarios, and response parsing validation

## Spec Documentation

- Tasks: @agent-os/specs/2025-08-11-v185-llm-profile-scoring/tasks.md
- Technical Specification: @agent-os/specs/2025-08-11-v185-llm-profile-scoring/sub-specs/technical-spec.md
- API Specification: @agent-os/specs/2025-08-11-v185-llm-profile-scoring/sub-specs/api-spec.md
- Database Schema: @agent-os/specs/2025-08-11-v185-llm-profile-scoring/sub-specs/database-schema.md
- Tests Specification: @agent-os/specs/2025-08-11-v185-llm-profile-scoring/sub-specs/tests.md
