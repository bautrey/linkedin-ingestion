# Spec Requirements Document

> Spec: REST API Refactor to Google AIP-121 Standards
> Created: 2025-07-25
> Status: Planning

## Overview

Refactor the LinkedIn Ingestion Service API from action-based endpoints to resource-oriented design following Google AIP-121 standards, enabling flexible profile search by LinkedIn URL, profile ID, and other parameters while maintaining backward compatibility during transition.

## User Stories

### Profile Search Integration
As a Make.com workflow developer, I want to search for profiles by LinkedIn URL so that I can retrieve previously ingested profile data for FIT assessment and JIRA integration without storing meaningless profile IDs in JIRA issues.

**Detailed Workflow**: Make.com receives a JIRA issue with a LinkedIn URL, searches the ingestion service to check if the profile already exists, retrieves the full profile data if found, sends it to FIT assessment service, and updates the JIRA issue with the assessment results.

### System Integration Flexibility  
As an internal system developer, I want to search profiles by various parameters (LinkedIn URL, profile ID, name) so that I can integrate the LinkedIn service with multiple Fortium systems that have different data access patterns.

**Detailed Workflow**: Various internal systems (PartnerConnect, evaluation tools, etc.) can query profiles using whatever identifier they have available, without requiring all systems to store and manage profile IDs.

### API Consistency
As a developer using the LinkedIn Ingestion Service, I want all endpoints to follow consistent REST patterns so that the API is predictable, well-documented, and easy to integrate with standard HTTP tools.

**Detailed Workflow**: Developers can use standard REST conventions to understand endpoint behavior, use OpenAPI documentation effectively, and build integrations that follow industry best practices.

## Spec Scope

1. **REST API Refactor** - Convert action-based URLs to resource-oriented design following Google AIP-121
2. **Profile Search Functionality** - Enable search by LinkedIn URL, profile ID, name, and company parameters  
3. **Make.com Integration Update** - Update existing Make.com integration to use new REST endpoints
4. **Response Format Standardization** - Ensure consistent response structures across all endpoints
5. **Query Parameter Support** - Implement filtering, pagination, and sorting capabilities

## Out of Scope

- Changes to database schema or data storage format
- Authentication mechanism changes (keep existing API key approach)
- FIT assessment service integration (separate future spec)
- Company profile search (focus on LinkedIn profiles only)
- Real-time data updates or webhooks

## Expected Deliverable

1. **Refactored API endpoints** following Google AIP-121 that pass all existing tests
2. **LinkedIn URL search capability** that returns profile data identical to current `/recent` endpoint format
3. **Updated Make.com integration** successfully using new endpoints with minimal configuration changes
