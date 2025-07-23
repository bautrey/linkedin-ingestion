# Feature Spec: Cassidy Integration Discovery and Test Data Preparation

## Overview

This feature establishes the foundation for LinkedIn profile ingestion by implementing Cassidy AI workflow integration and preparing comprehensive test datasets. Based on analysis of existing Cassidy blueprints, this spec covers both profile and company data workflows with robust error handling and data validation.

## Requirements

### Functional Requirements

1. **Cassidy Workflow Integration**
   - Implement HTTP client for Cassidy webhook endpoints
   - Support both profile and company scraping workflows
   - Handle async workflow execution with polling
   - Parse and validate JSON responses
   - Implement retry logic with exponential backoff

2. **Profile Data Workflow**
   - Endpoint: `https://app.cassidyai.com/api/webhook/workflows/cmbv9eaaz00139pa7krnjmoa0?results=true`
   - Input: LinkedIn profile URL
   - Output: Structured profile data with experiences, education, certifications
   - Extract company LinkedIn URLs from experience entries

3. **Company Data Workflow**
   - Endpoint: `https://app.cassidyai.com/api/webhook/workflows/cmckultwk008bknkgisuk5fef?results=true`
   - Input: Company LinkedIn URL from profile experiences
   - Output: Company details including funding, locations, employee data
   - Error handling for missing/invalid company profiles

4. **Test Data Management**
   - Curated test LinkedIn profiles spanning multiple industries
   - Mock response data for offline development/testing
   - Data validation schemas for all response types
   - Performance benchmarking datasets

### Technical Requirements

1. **API Client Implementation**
   - FastAPI-compatible async HTTP client
   - Request/response logging and monitoring
   - Rate limiting and throttling
   - Comprehensive error handling

2. **Data Models**
   - Pydantic models for all Cassidy response schemas
   - Vector embedding preparation models
   - Database storage models with pgvector compatibility

3. **Testing Infrastructure**
   - Unit tests with mocked Cassidy responses
   - Integration tests with real API calls
   - Performance tests with batch processing
   - Data quality validation tests

## Technical Design

### Architecture

```
FastAPI App
├── cassidy/
│   ├── client.py          # HTTP client for Cassidy workflows
│   ├── models.py          # Pydantic models for requests/responses
│   ├── workflows.py       # Workflow-specific implementations
│   └── exceptions.py      # Custom exception handling
├── data/
│   ├── schemas.py         # Database models
│   ├── validation.py      # Data quality checks
│   └── embeddings.py      # Vector preparation
└── tests/
    ├── test_cassidy.py    # API integration tests
    ├── fixtures/          # Mock response data
    └── data/              # Test LinkedIn profiles
```

### Data Flow

1. **Profile Ingestion Flow**
   ```
   LinkedIn URL → Cassidy Profile Workflow → Parse Response → Extract Companies → 
   Company Workflows → Aggregate Data → Vector Storage
   ```

2. **Error Handling Flow**
   ```
   API Failure → Retry Logic → Fallback Response → Log Error → Continue Processing
   ```

### Key Components

#### 1. Cassidy Client (`cassidy/client.py`)

```python
class CassidyClient:
    async def fetch_profile(self, linkedin_url: str) -> ProfileResponse
    async def fetch_company(self, company_url: str) -> CompanyResponse
    async def poll_workflow_result(self, workflow_id: str) -> WorkflowResult
    def _handle_rate_limiting(self, response: Response) -> None
    def _retry_with_backoff(self, request_func: Callable) -> Any
```

#### 2. Data Models (`cassidy/models.py`)

Based on the blueprint analysis, key models include:

```python
class ProfileResponse(BaseModel):
    id: str
    name: str
    position: str
    about: str
    current_company: CompanyInfo
    experience: List[ExperienceEntry]
    education: List[EducationEntry]
    certifications: List[CertificationEntry]
    # ... additional fields from ronlinkedin_pretty.json

class ExperienceEntry(BaseModel):
    title: str
    company: str
    company_id: str
    url: str  # LinkedIn company URL for company workflow
    start_date: str
    end_date: Optional[str]
    description: str
    location: str

class CompanyResponse(BaseModel):
    company_name: str
    description: str
    employee_count: int
    employee_range: str
    industries: List[str]
    funding_info: FundingInfo
    locations: List[LocationInfo]
    # ... complete schema from blueprint
```

#### 3. Workflow Implementation (`cassidy/workflows.py`)

```python
class LinkedInWorkflow:
    async def process_profile(self, url: str) -> EnrichedProfile:
        """Complete profile + company enrichment workflow"""
        profile = await self.client.fetch_profile(url)
        companies = await self._fetch_companies(profile.experience)
        return self._merge_profile_data(profile, companies)
    
    async def _fetch_companies(self, experiences: List[ExperienceEntry]) -> List[CompanyResponse]:
        """Parallel company data fetching with error handling"""
        # Implementation with sleep delays as shown in blueprint
```

## Test Data Strategy

### Test Profile Categories

1. **Executive Profiles** (C-level, VPs)
   - Ronald Sorozan profile (from existing data)
   - Multiple companies and industries
   - Rich experience history

2. **Technical Professionals** (Engineers, Developers)
   - Startup to enterprise progression
   - Technical certifications
   - Open source contributions

3. **Sales & Marketing** (Account Managers, Growth)
   - Client-facing roles
   - Performance metrics
   - Industry specializations

4. **Edge Cases**
   - Profiles with missing company data
   - Recent graduates with limited experience
   - International profiles with different formatting
   - Profiles with privacy restrictions

### Mock Data Structure

```
tests/fixtures/
├── profiles/
│   ├── executive_profiles.json
│   ├── technical_profiles.json
│   ├── sales_marketing_profiles.json
│   └── edge_cases.json
├── companies/
│   ├── startup_companies.json
│   ├── enterprise_companies.json
│   └── error_responses.json
└── workflows/
    ├── success_responses.json
    ├── partial_failures.json
    └── timeout_scenarios.json
```

## Implementation Plan

### Phase 1: Core Integration (Week 1)
- [ ] Implement basic Cassidy HTTP client
- [ ] Create Pydantic models from blueprint schemas
- [ ] Add error handling and retry logic
- [ ] Write unit tests with mocked responses

### Phase 2: Workflow Implementation (Week 2)
- [ ] Implement profile workflow integration
- [ ] Add company workflow with experience parsing
- [ ] Implement async batch processing
- [ ] Add comprehensive logging

### Phase 3: Test Data & Validation (Week 3)
- [ ] Curate diverse test LinkedIn profiles
- [ ] Create comprehensive mock datasets
- [ ] Implement data quality validation
- [ ] Add performance benchmarking

### Phase 4: Production Readiness (Week 4)
- [ ] Add rate limiting and monitoring
- [ ] Implement caching layer
- [ ] Create API documentation
- [ ] Deploy to staging environment

## Success Metrics

1. **Reliability**: 99%+ success rate for valid LinkedIn URLs
2. **Performance**: <30s average processing time per profile
3. **Data Quality**: 95%+ data completeness for core fields
4. **Error Handling**: Graceful degradation for API failures
5. **Test Coverage**: 90%+ code coverage with integration tests

## Risk Mitigation

1. **Cassidy API Changes**: Version pinning and change detection
2. **Rate Limiting**: Respect API limits with backoff strategies
3. **Data Quality**: Validation schemas and quality metrics
4. **Performance**: Async processing and batch optimization
5. **Monitoring**: Comprehensive logging and alerting

## Future Considerations

1. **Scaling**: Batch processing for multiple profiles
2. **Caching**: Redis layer for frequently accessed data
3. **Real-time**: WebSocket integration for live updates
4. **Analytics**: Data insights and trend analysis
5. **MCP Integration**: Claude-compatible server endpoints

---

**Dependencies**: FastAPI, httpx, pydantic, pytest  
**Estimated Effort**: 4 weeks  
**Priority**: High (Foundation for all ingestion workflows)
