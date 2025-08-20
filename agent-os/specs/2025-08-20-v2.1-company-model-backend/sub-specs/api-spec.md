# API Specification

This is the API specification for the spec detailed in @agent-os/specs/2025-08-20-v2.1-company-model-backend/spec.md

> Created: 2025-08-20
> Version: 1.0.0

## Enhanced Profile Endpoints

### GET /profiles/{profile_id}

**Purpose:** Retrieve a specific profile with optional company data inclusion
**Parameters:** 
- `profile_id` (path): UUID of the profile to retrieve
- `include_companies` (query): Boolean to include full company data (default: false)
**Response:** ProfileResponse with optional embedded company objects
**Errors:** 404 Profile not found, 400 Invalid UUID format

#### Response Format (include_companies=false - Default)
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "linkedin_profile_url": "https://linkedin.com/in/example",
  "full_name": "John Smith",
  "work_experience": [
    {
      "position_title": "CTO",
      "company_name": "PricewaterhouseCoopers",
      "company_linkedin_url": "https://linkedin.com/company/pwc",
      "company_id": "123e4567-e89b-12d3-a456-426614174000",
      "start_date": "2020-01-01",
      "end_date": null,
      "is_current": true
    }
  ]
}
```

#### Response Format (include_companies=true)
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000", 
  "linkedin_profile_url": "https://linkedin.com/in/example",
  "full_name": "John Smith",
  "work_experience": [
    {
      "position_title": "CTO",
      "company_name": "PricewaterhouseCoopers", 
      "company_linkedin_url": "https://linkedin.com/company/pwc",
      "company_id": "123e4567-e89b-12d3-a456-426614174000",
      "start_date": "2020-01-01",
      "end_date": null,
      "is_current": true,
      "company": {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "name": "PricewaterhouseCoopers",
        "linkedin_company_url": "https://linkedin.com/company/pwc",
        "employee_count": 284478,
        "employee_range": "10001+",
        "industries": ["Professional Services", "Consulting"],
        "specialties": "Assurance, Tax, Advisory, Consulting",
        "funding_info": null,
        "locations": [
          {
            "country": "United States",
            "city": "New York",
            "region": "NY"
          }
        ],
        "description": "Building trust in society and solving important problems."
      }
    }
  ]
}
```

### GET /profiles?include_companies=true

**Purpose:** List profiles with optional company data inclusion
**Parameters:**
- `include_companies` (query): Boolean to include full company data (default: false)  
- `limit` (query): Number of profiles to return (default: 50, max: 100)
- `offset` (query): Number of profiles to skip for pagination (default: 0)
**Response:** Array of ProfileResponse objects with optional company data
**Errors:** 400 Invalid query parameters

## New Company Endpoints

### GET /companies/{company_id}

**Purpose:** Retrieve detailed information about a specific company
**Parameters:** `company_id` (path): UUID of the company to retrieve
**Response:** Complete company object with all available data
**Errors:** 404 Company not found, 400 Invalid UUID format

#### Response Format
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "PricewaterhouseCoopers",
  "linkedin_company_url": "https://linkedin.com/company/pwc",
  "employee_count": 284478,
  "employee_range": "10001+", 
  "industries": ["Professional Services", "Consulting"],
  "specialties": "Assurance, Tax, Advisory, Consulting",
  "funding_info": null,
  "locations": [
    {
      "country": "United States",
      "city": "New York", 
      "region": "NY",
      "address": "300 Madison Avenue"
    }
  ],
  "description": "Building trust in society and solving important problems.",
  "created_at": "2025-08-20T10:30:00Z",
  "updated_at": "2025-08-20T15:45:00Z"
}
```

### GET /companies?search={query}

**Purpose:** Search companies by name, industry, or other criteria
**Parameters:**
- `search` (query): Search term for company name or industry
- `industry` (query): Filter by specific industry
- `employee_range` (query): Filter by employee size range (e.g., "10001+")
- `limit` (query): Number of results to return (default: 50, max: 100) 
- `offset` (query): Number of results to skip for pagination (default: 0)
**Response:** Array of company objects matching search criteria
**Errors:** 400 Invalid query parameters

### GET /companies/{company_id}/profiles

**Purpose:** Get all profiles associated with a specific company
**Parameters:**
- `company_id` (path): UUID of the company
- `current_only` (query): Only show profiles with current positions at company (default: false)
- `limit` (query): Number of profiles to return (default: 50, max: 100)
- `offset` (query): Number of profiles to skip for pagination (default: 0)
**Response:** Array of profiles who have worked at the company
**Errors:** 404 Company not found, 400 Invalid parameters

## Enhanced Scoring Integration

### POST /scoring/score-profile

**Purpose:** Score a profile with enhanced company context automatically included
**Parameters:** Profile ID and scoring template information
**Response:** Scoring result with company context utilized in evaluation
**Errors:** 404 Profile not found, 400 Invalid scoring parameters

#### Request Format
```json
{
  "profile_id": "550e8400-e29b-41d4-a716-446655440000",
  "template_name": "cto-assessment",
  "include_company_context": true
}
```

#### Response Format (Enhanced with Company Context)
```json
{
  "score": 8.7,
  "reasoning": "Strong technical leadership experience demonstrated at PricewaterhouseCoopers (284K employees), indicating ability to scale technology solutions in large enterprise environments. Industry experience in Professional Services provides relevant consulting background for client-facing technology roles.",
  "company_context_used": {
    "companies_analyzed": 3,
    "total_employees_across_companies": 295000,
    "industries_represented": ["Professional Services", "Technology", "Financial Services"],
    "company_size_distribution": "2 Enterprise (10K+), 1 Mid-size (1K-10K)"
  }
}
```

## Internal Service Endpoints

### POST /internal/companies

**Purpose:** Create or update company records during profile ingestion
**Parameters:** Company data from Cassidy processing
**Response:** Created or updated company object
**Errors:** 400 Invalid company data, 409 Duplicate company URL

#### Request Format  
```json
{
  "name": "PricewaterhouseCoopers",
  "linkedin_company_url": "https://linkedin.com/company/pwc",
  "employee_count": 284478,
  "employee_range": "10001+",
  "industries": ["Professional Services", "Consulting"],
  "specialties": "Assurance, Tax, Advisory, Consulting", 
  "funding_info": null,
  "locations": [
    {
      "country": "United States",
      "city": "New York",
      "region": "NY"
    }
  ],
  "description": "Building trust in society and solving important problems."
}
```

### POST /internal/profiles/{profile_id}/companies/{company_id}/link

**Purpose:** Establish work experience relationship between profile and company
**Parameters:** Work experience details (position, dates, current status)
**Response:** Created relationship record
**Errors:** 404 Profile or company not found, 400 Invalid relationship data

#### Request Format
```json
{
  "position_title": "Chief Technology Officer",
  "start_date": "2020-01-01",
  "end_date": null,
  "is_current": true
}
```

## Controllers Implementation

### ProfileController Enhancements
```python
class ProfileController:
    async def get_profile(
        self, 
        profile_id: UUID, 
        include_companies: bool = False
    ) -> ProfileResponse:
        """Retrieve profile with optional company data inclusion"""
        
    async def list_profiles(
        self, 
        include_companies: bool = False,
        limit: int = 50,
        offset: int = 0
    ) -> List[ProfileResponse]:
        """List profiles with optional company data inclusion"""
```

### CompanyController (New)
```python
class CompanyController:
    async def get_company(self, company_id: UUID) -> CompanyResponse:
        """Retrieve detailed company information"""
        
    async def search_companies(
        self,
        search: Optional[str] = None,
        industry: Optional[str] = None,
        employee_range: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[CompanyResponse]:
        """Search companies by various criteria"""
        
    async def get_company_profiles(
        self,
        company_id: UUID,
        current_only: bool = False,
        limit: int = 50,
        offset: int = 0  
    ) -> List[ProfileResponse]:
        """Get profiles associated with company"""
```

### CompanyIngestionController (Internal)
```python
class CompanyIngestionController:
    async def create_or_update_company(
        self, 
        company_data: CanonicalCompany
    ) -> CompanyResponse:
        """Create or update company during profile ingestion"""
        
    async def link_profile_company(
        self,
        profile_id: UUID,
        company_id: UUID, 
        work_experience: WorkExperienceLink
    ) -> RelationshipResponse:
        """Link profile to company with work experience details"""
```

## Response Models

### Enhanced ProfileResponse
```python
class ProfileResponse(BaseModel):
    id: UUID
    linkedin_profile_url: str
    full_name: str
    work_experience: List[WorkExperienceResponse]
    
class WorkExperienceResponse(BaseModel):
    position_title: str
    company_name: str
    company_linkedin_url: Optional[str]
    company_id: Optional[UUID]
    start_date: Optional[date]
    end_date: Optional[date]
    is_current: bool
    company: Optional[CompanyResponse] = None  # Only populated when include_companies=true
```

### CompanyResponse  
```python
class CompanyResponse(BaseModel):
    id: UUID
    name: str
    linkedin_company_url: Optional[str]
    employee_count: Optional[int]
    employee_range: Optional[str]
    industries: List[str]
    specialties: Optional[str]
    funding_info: Optional[Dict[str, Any]]
    locations: List[Dict[str, Any]]
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
```

## Error Handling

### Enhanced Error Responses
```python
# Company not found
{
  "error": "COMPANY_NOT_FOUND",
  "message": "Company with ID {company_id} not found",
  "suggestions": [
    "Verify the company ID is correct",
    "Check if the company exists in the system"
  ]
}

# Invalid company data during ingestion
{
  "error": "INVALID_COMPANY_DATA", 
  "message": "Company data validation failed",
  "details": {
    "employee_count": "Must be a non-negative integer",
    "name": "Company name cannot be empty"
  }
}
```

## Backward Compatibility

### Existing API Behavior Preservation
- All existing profile endpoints maintain identical responses when `include_companies=false` (default)
- No breaking changes to current API consumers
- Gradual migration path for systems wanting company data
- Optional parameters ensure existing integrations continue working

### Migration Support
- Profile responses include `company_id` fields to enable future company data retrieval
- Existing work experience structure remains unchanged
- New company data appears as additional nested objects when requested
