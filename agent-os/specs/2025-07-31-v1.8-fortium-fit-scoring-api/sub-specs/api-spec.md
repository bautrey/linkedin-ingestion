# V1.8 API Specification - Fortium Fit Scoring

## Endpoint: Profile Scoring

### GET /api/v1/profiles/{profile_id}/score

**Description**: Calculate and return fit score for a specific profile and role

**Authentication**: API Key required (X-API-Key header)

**Parameters**:
- `profile_id` (path, required): Profile identifier
- `role` (query, required): Target role (CIO|CTO|CISO)

**Request Example**:
```http
GET /api/v1/profiles/ronald-sorozan/score?role=CTO
X-API-Key: your-api-key
```

**Success Response (200)**:
```json
{
  "profile_id": "ronald-sorozan",
  "role": "CTO",
  "overall_score": 0.85,
  "category_scores": {
    "technical_leadership": 0.90,
    "industry_experience": 0.80,
    "company_scale": 0.85,
    "education_background": 0.75,
    "career_progression": 0.88
  },
  "summary": "Strong technical leader with extensive experience in enterprise software development and team management. Demonstrates solid background in fintech and scaling engineering organizations.",
  "recommendations": [
    "Excellent fit for CTO roles at mid-to-large companies",
    "Strong technical depth with proven leadership experience",
    "Consider for senior technical leadership positions"
  ],
  "alternative_roles": [
    "VP of Engineering",
    "Chief Technology Officer",
    "Director of Engineering"
  ],
  "scored_at": "2025-07-31T14:00:00Z",
  "algorithm_version": 1
}
```

**Error Responses**:

**404 - Profile Not Found**:
```json
{
  "error": "Profile not found",
  "profile_id": "invalid-profile"
}
```

**400 - Invalid Role**:
```json
{
  "error": "Invalid role specified",
  "valid_roles": ["CIO", "CTO", "CISO"],
  "provided_role": "CEO"
}
```

**401 - Unauthorized**:
```json
{
  "error": "API key required",
  "message": "Please provide a valid API key in X-API-Key header"
}
```

**500 - Scoring Engine Error**:
```json
{
  "error": "Scoring calculation failed",
  "message": "Unable to calculate score due to missing configuration"
}
```

## Performance Requirements

- Response time: < 200ms for cached results
- Response time: < 500ms for fresh calculations
- Concurrent requests: Support 100+ simultaneous scoring requests
- Caching: Results cached for 1 hour per profile/role combination

## Data Validation

- Profile ID: Must exist in database
- Role: Must be one of CIO, CTO, or CISO
- All scores: Range 0.0 to 1.0 with 2 decimal precision
- Response: Must be valid JSON with all required fields

## Security Considerations

- API key validation on every request
- Rate limiting: 1000 requests per hour per API key
- Input sanitization for all parameters
- No sensitive profile data in error messages
