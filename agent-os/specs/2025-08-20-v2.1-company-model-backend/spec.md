# Spec Requirements Document

> Spec: V2.1 Company Model Backend Integration
> Created: 2025-08-20
> Status: Planning

## Overview

Complete the backend company data integration by connecting the existing company infrastructure (table, models) with the profile ingestion pipeline and API endpoints to capture, store, and expose the rich company information that Cassidy already provides but we're currently discarding, dramatically improving scoring accuracy by distinguishing between vastly different company contexts (e.g., "CTO at 50-person startup" vs "CTO at 284K-employee PwC").

## User Stories

### Enhanced Scoring Context

As a **Business Development Analyst**, I want profile scoring to utilize complete company context (employee count, industry, funding status, company size category), so that I can accurately differentiate between candidates from small startups versus enterprise corporations for client-specific engagement requirements.

**Detailed Workflow:** When scoring profiles, the system automatically includes rich company data (employee_count: 284478, employee_range: "10001+", industries: ["Professional Services"], specialties, funding_info, locations) in the scoring prompts, enabling nuanced evaluation that considers company scale, industry relevance, and organizational complexity in role assessments.

### Comprehensive Profile Intelligence

As a **System Integration Developer**, I want profile API responses to include full company details for each work experience entry, so that downstream systems can access complete professional context without additional API calls.

**Detailed Workflow:** Profile retrieval endpoints return embedded company objects containing detailed information (size metrics, industry classifications, location data, funding details) alongside each work experience, eliminating the need for separate company lookup calls and providing comprehensive intelligence for PartnerConnect integration.

### Company Data Centralization  

As an **Internal Fortium System**, I want standardized company profiles to be automatically collected and stored during profile ingestion, so that consistent company intelligence is available across all evaluation and partner management workflows.

**Detailed Workflow:** During LinkedIn profile ingestion, the system automatically extracts company information from work experiences, checks for existing company records, creates or updates company profiles with rich data from Cassidy, and establishes proper relationships between profiles and companies for future retrieval and analysis.

## Spec Scope

1. **Profile-Company Junction Integration** - Create profile_companies relationship table to link existing profiles with companies
2. **Enhanced Profile Ingestion** - Update ingestion pipeline to populate existing company table and create profile-company relationships  
3. **Company API Integration** - Modify profile endpoints to include full company context using existing company data
4. **Company Service Layer** - Implement service layer to manage company CRUD operations and profile relationships
5. **Data Population Strategy** - Migrate existing work experience data to populate company table and relationships

## Out of Scope

- Frontend company display interface (reserved for V2.2)
- Advanced company search and filtering features
- Company-specific scoring template modifications (reserved for V2.3)
- Historical company data migration for existing profiles
- Company logo or image processing

## Expected Deliverable

1. **Production-Ready Company Model** - Complete company data storage and retrieval with all existing profiles automatically enhanced with company context
2. **Enhanced Profile API Responses** - Profile endpoints returning embedded company data for immediate use in scoring and downstream systems
3. **Validated Company Integration** - All existing and new profile ingestion processes automatically capture and store company information with proper error handling and data validation

## Spec Documentation

- Tasks: @agent-os/specs/2025-08-20-v2.1-company-model-backend/tasks.md
- Technical Specification: @agent-os/specs/2025-08-20-v2.1-company-model-backend/sub-specs/technical-spec.md
- API Specification: @agent-os/specs/2025-08-20-v2.1-company-model-backend/sub-specs/api-spec.md
- Database Schema: @agent-os/specs/2025-08-20-v2.1-company-model-backend/sub-specs/database-schema.md
- Tests Specification: @agent-os/specs/2025-08-20-v2.1-company-model-backend/sub-specs/tests.md
