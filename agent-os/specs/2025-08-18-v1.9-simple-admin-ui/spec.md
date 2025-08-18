# Spec Requirements Document

> Spec: Simple Admin UI with Node.js + Express + Bootstrap 5
> Created: 2025-08-18
> Status: Planning

## Overview

Implement a lightweight, fast-to-develop administrative web interface for the LinkedIn Ingestion Service using Node.js + Express + Bootstrap 5 + vanilla JavaScript. This replaces the previously planned complex Next.js + shadcn/ui approach with a simple, maintainable solution optimized for rapid development and a small user base.

## User Stories

### Profile Browsing and Management

As a Business Development Analyst, I want to view and search LinkedIn profiles in a comprehensive table, so that I can quickly browse collected profiles and assess candidate quality without needing API knowledge.

The interface will provide a sortable, filterable table with single-line entries showing key profile information (name, current title, company, location, ingestion date, score). Columns will be adjustable in width and sortable by appropriate data types. Clicking on a profile will show a detailed modal or dedicated page with complete LinkedIn data formatted for easy reading.

### Profile Scoring Management

As a Business Development Analyst, I want to score or re-score profiles directly in the admin interface, so that I can evaluate candidates using our AI scoring system without using the API directly.

The interface will provide scoring functionality with template selection, the ability to trigger new scoring jobs, view scoring results with detailed breakdowns, and re-score profiles with different templates as needed.

### Template Management

As a System Integration Developer, I want to manage prompt templates through the admin interface, so that I can create, edit, and version control scoring templates without database access.

The interface will provide full CRUD operations for templates, template versioning capabilities, the ability to save new versions from existing templates, and template selection for scoring operations.

### LinkedIn Profile Ingestion

As a Business Development Analyst, I want to ingest new LinkedIn profiles by providing URLs, so that I can add new candidates to the system directly through the admin interface.

The interface will provide a form to enter LinkedIn profile URLs, trigger ingestion jobs, monitor ingestion progress, and show results with error handling for invalid URLs or ingestion failures.

## Spec Scope

1. **Profile Table Interface** - Comprehensive sortable/filterable table with single-line entries and adjustable column widths
2. **Profile Detail View** - Modal or dedicated page showing complete profile data in readable format
3. **Profile Scoring System** - Score and re-score profiles with template selection and results display
4. **Template Management** - Full CRUD operations for prompt templates with versioning capabilities
5. **LinkedIn Ingestion Interface** - Form-based profile ingestion from LinkedIn URLs with progress monitoring
6. **Dashboard Overview** - System statistics and recent activity with real-time updates

## Out of Scope

- Complex React/Next.js framework dependencies
- Advanced user authentication and role management
- Company-centric browsing (nice-to-have but not primary use case)
- Mobile app or PWA functionality
- Advanced analytics or reporting dashboards
- Bulk import/export functionality
- Custom LinkedIn page recreation (use modal/dedicated page with our data)

## Expected Deliverable

1. Professional profile management table with comprehensive sorting, filtering, and column adjustment capabilities showing all ingested profiles
2. Complete scoring system integration allowing direct profile scoring with template selection and detailed results display
3. Template management interface with full CRUD operations and versioning for prompt template administration
4. LinkedIn ingestion capability allowing new profile addition via URL with progress monitoring and error handling
