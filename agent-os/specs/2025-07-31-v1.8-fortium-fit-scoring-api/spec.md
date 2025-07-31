# V1.8 Fortium Fit Scoring API

## Overview

Implement a role-aware candidate fit scoring API endpoint that provides deterministic scoring for CIO, CTO, and CISO roles with database-driven configuration, detailed category scoring, textual summaries, recommendations, and alternative role suggestions.

## Goals

- Create a flexible scoring system for Fortium partners
- Support different scoring algorithms per role
- Enable real-time configurability without redeployments

## Features

- **Endpoint**: `GET /api/v1/profiles/{profile_id}/score?role={role}`
- **Role-Aware Scoring**: Support CIO, CTO, CISO roles
- **Database-Driven Configuration**: Store scoring algorithms and thresholds
- **Comprehensive Response**: Detailed scores, summaries, and recommendations

## Success Criteria

- Deterministic results: Same inputs always produce identical outputs
- All production tests pass and zero warnings

## Dependencies

- Fully functioning LinkedIn ingestion system
- Up-to-date Supabase database setup

## Phases and Steps

See detailed task breakdown: @agent-os/specs/2025-07-31-v1.8-fortium-fit-scoring-api/tasks.md

## Documentation References

- **Technical Specification**: @agent-os/specs/2025-07-31-v1.8-fortium-fit-scoring-api/sub-specs/technical-spec.md
- **Database Schema**: @agent-os/specs/2025-07-31-v1.8-fortium-fit-scoring-api/sub-specs/database-schema.md
- **API Specification**: @agent-os/specs/2025-07-31-v1.8-fortium-fit-scoring-api/sub-specs/api-spec.md
- **Test Specification**: @agent-os/specs/2025-07-31-v1.8-fortium-fit-scoring-api/sub-specs/tests.md
- **Task Breakdown**: @agent-os/specs/2025-07-31-v1.8-fortium-fit-scoring-api/tasks.md
