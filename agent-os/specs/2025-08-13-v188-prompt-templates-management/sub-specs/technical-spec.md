# Technical Specification

> Spec: V1.88 Prompt Templates Management System
> Document: Technical Specification
> Created: 2025-08-13

## Architecture Overview

The prompt templates management system will extend the existing LinkedIn ingestion service with a new data layer and API endpoints for managing reusable evaluation prompts. The system integrates with the existing LLM scoring infrastructure to provide template-based scoring workflows.

## System Integration Points

### Existing Systems
- **LLM Scoring Service** (`app/services/llm_scoring_service.py`) - Will be extended to accept template IDs
- **Scoring Controllers** (`app/controllers/scoring_controllers.py`) - Will support template-based scoring requests
- **Supabase Database** - New prompt_templates table alongside existing scoring_jobs table
- **FastAPI Application** (`main.py`) - New template management endpoints

### New Components
- **PromptTemplate Model** - Pydantic model for template data validation
- **PromptTemplateService** - Business logic for template operations
- **Template Controllers** - API request/response handling
- **Database Migration** - Schema deployment for prompt_templates table

## Data Flow Architecture

```
Template Creation Flow:
UI/API Request → Template Controller → Template Service → Database → Response

Template Retrieval Flow:
UI/API Request → Template Controller → Template Service → Database → Response

Scoring with Template Flow:
Scoring Request (template_id) → Scoring Controller → Template Service (get template) → LLM Scoring Service → Database
```

## Technical Implementation Strategy

### Database Layer
- **Technology**: Supabase PostgreSQL with existing connection patterns
- **Schema**: Single `prompt_templates` table with JSONB metadata field
- **Migration Strategy**: Follow existing migration pattern with Supabase CLI deployment
- **Indexing**: Primary key (UUID), category index, active templates index

### Service Layer
- **Pattern**: Follow existing service pattern from `llm_scoring_service.py`
- **Error Handling**: Comprehensive exception handling with proper HTTP status codes
- **Validation**: Pydantic models for all template operations
- **Logging**: Structured logging consistent with existing services

### API Layer
- **Framework**: FastAPI with existing authentication middleware
- **Endpoints**: RESTful design following existing API patterns
- **Documentation**: Automatic OpenAPI generation
- **Authentication**: x-api-key header (consistent with existing endpoints)

### Integration Strategy
- **LLM Service Extension**: Modify existing `LLMScoringService.score_profile()` to accept template objects
- **Backward Compatibility**: Maintain existing prompt-based scoring while adding template support
- **Controller Extension**: Add template resolution to existing scoring controllers

## Production Deployment Strategy

### Database Migration
1. **Create Migration File**: Follow existing pattern (`supabase/migrations/`)
2. **Local Testing**: Verify migration with local Supabase setup
3. **Production Deployment**: Use `supabase db push --password` (learned from V1.85 experience)
4. **Validation**: Immediate production testing of table creation and constraints

### Application Deployment
1. **Railway Auto-Deploy**: Leverage existing Git-based deployment
2. **Environment Variables**: No new variables needed (uses existing Supabase connection)
3. **Health Check**: Extend existing health check to include template system
4. **Production Testing**: Immediate API endpoint validation

### Default Data Seeding
1. **Migration Seeding**: Include default Fortium templates in migration
2. **Production Verification**: Test template retrieval and scoring integration
3. **End-to-End Testing**: Complete workflow validation with real profile data

## Security Considerations

### Authentication
- **Existing API Key System**: No changes to authentication model
- **Template Access**: Single-tenant model (all templates accessible to authenticated requests)
- **Data Validation**: Pydantic models prevent malicious template content

### Data Privacy
- **Template Content**: Store evaluation prompts as plain text (no sensitive data)
- **Audit Trail**: Created/updated timestamps for template changes
- **Production Environment**: Same security model as existing scoring system

## Performance Considerations

### Database Performance
- **Indexes**: Efficient querying by category, active status
- **Connection Pooling**: Leverage existing Supabase connection management
- **Query Optimization**: Simple CRUD operations, minimal performance impact

### API Performance
- **Caching**: Templates are relatively static, suitable for caching if needed
- **Response Size**: Small JSON objects, minimal bandwidth impact
- **Concurrent Access**: Stateless operations, high concurrency support

## Error Handling Strategy

### Database Errors
- **Connection Failures**: Consistent with existing database error handling
- **Constraint Violations**: Proper validation before database operations
- **Migration Errors**: Comprehensive testing before production deployment

### API Errors
- **Validation Errors**: 400 Bad Request with detailed error messages
- **Not Found**: 404 for non-existent templates
- **Server Errors**: 500 with proper logging for debugging

### Integration Errors
- **Template Resolution**: Graceful fallback for missing templates
- **Scoring Integration**: Clear error messages for template-related scoring failures

## Monitoring and Observability

### Logging Strategy
- **Structured Logging**: JSON format consistent with existing services
- **Log Levels**: INFO for operations, ERROR for failures, DEBUG for development
- **Context**: Include template IDs, operation types, and user context

### Health Monitoring
- **Health Check Extension**: Add template system status to existing `/health` endpoint
- **Database Connectivity**: Verify prompt_templates table accessibility
- **Basic Functionality**: Template CRUD operations validation

## Technology Stack Alignment

### Existing Stack Compatibility
- **FastAPI**: Consistent with existing API framework
- **Pydantic V2**: Following project's Pydantic V2 migration
- **Supabase**: Using established database connection patterns
- **pytest**: Testing framework consistent with existing test suite

### Development Environment
- **Local Development**: Same virtual environment and dependency management
- **Testing**: Existing pytest configuration and async testing patterns
- **Production**: Railway deployment with existing CI/CD pipeline
