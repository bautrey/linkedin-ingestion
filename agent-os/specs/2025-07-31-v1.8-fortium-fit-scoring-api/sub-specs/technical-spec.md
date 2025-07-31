# V1.8 Fortium Fit Scoring API - Technical Specification

## System Architecture

### API Endpoint Design
- **Method**: GET
- **Path**: `/api/v1/profiles/{profile_id}/score`
- **Query Parameters**: `role` (required: CIO|CTO|CISO)

### Database Schema Requirements
- Scoring algorithms table
- Role-specific thresholds table
- Scoring categories configuration
- Historical scores for audit trail

### Response Structure
```json
{
  "profile_id": "string",
  "role": "CIO|CTO|CISO",
  "overall_score": 0.85,
  "category_scores": {
    "technical_leadership": 0.9,
    "industry_experience": 0.8,
    "company_scale": 0.85
  },
  "summary": "Strong technical leader with...",
  "recommendations": ["Consider for CTO roles", "..."],
  "alternative_roles": ["CTO", "VP Engineering"],
  "scored_at": "2025-07-31T14:00:00Z"
}
```

### Implementation Components
- Scoring engine service
- Database configuration layer
- Caching strategy
- Error handling patterns

## Technical Requirements

### Performance
- Response time < 200ms
- Database-driven configuration (no code deployment for changes)
- Deterministic results (same input = same output)

### Security
- API key authentication required
- Input validation for all parameters
- Safe handling of profile data

### Testing
- Unit tests for all scoring algorithms
- Integration tests with live database
- Performance benchmarks
- Edge case coverage

## Integration Points

### Existing System
- Uses existing CanonicalProfile models
- Integrates with current API authentication
- Leverages existing Supabase connection

### Future Extensions
- Support for additional roles
- Machine learning model integration
- Batch scoring capabilities
