# Technical Specification

This is the technical specification for the spec detailed in @agent-os/specs/2025-08-20-v2.1-company-model-backend/spec.md

> Created: 2025-08-20
> Version: 1.0.0

## Technical Requirements

### Company Model Architecture
- **Pydantic Model**: CanonicalCompany with comprehensive field validation matching Cassidy output structure
- **Database Integration**: SQLAlchemy ORM model with proper indexing for performance
- **Data Validation**: Field-level validation for employee counts, industry classifications, and location data
- **Relationship Mapping**: Many-to-many relationship between profiles and companies through work experiences

### Profile Ingestion Enhancement
- **Cassidy Integration**: Extract company data during profile processing without additional API calls
- **Company Deduplication**: Smart matching algorithm to identify existing companies by LinkedIn URL and name
- **Batch Processing**: Efficient company creation/updates for profiles with multiple work experiences
- **Error Resilience**: Graceful handling of missing or malformed company data without blocking profile ingestion

### API Response Integration
- **Profile Serialization**: Embedded company objects in profile responses with configurable depth
- **Performance Optimization**: Efficient database joins to minimize N+1 query issues
- **Backward Compatibility**: Maintain existing API structure while adding company data
- **Response Size Management**: Optional company inclusion to prevent response bloat for basic queries

### Data Structure Alignment
- **Cassidy Format Mapping**: Direct mapping from Cassidy company response to internal model
- **Field Standardization**: Consistent naming conventions and data types across all company fields
- **Nullable Field Handling**: Proper handling of optional company information that may not be available

## Approach Options

**Option A: Embedded Company Data in All Profile Responses**
- Pros: Single API call provides complete context, immediate availability for scoring
- Cons: Larger response sizes, potential performance impact on basic profile queries
- Implementation: Default include company data with opt-out parameter

**Option B: Optional Company Data with Query Parameter (Selected)**
- Pros: Flexible response sizes, backward compatibility, performance optimization
- Cons: Additional complexity for API consumers, requires parameter awareness
- Implementation: `?include_companies=true` parameter for profile endpoints

**Rationale:** Option B provides the best balance of functionality and performance. Critical scoring operations can request full company context, while lightweight operations maintain fast response times. This approach also maintains backward compatibility with existing API consumers.

**Option C: Separate Company Endpoints with Reference IDs**
- Pros: Clean separation, optimal response sizes, dedicated company operations
- Cons: Multiple API calls required, complex frontend logic, delayed company context access
- Implementation: Company IDs in profile responses, separate `/companies/{id}` endpoints

## External Dependencies

**No new external dependencies required** - All implementation uses existing technology stack:

- **SQLAlchemy**: Already in use for database ORM operations
- **Pydantic**: Already in use for data validation and serialization  
- **FastAPI**: Already in use for API endpoint implementation
- **Supabase**: Already configured for database operations

## Implementation Architecture

### Model Layer
```python
# app/models/canonical.py - Enhanced CanonicalCompany model
class CanonicalCompany(BaseModel):
    linkedin_company_url: Optional[str]
    name: str
    employee_count: Optional[int]
    employee_range: Optional[str] 
    industries: List[str]
    specialties: Optional[str]
    funding_info: Optional[Dict[str, Any]]
    locations: List[Dict[str, Any]]
    description: Optional[str]
```

### Database Layer
```python
# app/database/models.py - Company table and relationships
class Company(Base):
    __tablename__ = "companies"
    id = Column(UUID, primary_key=True)
    linkedin_company_url = Column(String, unique=True, index=True)
    name = Column(String, nullable=False, index=True)
    # ... additional fields matching CanonicalCompany
```

### Service Layer
```python
# app/services/company_service.py - Company CRUD operations
class CompanyService:
    def create_or_update_company(self, company_data: CanonicalCompany)
    def find_company_by_url(self, linkedin_url: str)
    def link_profile_to_company(self, profile_id: UUID, company_id: UUID)
```

### API Integration
```python
# app/api/routes/profiles.py - Enhanced profile endpoints
@router.get("/profiles/{profile_id}")
async def get_profile(profile_id: UUID, include_companies: bool = False):
    # Return profile with optional company data
```

## Performance Considerations

### Database Optimization
- **Indexed Columns**: linkedin_company_url, name, and employee_count for fast lookups
- **Selective Loading**: Use SQLAlchemy's selectinload for efficient relationship fetching
- **Query Optimization**: Single query to fetch profile with all associated companies

### Caching Strategy
- **Company Deduplication**: Cache company lookups by LinkedIn URL during ingestion batch processing
- **API Response Caching**: Consider Redis caching for frequently accessed profile+company combinations
- **Database Connection Pooling**: Leverage existing Supabase connection pooling for scalability

### Memory Management
- **Lazy Loading**: Load company data only when requested via include_companies parameter
- **Batch Processing**: Process multiple company updates in single database transactions
- **Response Streaming**: For large company datasets, consider streaming responses

## Integration Points

### Ingestion Pipeline Integration
1. **Profile Processing**: Extract company data from Cassidy response during profile ingestion
2. **Company Resolution**: Check for existing companies by LinkedIn URL before creating new records
3. **Work Experience Linking**: Create relationships between profile work experiences and company records
4. **Data Validation**: Validate company data structure before database persistence

### API Layer Integration
1. **Profile Endpoints**: Add optional company inclusion to existing GET /profiles endpoints
2. **Response Serialization**: Extend ProfileResponse model to include company data
3. **Query Optimization**: Implement efficient database queries for profile+company retrieval
4. **Error Handling**: Graceful degradation when company data is unavailable
