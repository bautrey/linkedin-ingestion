# Technical Specification

This is the technical specification for the spec detailed in @.agent-os/specs/2025-07-25-rest-api-refactor/spec.md

> Created: 2025-07-25
> Version: 1.0.0

## Technical Requirements

- Convert action-based endpoints (`/ingest`, `/recent`) to resource-oriented endpoints (`/profiles`, `/profiles/{id}`)
- Implement profile search by LinkedIn URL using query parameters
- Maintain API key authentication mechanism for all endpoints
- Ensure response format consistency across all endpoints
- Support pagination for profile listing endpoints
- Implement proper HTTP status codes following REST conventions
- Add OpenAPI documentation generation support

## Approach Options

**Option A: Gradual Migration with Dual Endpoints**
- Pros: Zero downtime, backward compatibility, allows testing
- Cons: Temporary code duplication, requires cleanup phase

**Option B: Complete Refactor with Breaking Changes** (Selected)
- Pros: Clean implementation, no legacy code debt, simpler architecture
- Cons: Requires coordinated deployment, breaks existing integrations

**Option C: Adapter Pattern Implementation**
- Pros: Maintains backward compatibility indefinitely, clean new API, gradual migration path
- Cons: Slightly more complex routing logic, maintains technical debt

**Rationale:** Option B provides the cleanest implementation since Make.com is the only existing integration and can be easily updated to use the new REST endpoints. This eliminates technical debt and results in a more maintainable codebase.

## API Design Specification

### Resource-Oriented Endpoints (New)

**GET /api/v1/profiles**
- Purpose: List all profiles with filtering capabilities
- Query Parameters: 
  - `linkedin_url`: Filter by LinkedIn URL (enables search functionality)
  - `company`: Filter by company name
  - `name`: Filter by person name
  - `limit`: Pagination limit (default: 50, max: 100)
  - `offset`: Pagination offset (default: 0)
- Response: Array of profile objects with pagination metadata
- Authentication: API key required

**GET /api/v1/profiles/{id}**
- Purpose: Retrieve specific profile by ID
- Parameters: Profile ID in URL path
- Response: Single profile object
- Authentication: API key required

**POST /api/v1/profiles**
- Purpose: Create new profile (ingestion)
- Body: LinkedIn profile data
- Response: Created profile object with generated ID
- Authentication: API key required

## Data Flow Architecture

```
REST Endpoints → Resource Controllers → Business Logic → Database
```

## External Dependencies

- **No new external dependencies required**
- **Justification:** Refactor uses existing FastAPI capabilities for routing, validation, and response formatting

## Implementation Strategy

1. Create new resource-oriented controller structure
2. Implement core business logic in service layer
3. Replace existing endpoints with new REST endpoints
4. Update Make.com integration to use new endpoints
5. Ensure consistent error handling and response formats
6. Add comprehensive OpenAPI documentation
