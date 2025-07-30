# Spec Requirements Document

> Spec: Canonical Profile Models
> Created: 2025-07-30
> Status: Planning

## Overview

Create clean, Pydantic V2-compliant internal data models for LinkedIn profiles and companies to serve as a stable, internal data contract, decoupling the application from any specific external data provider's format.

## User Stories

### Decoupled Internal Models

As a system integration developer, I want to work with a stable, well-defined internal data model, so that changes in external data provider APIs do not break my application.

**Detailed Workflow**: When the Cassidy API changes its response structure, the adapter layer is updated, but the internal `CanonicalProfile` model remains unchanged, ensuring no downstream code needs to be modified.

### Consistent Data Structures

As a backend developer, I want all profile and company data to conform to a strict, consistent schema, so that I can write reliable business logic without worrying about data inconsistencies.

**Detailed Workflow**: The `CanonicalProfile` model enforces that `linkedin_url` is always a valid Pydantic `AnyUrl` and that all `work_history` entries are valid `CanonicalCompany` objects, preventing malformed data from entering the system.

## Spec Scope

1.  **`CanonicalProfile` Model** - Pydantic V2 model for LinkedIn profiles
2.  **`CanonicalCompany` Model** - Pydantic V2 model for company profiles
3.  **Strict Validation** - All fields use proper data types with strict validation
4.  **Deprecation-Free** - No Pydantic V1 deprecation warnings

## Out of Scope

-   Cassidy-to-Canonical adapter implementation (v1.7)
-   API exposure of Canonical models
-   Database schema changes

## Expected Deliverable

1.  `app/models/canonical.py` created with `CanonicalProfile` and `CanonicalCompany` models
2.  All Pydantic V1 deprecation warnings in the application are resolved
3.  The application test suite passes with the new models

## Spec Documentation

- Tasks: @agent-os/specs/2025-07-30-v1.6-canonical-profile-models/tasks.md
- Technical Specification: @agent-os/specs/2025-07-30-v1.6-canonical-profile-models/sub-specs/technical-spec.md
- Tests Specification: @agent-os/specs/2025-07-30-v1.6-canonical-profile-models/sub-specs/tests.md

