# Product Roadmap

> Last Updated: 2025-07-25
> Version: 2.0.0
> Status: API Refactor Phase

## Current Status (July 2025)

**✅ COMPLETED PHASES:**
- **Phase 1**: Core MVP - LinkedIn profile ingestion with SQLite storage, FastAPI deployment
- **Phase 2**: Basic API endpoints - POST /ingest, GET /recent with API key authentication
- **Phase 3**: Production deployment - Railway hosting, API security, Make.com integration

**🚧 CURRENT PHASE: REST API Refactor**
- **Goal**: Convert action-based endpoints to resource-oriented design following Google AIP-121
- **Status**: Specification complete, ready for implementation
- **Spec**: @.agent-os/specs/2025-07-25-rest-api-refactor/

**📋 PHASE PROGRESS:**
- [x] Requirements gathering and specification
- [x] Technical architecture design
- [x] API endpoint specification
- [x] Comprehensive test planning
- [ ] Implementation (Next: Task breakdown creation)
- [ ] Make.com integration update
- [ ] Testing and deployment

## Phase 1: Core MVP Functionality (2-3 weeks)

**Goal:** Establish basic LinkedIn profile ingestion with vector storage
**Success Criteria:** Can ingest LinkedIn profiles and store them in vector database with basic API access

### Must-Have Features

- [ ] LinkedIn Profile URL Ingestion - Accept LinkedIn URLs and fetch profile data `L`
- [ ] Supabase Vector Store Setup - Configure pgvector database for profile storage `M`
- [ ] Basic Profile Storage - Store LinkedIn profiles with proper schema `M`
- [ ] Profile Retrieval API - GET endpoint to retrieve stored profiles `S`
- [ ] FastAPI Project Setup - Basic FastAPI application with proper structure `S`

### Should-Have Features

- [ ] Input Validation - Pydantic models for request validation `S`
- [ ] Basic Error Handling - Proper error responses for common failures `S`
- [ ] Health Check Endpoint - Basic service health monitoring `XS`

### Dependencies

- Supabase account and project setup
- LinkedIn data access method (Cassidy AI integration)
- Basic FastAPI environment

## Phase 2: Company Data Integration (2-3 weeks)

**Goal:** Add automatic company profile collection for work experience entries
**Success Criteria:** Full candidate intelligence with both personal and company data

### Must-Have Features

- [ ] Work Experience Parsing - Extract company information from LinkedIn profiles `M`
- [ ] Company Profile Collection - Fetch company profiles for each work experience `L`
- [ ] Relationship Mapping - Link profiles to companies with work history context `M`
- [ ] Batch Company Processing - Handle multiple company fetches efficiently `M`

### Should-Have Features

- [ ] Company Deduplication - Avoid storing duplicate company profiles `S`
- [ ] Enhanced Data Schema - Improved database schema for relationships `S`
- [ ] Progress Tracking - Show ingestion progress for multi-step process `M`

### Dependencies

- Phase 1 completion
- Company profile data source integration
- Enhanced database schema

## Phase 3: API Hardening & Performance (1-2 weeks)

**Goal:** Production-ready API with proper error handling and performance optimization
**Success Criteria:** Reliable API that can handle production loads with comprehensive monitoring

### Must-Have Features

- [ ] Comprehensive Error Handling - Proper error responses for all failure scenarios `M`
- [ ] Rate Limiting - Respect LinkedIn API limits and implement backoff `M`
- [ ] Async Processing - Non-blocking ingestion with status tracking `L`
- [ ] API Authentication - Secure API access for internal services `S`

### Should-Have Features

- [ ] Request Logging - Structured logging for debugging and monitoring `S`
- [ ] Performance Metrics - Basic performance and usage tracking `S`
- [ ] OpenAPI Documentation - Complete API documentation generation `XS`

### Dependencies

- Phase 2 completion
- Production environment setup
- Authentication system design

## Phase 4: Advanced Features & Integration (2 weeks)

**Goal:** Enhanced functionality for downstream system integration
**Success Criteria:** Ready for integration with FIT scoring and PartnerConnect systems

### Must-Have Features

- [ ] Vector Similarity Search - Find similar profiles based on vector embeddings `M`
- [ ] Batch Profile Processing - Support for multiple profile ingestion `M`
- [ ] Data Export API - Flexible export formats for downstream systems `M`
- [ ] Profile Update Logic - Smart update vs create handling for existing profiles `L`

### Should-Have Features

- [ ] Webhook Notifications - Optional notifications for completed ingestion `S`
- [ ] Profile Status Tracking - Detailed status for multi-step ingestion process `S`
- [ ] Data Validation - Enhanced validation for profile completeness `S`

### Dependencies

- Phase 3 completion
- Vector embedding strategy finalization
- Downstream system integration requirements

## Phase 5: MCP Server & AI Integration (1-2 weeks)

**Goal:** AI-ready service layer for LLM and MCP server integration
**Success Criteria:** Seamless integration with AI systems and LLM workflows

### Must-Have Features

- [ ] MCP Server Interface - Design API endpoints optimized for MCP server consumption `M`
- [ ] AI-Optimized Data Format - Structure data for optimal LLM processing `M`
- [ ] Profile Summary Generation - Generate embeddings and summaries for AI analysis `L`

### Should-Have Features

- [ ] Query Optimization - Optimized queries for AI use cases `S`
- [ ] Context Packaging - Package related data (profile + companies) for AI context `M`
- [ ] Integration Testing - Comprehensive testing with AI systems `S`

### Dependencies

- Phase 4 completion
- MCP server architecture decisions
- AI integration requirements from consuming systems

## Cross-Phase Considerations

### Testing Strategy
- Unit tests developed alongside each feature
- Integration tests for LinkedIn data processing
- End-to-end API testing for all endpoints

### Security & Compliance
- Secure API key management throughout all phases
- Data privacy considerations for LinkedIn profile storage
- Rate limiting and ethical data usage

### Documentation
- API documentation maintained with each phase
- Integration guides for downstream systems
- Operational runbooks for deployment and monitoring
