# Quality Gates Validation Pipeline

This document describes the multi-stage validation system that acts as quality gates before the expensive LinkedIn profile ingestion process.

## Overview

The quality gates system implements a fail-fast validation pipeline to:
- ✅ Reduce unnecessary API calls and processing time
- ✅ Block invalid or inaccessible profiles early
- ✅ Provide detailed validation feedback
- ✅ Improve overall system reliability and performance

## Validation Stages

### Stage 1: URL Sanitization & Validation
**Service:** `URLValidationService` (`app/services/url_validation_service.py`)

**Purpose:** Clean and validate LinkedIn URLs before processing
- Removes marketing parameters (`utm_source`, `trk`, etc.)
- Normalizes URL format (adds https://, removes trailing slashes)
- Validates LinkedIn profile URL structure
- Rejects company URLs, legacy formats, and invalid domains

**Input:** Raw LinkedIn URL (potentially dirty)
```
https://linkedin.com/in/john-smith/?utm_source=share&trk=public_profile
```

**Output:** Sanitized URL or validation failure
```
https://www.linkedin.com/in/john-smith/
```

**Timing:** ~1-5ms (very fast, local processing only)

---

### Stage 2: Cassidy Quick Validation
**Service:** `CassidyQuickValidationService` (`app/services/quick_validation_service.py`)

**Purpose:** Verify profile accessibility without expensive company processing
- Uses Cassidy client to fetch LinkedIn profile
- Validates basic profile data completeness
- Returns lightweight profile summary
- Fails fast for inaccessible or incomplete profiles

**Input:** Sanitized LinkedIn URL from Stage 1
**Output:** Profile accessibility status + basic profile summary
**Timing:** ~500-2000ms (depends on LinkedIn/Cassidy response time)

---

### Stage 3: AI Role Compatibility Check
**Service:** `AIRoleCompatibilityService` (`app/services/ai_role_compatibility_service.py`)

**Purpose:** Check if profile matches suggested executive role using AI
- Quick sanity check: "Does this profile make sense as a [ROLE] candidate?"
- Auto-role detection: If submitted role fails, try other roles (CTO->CIO->CISO)
- Lightweight OpenAI prompts designed for speed over detail
- Prevent mismatched scoring (e.g., CIO profile scored against CISO prompt)

**Input:** Profile data from Stage 2 + suggested role (CTO/CIO/CISO)
**Output:** Pass/fail gate result + recommended role for scoring
**Timing:** ~1000-3000ms (depends on number of roles checked)

---

### Stage 4: Full Ingestion Pipeline *(Existing)*
**Purpose:** Complete profile and company data processing
- Full profile ingestion via existing `LinkedInDataPipeline`
- Company data processing and enrichment
- Database storage and indexing

## Usage Examples

### Basic Usage

```python
from app.services.url_validation_service import URLValidationService
from app.services.quick_validation_service import CassidyQuickValidationService
from app.services.ai_role_compatibility_service import AIRoleCompatibilityService, ExecutiveRole

# Stage 1: URL validation
url_validator = URLValidationService()
url_result = url_validator.validate_and_sanitize_url(raw_url)

if not url_result.is_valid:
    # Early exit - invalid URL
    return {"error": "Invalid LinkedIn URL", "details": url_result.validation_errors}

# Stage 2: Quick profile validation  
quick_validator = CassidyQuickValidationService()
quick_result = await quick_validator.quick_validate_profile(url_result.sanitized_url)

if not quick_result.is_valid:
    # Early exit - profile not accessible or incomplete
    return {"error": "Profile validation failed", "details": quick_result.validation_errors}

# Stage 3: AI role compatibility check
role_validator = AIRoleCompatibilityService()
profile = await get_full_profile(url_result.sanitized_url)  # Get full profile for role checking
role_result = await role_validator.check_role_compatibility(profile, ExecutiveRole.CTO)

if not role_result.is_valid:
    # Early exit - profile doesn't match any executive role
    return {"error": "Profile not compatible with executive roles", "details": role_result.reasoning}

# Proceed to full ingestion with correct role template
final_role = role_result.suggested_role  # Use AI-recommended role
pipeline = LinkedInDataPipeline()
full_result = await pipeline.process_profile_with_role(url_result.sanitized_url, final_role)
```

### Integration with FastAPI

```python
@app.post("/api/v1/profiles/validate")
async def validate_profile_quick(url: str, suggested_role: str = "CTO"):
    """Complete quality gates validation endpoint"""
    
    # Stage 1: URL validation
    url_validator = URLValidationService()
    url_result = url_validator.validate_and_sanitize_url(url)
    
    if not url_result.is_valid:
        raise HTTPException(status_code=400, detail={
            "stage": "url_validation",
            "errors": url_result.validation_errors
        })
    
    # Stage 2: Quick validation
    quick_validator = CassidyQuickValidationService()
    quick_result = await quick_validator.quick_validate_profile(url_result.sanitized_url)
    
    if not quick_result.is_valid:
        raise HTTPException(status_code=400, detail={
            "stage": "profile_validation", 
            "errors": quick_result.validation_errors
        })
    
    # Stage 3: Role compatibility check
    role_validator = AIRoleCompatibilityService()
    profile = await get_full_profile(url_result.sanitized_url)
    role_result = await role_validator.check_role_compatibility(
        profile, ExecutiveRole(suggested_role.upper())
    )
    
    return {
        "url_validation": url_result,
        "profile_validation": quick_result,
        "role_compatibility": role_result,
        "ready_for_ingestion": role_result.is_valid,
        "recommended_role": role_result.suggested_role.value
    }
```

### Demo Script

Run the complete validation pipeline demo:

```bash
# Single URL test with role
python3 -m app.services.validation_pipeline_demo "https://linkedin.com/in/someone" "CTO"

# Single URL test with default role (CTO)
python3 -m app.services.validation_pipeline_demo "https://linkedin.com/in/someone"

# Multiple test cases with different roles (default)
python3 -m app.services.validation_pipeline_demo
```

## API Reference

### URLValidationService

#### `validate_and_sanitize_url(url: str) -> URLValidationResult`

**Parameters:**
- `url`: Raw LinkedIn URL input

**Returns:** `URLValidationResult`
- `is_valid: bool` - Overall validation result
- `sanitized_url: Optional[str]` - Clean URL if valid
- `validation_errors: List[str]` - List of validation errors
- `sanitization_applied: List[str]` - List of cleaning operations applied

---

### AIRoleCompatibilityService

#### `check_role_compatibility(profile: CanonicalProfile, suggested_role: ExecutiveRole) -> RoleCompatibilityResult`

**Parameters:**
- `profile`: Full profile data for role analysis
- `suggested_role`: Role suggested by user (CTO/CIO/CISO)

**Returns:** `RoleCompatibilityResult`
- `is_valid: bool` - Passes gate for at least one role
- `suggested_role: ExecutiveRole` - Best matching role
- `original_role: ExecutiveRole` - Originally suggested role
- `role_changed: bool` - Whether role recommendation changed
- `compatibility_scores: Dict[ExecutiveRole, float]` - Scores for each checked role
- `confidence: float` - Confidence in recommendation (0.0-1.0)
- `reasoning: str` - Explanation of decision
- `processing_time_ms: float` - Processing time
- `tokens_used: int` - OpenAI tokens consumed
- `validation_errors: List[str]` - Any validation errors

#### `quick_role_check(profile: CanonicalProfile, role: ExecutiveRole) -> Tuple[bool, float, str]`

Performs single-role compatibility check.

**Returns:** `(is_compatible, score, reasoning)`

#### `health_check() -> Dict[str, Any]`

Returns health status of the AI role compatibility service.

---

### CassidyQuickValidationService

#### `quick_validate_profile(linkedin_url: str) -> QuickValidationResult`

**Parameters:**
- `linkedin_url`: Sanitized LinkedIn URL from Stage 1

**Returns:** `QuickValidationResult`
- `is_valid: bool` - Overall validation result
- `profile_accessible: bool` - Whether profile was fetchable
- `basic_data_valid: bool` - Whether profile has required data
- `validation_errors: List[str]` - List of validation errors
- `warnings: List[str]` - List of validation warnings
- `profile_summary: Optional[Dict]` - Lightweight profile data
- `processing_time_ms: float` - Processing time
- `cassidy_error: Optional[str]` - Cassidy-specific error if any

#### `health_check() -> Dict[str, Any]`

Returns health status of the quick validation service and its dependencies.

## Error Handling

### Stage 1 Failures
- **Invalid URL format:** Return immediately with validation errors
- **Company URL detected:** Reject (this pipeline is for profiles only)
- **Legacy URL format:** Reject or attempt conversion

### Stage 2 Failures
- **Profile not accessible:** LinkedIn profile doesn't exist or is private
- **Basic data missing:** Profile exists but lacks name or URL
- **Cassidy API error:** Service unavailable, rate limited, etc.

### Stage 3 Failures
- **Role incompatible:** Profile doesn't match suggested role below threshold (0.4)
- **All roles failed:** Profile doesn't match any executive role above minimum threshold
- **AI service error:** OpenAI API unavailable, rate limited, or other errors

### Error Response Format

```json
{
  "stage": "url_validation" | "profile_validation" | "role_compatibility",
  "is_valid": false,
  "errors": ["Detailed error message"],
  "warnings": ["Warning message"],
  "processing_time_ms": 123.45,
  "suggested_role": "CTO" | "CIO" | "CISO",
  "role_changed": false
}
```

## Performance Characteristics

| Stage | Typical Response Time | Failure Rate |
|-------|----------------------|--------------|
| URL Validation | 1-5ms | <1% (malformed URLs) |
| Profile Validation | 500-2000ms | 5-15% (invalid/private profiles) |
| Role Compatibility | 1000-3000ms | 20-35% (role mismatch) |
| Full Ingestion | 10-30 seconds | 2-8% (various issues) |

**Benefits:**
- 🚀 **90% faster failure detection** for invalid profiles and role mismatches
- 💰 **Reduced scoring costs** by avoiding expensive detailed scoring on wrong roles
- ⚡ **Better user experience** with faster feedback and correct role matching
- 🔍 **Detailed validation errors** for debugging
- 🎯 **Improved scoring accuracy** by using the right role template

## Testing

Run the test suite:

```bash
# Test URL validation service
python3 -m pytest tests/services/test_url_validation_service.py -v

# Test quick validation service  
python3 -m pytest tests/services/test_quick_validation_service.py -v

# Test AI role compatibility service
python3 -m pytest tests/services/test_ai_role_compatibility_service.py -v

# Test complete validation pipeline integration
python3 -m pytest tests/services/test_validation_pipeline.py -v
```

## Monitoring and Observability

All validation services include structured logging with:
- 🏷️ **Stage identification** (STAGE_1_URL_VALIDATION, STAGE_2_CASSIDY_VALIDATION, STAGE_3_AI_ROLE_COMPATIBILITY)
- ⏱️ **Performance timing** for each validation step
- 🔍 **Detailed error classification** for monitoring
- 📊 **Validation success/failure metrics**
- 🎯 **Role compatibility scores** and role change tracking

Example log entries:
```
INFO     🔧 URL_SANITIZATION_SUCCESS: Removed marketing parameters stage=STAGE_1_URL_VALIDATION
INFO     🔍 QUICK_VALIDATION_START: Starting profile accessibility check stage=STAGE_2_CASSIDY_VALIDATION  
INFO     ✅ PROFILE_FETCH_SUCCESS: Cassidy profile fetch successful stage=STAGE_2_CASSIDY_VALIDATION
INFO     🎉 QUICK_VALIDATION_SUCCESS: Profile validation completed successfully stage=STAGE_2_CASSIDY_VALIDATION status=PASSED
INFO     🎯 ROLE_COMPATIBILITY_START: Starting role compatibility check stage=STAGE_3_AI_ROLE_COMPATIBILITY
INFO     🔄 ROLE_CHANGED: Profile passed gate with different role stage=STAGE_3_AI_ROLE_COMPATIBILITY status=PASSED_WITH_CHANGE
```

## Next Steps

1. **Complete Stage 1: URL Sanitization & Validation** ✅
2. **Complete Stage 2: Cassidy Quick Validation** ✅
3. **Complete Stage 3: AI Role Compatibility Check** ✅
4. **Integrate validation pipeline into existing ingestion endpoints**
5. **Add comprehensive monitoring and alerting**
6. **Performance optimization and caching**
7. **A/B test role compatibility accuracy vs manual role assignments**
