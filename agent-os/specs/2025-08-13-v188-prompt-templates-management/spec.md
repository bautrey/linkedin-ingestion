# Spec Requirements Document

> Spec: V1.88 Prompt Templates Management System
> Created: 2025-08-13
> Status: Planning

## Overview

Implement a database-driven prompt templates management system that allows saving, versioning, and retrieving evaluation prompts for LinkedIn profile scoring. This system will enable the upcoming V1.9 frontend UI to provide users with reusable prompt templates for different evaluation criteria (CTO/CIO/CISO fit, seniority assessment, industry expertise, etc.).

## User Stories

### Primary User: Business Development Analyst

As a **Talent analyst**, I want to save and reuse evaluation prompts for different scoring the fit of a candidate for fortium's model, so that I can quickly apply consistent scoring criteria without rewriting prompts each time.

The analyst can create, save, and select from predefined prompt templates when scoring candidates, ensuring consistent evaluation standards across different candidates.

### Secondary User: Internal System Integration

As a **Fortium system developer**, I want to programmatically access and manage prompt templates, so that I can build automated evaluation workflows that use standardized assessment criteria.

The developer can retrieve prompt templates via API to populate scoring requests and manage prompt templates programmatically for system integrations.

## Spec Scope

1. **Prompt Templates Database Schema** - Table design with versioning, categorization, and metadata support
2. **CRUD API Endpoints** - Full create, read, update, delete operations for prompt templates
3. **Template Categories & Roles** - Organization system for different evaluation types (CTO, CIO, CISO, etc.)
4. **Default Template Seeding** - Populate database with Fortium's standard evaluation prompts
5. **Integration with Scoring System** - Connect prompt templates to existing LLM scoring workflow
6. **Production Deployment** - Database migration and API deployment with immediate production validation

## Out of Scope

- Frontend UI components (reserved for V1.9)
- Advanced templating features (variables, conditional logic)
- Multi-user access controls (single-tenant for now)
- Template sharing or collaboration features
- Bulk template import/export (beyond seeding)

## Expected Deliverable

1. **Functional Template Management API** - Complete CRUD endpoints for prompt templates
2. **Database Schema Deployed** - Production-ready prompt_templates table with proper indexing
3. **Default Templates Seeded** - Fortium's CTO/CIO/CISO evaluation prompts loaded in production
4. **Scoring Integration** - Modified scoring endpoints to accept template IDs instead of raw prompts
5. **Production Validated** - All features tested and working in production environment
6. **Complete Test Coverage** - Comprehensive tests including database operations and API endpoints

## Critical Success Criteria

**Production-First Validation**: Given our history of local-vs-production discrepancies, this spec emphasizes rapid production deployment and validation:

1. **Database Migration Applied**: Schema changes deployed to production Supabase within first development session
2. **API Endpoints Live**: Template management endpoints accessible in production environment
3. **Real Data Testing**: Default templates created and tested with actual profile scoring in production
4. **End-to-End Validation**: Complete workflow from template creation to scoring job completion tested in production

## Spec Documentation

- Tasks: @agent-os/specs/2025-08-13-v188-prompt-templates-management/tasks.md
- Technical Specification: @agent-os/specs/2025-08-13-v188-prompt-templates-management/sub-specs/technical-spec.md
- Database Schema: @agent-os/specs/2025-08-13-v188-prompt-templates-management/sub-specs/database-schema.md
- API Specification: @agent-os/specs/2025-08-13-v188-prompt-templates-management/sub-specs/api-spec.md
- Tests Specification: @agent-os/specs/2025-08-13-v188-prompt-templates-management/sub-specs/tests.md
