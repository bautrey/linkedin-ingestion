# Spec Requirements Document

> Spec: Company Processing Consolidation
> Created: 2025-08-22
> Status: Planning

## Overview

Consolidate duplicate company processing logic between LinkedInDataPipeline and ProfileController into a single unified path in ProfileController.create_profile method, eliminating code duplication and establishing "one model, one way in and one way out" for LinkedIn profile and company ingestion.

## User Stories

### System Integration Developer

As a system integration developer, I want a single, reliable entry point for LinkedIn profile and company processing, so that I can trust the data consistency and don't have to worry about which processing path is being used.

**Workflow:** Developer calls POST /api/v1/profiles with include_companies=true and receives complete profile with associated company data through a single, well-tested code path that combines the working elements of both current approaches.

### Fortium Business Development Analyst

As a BD analyst, I want consistent company data collection every time a LinkedIn profile is processed, so that I can rely on having complete candidate intelligence without worrying about which backend processing method was used.

**Workflow:** Analyst submits LinkedIn URLs through Make.com integration, and all profiles consistently receive comprehensive company data processing through the consolidated pathway.

## Spec Scope

1. **Code Analysis** - Systematic analysis of LinkedInDataPipeline vs ProfileController company processing to identify working components
2. **Unified Implementation** - Merge working logic from both approaches into ProfileController.create_profile method
3. **LinkedInDataPipeline Removal** - Remove LinkedInDataPipeline initialization and calls from ProfileController critical path
4. **Production Testing** - Validate consolidated approach works with real Cassidy API and database operations
5. **Progress Monitoring** - Implement database monitoring to track company processing completion during testing

## Out of Scope

- Modifying the external API endpoints (POST /api/v1/profiles remains unchanged)
- Changing the database schema or company data models
- Updating other systems that might use LinkedInDataPipeline (if any exist)
- Performance optimization (focus on functionality consolidation)

## Expected Deliverable

1. **Single Company Processing Path** - ProfileController.create_profile handles all LinkedIn profile and company processing without LinkedInDataPipeline dependencies
2. **Production-Validated Solution** - Confirmed working in production with real Cassidy API, database monitoring showing successful company data ingestion
3. **Clean Codebase** - LinkedInDataPipeline removed from critical path with no duplicate company processing logic

## Spec Documentation

- Tasks: @agent-os/specs/2025-08-22-company-processing-consolidation/tasks.md
- Technical Specification: @agent-os/specs/2025-08-22-company-processing-consolidation/sub-specs/technical-spec.md
- Tests Specification: @agent-os/specs/2025-08-22-company-processing-consolidation/sub-specs/tests.md
