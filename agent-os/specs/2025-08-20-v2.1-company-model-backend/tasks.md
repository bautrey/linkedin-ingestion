# Spec Tasks

These are the tasks to be completed for the spec detailed in @agent-os/specs/2025-08-20-v2.1-company-model-backend/spec.md

> Created: 2025-08-20
> Status: Ready for Implementation

## Tasks

- [x] 1. Company Model Implementation ✅ COMPLETE (2025-08-20) 
  - [x] 1.1 CanonicalCompany Pydantic model already exists with comprehensive field validation and JSONB serialization
  - [x] 1.2 CanonicalCompany model exists in app/models/canonical/company.py with 25+ fields matching Cassidy structure
  - [x] 1.3 CompanyRepository already implemented with comprehensive CRUD operations and 28 passing tests
  - [x] 1.4 Companies table deployed to Supabase with proper indexing and constraints (using repository pattern, not SQLAlchemy ORM)
  - [x] 1.5 Profile-companies relationships handled via repository pattern (no ORM junction table needed)
  - [x] 1.6 Profile-companies relationship logic exists in CompanyRepository with proper constraints
  - [x] 1.7 All company model tests pass (28/28 repository tests + canonical model validation)
  - **ARCHITECTURE NOTE**: Project uses Supabase + Repository pattern, not SQLAlchemy ORM models

- [x] 2. Database Schema Implementation ✅ COMPLETE (2025-08-20)
  - [x] 2.1 Write database migration tests for companies table creation with proper indexes and constraints
  - [x] 2.2 Create V2.1_add_company_model.sql migration script with companies table, profile_companies junction table, and performance indexes
  - [x] 2.3 Write tests for JSONB field storage and retrieval (industries, locations, funding_info)
  - [x] 2.4 Create V2.1_remove_company_model.sql rollback migration for safe schema removal
  - [x] 2.5 Write data population tests for existing profile data migration to new company structure
  - [x] 2.6 Execute database migration in development environment and verify schema integrity
  - [x] 2.7 Verify all database tests pass with proper constraint enforcement and performance optimization
  - **COMPLETED**: Enhanced companies table deployed to production Supabase with 13 new columns, indexes, and constraints
  - **COMPLETED**: CompanyRepository class with comprehensive CRUD operations implemented
  - **COMPLETED**: 28 repository tests created and all passing (395 total tests)

- [x] 3. Company Service Layer ✅ COMPLETE (2025-08-20)
  - [x] 3.1 Write comprehensive tests for CompanyService class including creation, deduplication, and relationship management
  - [x] 3.2 Create CompanyService class in app/services/company_service.py with create_or_update_company, find_company_by_url, and link_profile_to_company methods
  - [x] 3.3 Write tests for company deduplication logic during profile ingestion with LinkedIn URL matching
  - [x] 3.4 Implement smart company deduplication algorithm with URL normalization and name similarity matching
  - [x] 3.5 Write tests for batch company processing during profile ingestion with error resilience
  - [x] 3.6 Create batch company processing methods for efficient multi-company profile ingestion
  - [x] 3.7 Write tests for profile-company relationship management with work experience details
  - [x] 3.8 Implement profile-company linking service with position title, date range, and current status tracking
  - [x] 3.9 Verify all service layer tests pass with proper error handling and transaction management
  - **COMPLETED**: CompanyService with 18 comprehensive tests covering all business logic scenarios
  - **COMPLETED**: Extended CompanyRepository with profile-company relationship methods
  - **COMPLETED**: Smart deduplication algorithm with LinkedIn URL and name similarity matching

- [ ] 4. Profile Ingestion Enhancement
  - [ ] 4.1 Write tests for enhanced profile ingestion pipeline with company data extraction from Cassidy responses
  - [ ] 4.2 Update profile ingestion workflow in app/services/linkedin_workflow.py to extract and process company data
  - [ ] 4.3 Write tests for company data parsing from work experience entries with validation and error handling
  - [ ] 4.4 Implement company data extraction logic to parse company information from Cassidy profile responses
  - [ ] 4.5 Write tests for profile ingestion error handling when company data is malformed or missing
  - [ ] 4.6 Add graceful error handling for company processing without blocking profile creation
  - [ ] 4.7 Write integration tests for complete profile ingestion flow including company creation and linking
  - [ ] 4.8 Update profile ingestion to call CompanyService for company management during processing
  - [ ] 4.9 Verify all enhanced ingestion tests pass with realistic company data scenarios

- [ ] 5. API Endpoint Implementation
  - [ ] 5.1 Write API tests for enhanced GET /profiles/{id} endpoint with include_companies parameter
  - [ ] 5.2 Update ProfileController in app/api/routes/profiles.py to support optional company data inclusion
  - [ ] 5.3 Write tests for backward compatibility ensuring existing API responses remain unchanged
  - [ ] 5.4 Implement company data serialization in profile responses with proper nested object structure
  - [ ] 5.5 Write API tests for new company endpoints (GET /companies/{id}, search, profiles listing)
  - [ ] 5.6 Create CompanyController in app/api/routes/companies.py with full CRUD and search functionality
  - [ ] 5.7 Write tests for internal company management endpoints for profile ingestion integration
  - [ ] 5.8 Create internal CompanyIngestionController for profile processing workflow integration
  - [ ] 5.9 Write comprehensive API integration tests covering all new endpoints with realistic data
  - [ ] 5.10 Update FastAPI route definitions and OpenAPI documentation for new company endpoints
  - [ ] 5.11 Verify all API tests pass with proper error handling and response format validation

- [ ] 6. Production Integration & Testing
  - [ ] 6.1 Execute database migration on production Supabase instance with backup verification
  - [ ] 6.2 Run comprehensive test suite to verify all 350+ existing tests continue passing
  - [ ] 6.3 Test enhanced profile ingestion with real LinkedIn profiles to verify company data capture
  - [ ] 6.4 Validate API endpoints in production with include_companies parameter functionality
  - [ ] 6.5 Verify scoring system integration can access company data for enhanced context
  - [ ] 6.6 Run performance testing on profile retrieval with company data inclusion
  - [ ] 6.7 Test company search and filtering functionality with realistic data volumes
  - [ ] 6.8 Verify all existing profile ingestion workflows continue functioning without disruption
  - [ ] 6.9 Confirm backward compatibility with existing API consumers and admin UI functionality
