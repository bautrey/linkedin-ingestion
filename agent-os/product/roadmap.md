# Product Roadmap

> Last Updated: 2025-08-12
> Version: 2.2.0
> Status: 🚧 V1.85 IN PROGRESS - 60% complete, Tasks 1-3 finished, ready for async processing

## Current Status (July 2025)

**✅ COMPLETED PHASES:**
- **Phase 1**: Core MVP - LinkedIn profile ingestion with SQLite storage, FastAPI deployment
- **Phase 2**: Basic API endpoints - POST /ingest, GET /recent with API key authentication
- **Phase 3**: Production deployment - Railway hosting, API security, Make.com integration

**✅ COMPLETED: REST API Refactor**
- **Goal**: Convert action-based endpoints to resource-oriented design following Google AIP-121
- **Status**: ✅ FULLY COMPLETE - All tasks finished, Make.com integration updated
- **Spec**: @agent-os/specs/2025-07-25-rest-api-refactor/ (✅ COMPLETE)
- **Deliverables**: New REST endpoints, Make.com integration updated, production deployment verified

**✅ COMPLETED: Critical Workflow & API Integration Fixes**
- **Goal**: Fix fundamental workflow bypass issues and enhance API functionality
- **Status**: ✅ FULLY COMPLETE - All workflow and API fixes implemented and verified
- **Priority**: HIGH - Production system has incomplete profile data due to workflow bypass

**✅ COMPLETED: v1.6 Canonical Profile Models (Pydantic V2)**
- **Goal**: Clean internal data structures decoupled from external API format
- **Status**: ✅ FULLY COMPLETE - All Pydantic V2 models created, deprecation warnings resolved
- **Spec**: @agent-os/specs/2025-07-30-v1.6-canonical-profile-models/ (✅ COMPLETE)
- **Deliverables**: CanonicalProfile and CanonicalCompany models, zero deprecation warnings

**🚧 CURRENT DEVELOPMENT SEQUENCE: AI-Powered Profile Intelligence**
- **v1.7**: ✅ Cassidy-to-Canonical Adapter - Decouple from external API format (COMPLETE)
- **v1.8**: 🗑️ REMOVED - Keyword-based scoring system (replaced by V1.85 LLM approach)
- **v1.85/v1.88**: ✅ LLM-Based Profile Scoring - AI-driven executive role assessment with OpenAI (FULLY COMPLETE)
  - ✅ **Task 1**: Database Schema & Job Infrastructure (100% complete)
  - ✅ **Task 2**: OpenAI Integration & LLM Service (100% complete)
  - ✅ **Task 3**: API Endpoints Implementation (100% complete)
  - ✅ **Task 4**: Async Job Processing System (100% complete)
  - ✅ **Task 5**: Integration Testing & Production Deployment (100% complete)
  - ✅ **Task 6**: Template Management Integration (100% complete)
  - ✅ **Task 7**: Admin UI Integration (100% complete)
- **v1.9**: 🚧 Enhanced Admin UI - Task 3.1 COMPLETE, ready for Task 3.2+ (Template Versioning)

**📋 PHASE PROGRESS:**
- [x] Issue identification and analysis (Gregory Pascuzzi profile case)
- [x] Root cause analysis (REST API bypasses LinkedInWorkflow.process_profile())
- [x] Requirements specification for fixes
- [x] Implementation of workflow integration fixes
- [x] Add delete functionality and database methods
- [x] Implement smart profile management with update capabilities
- [x] Enhanced error handling and graceful conflict resolution (v1.5 spec)
- [x] Testing with full profile re-ingestion
- [x] Make.com integration verification

## Phase 1: Core MVP Functionality (2-3 weeks)

**Goal:** Establish basic LinkedIn profile ingestion with vector storage
**Success Criteria:** Can ingest LinkedIn profiles and store them in vector database with basic API access

### Must-Have Features

- [x] LinkedIn Profile URL Ingestion - Accept LinkedIn URLs and fetch profile data `L`
- [x] Supabase Vector Store Setup - Configure pgvector database for profile storage `M`
- [x] Basic Profile Storage - Store LinkedIn profiles with proper schema `M`
- [x] Profile Retrieval API - GET endpoint to retrieve stored profiles `S`
- [x] FastAPI Project Setup - Basic FastAPI application with proper structure `S`

### Should-Have Features

- [x] Input Validation - Pydantic models for request validation `S`
- [x] Basic Error Handling - Proper error responses for common failures `S`
- [x] Health Check Endpoint - Basic service health monitoring `XS`

### Dependencies

- Supabase account and project setup
- LinkedIn data access method (Cassidy AI integration)
- Basic FastAPI environment

## Phase 2: Company Data Integration (2-3 weeks)

**Goal:** Add automatic company profile collection for work experience entries
**Success Criteria:** Full candidate intelligence with both personal and company data

### Must-Have Features

- [x] Work Experience Parsing - Extract company information from LinkedIn profiles `M`
- [x] Company Profile Collection - Fetch company profiles for each work experience `L`
- [x] Relationship Mapping - Link profiles to companies with work history context `M`
- [x] Batch Company Processing - Handle multiple company fetches efficiently `M`

### Should-Have Features

- [x] Company Deduplication - Avoid storing duplicate company profiles `S`
- [x] Enhanced Data Schema - Improved database schema for relationships `S`
- [x] Progress Tracking - Show ingestion progress for multi-step process `M`

### Dependencies

- Phase 1 completion
- Company profile data source integration
- Enhanced database schema

## Phase 3: Testing & Documentation (1 week)

**Goal:** Comprehensive testing coverage and developer-friendly API documentation
**Success Criteria:** Reliable test coverage prevents production issues and API is well-documented

### Must-Have Features

- [x] Comprehensive API Integration Tests - Full endpoint testing with pytest-asyncio `M`
- [x] Error Scenario Testing - Test all failure modes and edge cases `M`
- [x] End-to-End Workflow Testing - Complete LinkedIn → DB → API flow validation `M`
- [x] OpenAPI/Swagger Documentation - Auto-generated interactive API docs `S`

### Should-Have Features

- [x] Postman Collection - Ready-to-use API testing collection `S`
- [x] Test Data Fixtures - Realistic test data that matches production scenarios `S`
- [ ] Performance Testing - Load testing for production readiness `M`
- [x] API Response Examples - Comprehensive examples for all endpoints `S`

## Phase 4: API Hardening & Performance (1-2 weeks)

**Goal:** Production-ready API with proper error handling and performance optimization
**Success Criteria:** Reliable API that can handle production loads with basic monitoring

### Must-Have Features

- [x] Comprehensive Error Handling - Proper error responses for all failure scenarios `M`
- [ ] Request/Response Logging - Detailed logging for debugging and audit `S`
- [x] Health Check Enhancements - Component-level health monitoring `S`
- [x] Input Validation - Enhanced security beyond Pydantic validation `S`

### Should-Have Features

- [ ] Request Logging - Structured logging for debugging and monitoring `S`
- [ ] Performance Metrics - Basic performance and usage tracking `S`
- [ ] API Usage Analytics - Track endpoint usage patterns `XS`

### Dependencies

- Phase 2 completion
- Production environment setup
- Authentication system design

## Phase 5: Advanced Features & Integration (2 weeks)

**Goal:** Enhanced functionality for downstream system integration
**Success Criteria:** Ready for integration with FIT scoring and PartnerConnect systems

### Must-Have Features

- [ ] Vector Similarity Search - Find similar profiles based on vector embeddings `M`
- [ ] Batch Profile Processing - Support for multiple profile ingestion `M`
- [ ] Data Export API - Flexible export formats for downstream systems `M`
- [x] Profile Update Logic - Smart update vs create handling for existing profiles `L`

### Should-Have Features

- [ ] Webhook Notifications - Optional notifications for completed ingestion `S`
- [ ] Profile Status Tracking - Detailed status for multi-step ingestion process `S`
- [ ] Data Validation - Enhanced validation for profile completeness `S`

### Dependencies

- Phase 3 completion
- Vector embedding strategy finalization
- Downstream system integration requirements

## Phase 6: MCP Server & AI Integration (1-2 weeks)

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

## 🚀 Future Vision & Strategic Direction

### **AI-Powered Talent Intelligence Platform**
Evolution beyond basic LinkedIn ingestion toward comprehensive candidate matching and assessment system for Fortium.

#### **Enhanced Search Capabilities**
- **Semantic Industry Matching**: OpenAI embeddings for nuanced "fintech" = "financial technology" understanding
- **Multi-Vector Search**: Combine job titles, companies, industries, skills for complex queries
- **Natural Language Queries**: "Find senior consultants similar to John who can travel internationally"
- **Experience-Level Awareness**: Distinguish senior vs junior roles in search results
- **Industry Clustering**: Advanced sector-based candidate groupings

#### **Professional Bio Generation Pipeline**
- **Data Fusion**: Merge LinkedIn + resume + personal preferences seamlessly
- **AI Content Generation**: GPT-4/Claude integration for professional bio creation
- **Template System**: Multiple format outputs for different use cases
- **PartnerConnect Integration**: Replace manual bio creation process

#### **Advanced Profile Management**
- **Periodic Re-ingestion**: Smart update routines for profile freshness
- **Change Detection**: Differential ingestion to preserve manual additions
- **Extended Schema**: Support non-LinkedIn data (availability, travel willingness)
- **Profile Merging**: Combine LinkedIn + PartnerConnect data intelligently

#### **Integration Architecture**
- **Fortium Candidate Fit Assessment**: Direct API integration for AI assessment
- **Fortium Engagement Fit Assessment**: Short-list evaluation capabilities
- **PartnerConnect Unified Profiles**: Seamless data flow between systems
- **Multi-Source Search**: Query across LinkedIn + PartnerConnect data simultaneously

#### **Use Case Examples**
- **Candidate Discovery**: "Who do we have with healthcare startup experience?"
- **Similarity Matching**: "Find people with experience similar to this prospect"
- **Complex Filtering**: "Senior developers with fintech experience at remote-friendly companies"
- **Bio Generation**: LinkedIn + resume + preferences → professional bio variants

#### **Technical Architecture Considerations**
- **Multiple Embedding Strategies**: Profile-level, skill-level, company-level vectors
- **Query Parsing Engine**: Natural language → structured search parameters
- **Real-time Updates**: Balance freshness vs API rate limits
- **Data Consistency**: Ensure reliable ingestion for mission-critical assessments

*This vision guides long-term architectural decisions while maintaining focus on current implementation priorities.*

---

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
