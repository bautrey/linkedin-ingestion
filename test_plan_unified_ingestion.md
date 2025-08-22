# Test Plan: Unified Profile Ingestion with Company Processing

## Overview
This test plan verifies the newly unified profile ingestion flow that includes complete company processing and junction table relationships.

## Database Migration Verification ✅
- [x] Applied `profile_companies` junction table migration to local database
- [x] Applied migration to production database using `supabase db push --password`
- [x] Verified table structure and SQL functions exist
- [x] Tested foreign key constraints work correctly

## Test Scenarios

### 1. Database Schema Tests

#### 1.1 Junction Table Structure ✅
- [x] `profile_companies` table exists with correct schema
- [x] Foreign key constraints to `linkedin_profiles` and `companies` tables
- [x] Indexes on `profile_id`, `company_id`, and `is_current_role`
- [x] SQL functions `get_profiles_for_company()` and `get_companies_for_profile()` exist

#### 1.2 Helper Methods ✅
- [x] `link_profile_to_company()` method added to SupabaseClient
- [x] Helper methods added to ProfileController:
  - [x] `_extract_company_urls_from_experience()`
  - [x] `_extract_company_id_from_url()`
  - [x] `_find_job_info_for_company()`

### 2. API Endpoint Tests

#### 2.1 Single Profile Creation - `POST /api/v1/profiles`
**Test Case**: Create a profile with company processing
```bash
curl -X POST "http://localhost:8000/api/v1/profiles" \
  -H "X-API-Key: li_HieZz-IjBp0uE7d-rZkRE0qyy12r5_ZJS_FR4jMvv0I" \
  -H "Content-Type: application/json" \
  -d '{
    "linkedin_url": "https://www.linkedin.com/in/test-profile/",
    "suggested_role": "CTO",
    "include_companies": true
  }'
```

**Expected Results**:
- Profile created successfully with unique ID
- Companies extracted from experience section
- Company profiles fetched from Cassidy API
- Companies stored in database (with deduplication)
- Junction table records created linking profile to companies
- Response includes `companies_processed` array with metadata
- Response includes `pipeline_metadata` with processing info

#### 2.2 Profile Without Company Processing
**Test Case**: Create profile with `include_companies: false`
```bash
curl -X POST "http://localhost:8000/api/v1/profiles" \
  -H "X-API-Key: li_HieZz-IjBp0uE7d-rZkRE0qyy12r5_ZJS_FR4jMvv0I" \
  -H "Content-Type: application/json" \
  -d '{
    "linkedin_url": "https://www.linkedin.com/in/test-profile-no-companies/",
    "suggested_role": "CIO",
    "include_companies": false
  }'
```

**Expected Results**:
- Profile created successfully
- No company processing performed
- No `companies_processed` field in response
- No junction table records created

#### 2.3 Batch Profile Creation - `POST /api/v1/profiles/batch`
**Test Case**: Create multiple profiles with company processing
```bash
curl -X POST "http://localhost:8000/api/v1/profiles/batch" \
  -H "X-API-Key: li_HieZz-IjBp0uE7d-rZkRE0qyy12r5_ZJS_FR4jMvv0I" \
  -H "Content-Type: application/json" \
  -d '{
    "profiles": [
      {
        "linkedin_url": "https://www.linkedin.com/in/batch-test-1/",
        "suggested_role": "CTO",
        "include_companies": true
      },
      {
        "linkedin_url": "https://www.linkedin.com/in/batch-test-2/",
        "suggested_role": "CISO",
        "include_companies": true
      }
    ],
    "max_concurrent": 2
  }'
```

**Expected Results**:
- Batch processing completed with unique `batch_id`
- Individual profile results in `results` array
- Each successful profile includes company processing
- Concurrency respected (max 2 concurrent)
- Processing time and statistics included

#### 2.4 Re-ingestion Test (Smart Update)
**Test Case**: Re-ingest existing profile
```bash
# First create a profile
curl -X POST "http://localhost:8000/api/v1/profiles" \
  -H "X-API-Key: li_HieZz-IjBp0uE7d-rZkRE0qyy12r5_ZJS_FR4jMvv0I" \
  -H "Content-Type: application/json" \
  -d '{
    "linkedin_url": "https://www.linkedin.com/in/re-ingest-test/",
    "suggested_role": "CTO",
    "include_companies": true
  }'

# Then re-ingest the same URL
curl -X POST "http://localhost:8000/api/v1/profiles" \
  -H "X-API-Key: li_HieZz-IjBp0uE7d-rZkRE0qyy12r5_ZJS_FR4jMvv0I" \
  -H "Content-Type: application/json" \
  -d '{
    "linkedin_url": "https://www.linkedin.com/in/re-ingest-test/",
    "suggested_role": "CTO",
    "include_companies": true
  }'
```

**Expected Results**:
- Old profile deleted automatically
- New profile created with fresh data
- Old junction table records cleaned up (CASCADE DELETE)
- New company relationships established
- No duplicate profiles in database

### 3. Error Handling Tests

#### 3.1 Invalid LinkedIn URL
```bash
curl -X POST "http://localhost:8000/api/v1/profiles" \
  -H "X-API-Key: li_HieZz-IjBp0uE7d-rZkRE0qyy12r5_ZJS_FR4jMvv0I" \
  -H "Content-Type: application/json" \
  -d '{
    "linkedin_url": "https://not-a-linkedin-url.com",
    "suggested_role": "CTO"
  }'
```

**Expected**: 400 error with helpful error message and suggestions

#### 3.2 Missing Required Fields
```bash
curl -X POST "http://localhost:8000/api/v1/profiles" \
  -H "X-API-Key: li_HieZz-IjBp0uE7d-rZkRE0qyy12r5_ZJS_FR4jMvv0I" \
  -H "Content-Type: application/json" \
  -d '{
    "linkedin_url": "https://www.linkedin.com/in/test/"
  }'
```

**Expected**: 422 validation error for missing `suggested_role`

#### 3.3 Invalid API Key
```bash
curl -X POST "http://localhost:8000/api/v1/profiles" \
  -H "X-API-Key: invalid-key" \
  -H "Content-Type: application/json" \
  -d '{
    "linkedin_url": "https://www.linkedin.com/in/test/",
    "suggested_role": "CTO"
  }'
```

**Expected**: 403 unauthorized error

#### 3.4 Company Processing Failure Recovery
**Test**: Profile with companies that fail to fetch
**Expected**: Profile creation continues, successful companies processed, failed companies logged but don't block profile creation

### 4. Data Integrity Tests

#### 4.1 Junction Table Relationships
```sql
-- After creating profiles with companies, verify relationships
SELECT 
  p.name as profile_name,
  c.company_name,
  pc.job_title,
  pc.is_current_role,
  pc.start_date,
  pc.end_date
FROM profile_companies pc
JOIN linkedin_profiles p ON pc.profile_id = p.id  
JOIN companies c ON pc.company_id = c.id
ORDER BY p.created_at DESC;
```

**Expected**: 
- Correct profile-company relationships
- Job details populated from experience
- Current roles marked correctly
- Date information preserved

#### 4.2 Company Deduplication
**Test**: Create two profiles that worked at the same company
**Expected**: 
- Single company record in database
- Multiple junction records pointing to same company
- No duplicate companies created

#### 4.3 Cascade Deletion
```bash
# Delete a profile and verify cleanup
curl -X DELETE "http://localhost:8000/api/v1/profiles/{profile_id}" \
  -H "X-API-Key: li_HieZz-IjBp0uE7d-rZkRE0qyy12r5_ZJS_FR4jMvv0I"
```

**Expected**:
- Profile deleted
- Junction table records deleted (CASCADE)
- Company records remain (shared resource)

### 5. Performance Tests

#### 5.1 Rate Limiting
**Test**: Profile with 5+ companies
**Expected**: 
- 1-second delays between company API calls
- All companies processed successfully
- Total processing time ~5+ seconds for 5 companies

#### 5.2 Batch Concurrency
**Test**: Batch with 10 profiles, max_concurrent=3
**Expected**:
- Only 3 profiles processed simultaneously
- Remaining profiles queued
- All profiles eventually processed
- Performance improvement over sequential processing

### 6. Integration Tests

#### 6.1 End-to-End Profile Creation
1. Create profile with companies
2. Verify profile in database
3. Verify companies in database  
4. Verify junction relationships
5. Test query functions work
6. Verify suggested role set correctly

#### 6.2 Company Query Functions
```bash
# Get companies for a profile
curl "http://localhost:8000/api/v1/profiles/{profile_id}/companies" \
  -H "X-API-Key: li_HieZz-IjBp0uE7d-rZkRE0qyy12r5_ZJS_FR4jMvv0I"

# Get profiles for a company  
curl "http://localhost:8000/api/v1/companies/{company_id}/profiles" \
  -H "X-API-Key: li_HieZz-IjBp0uE7d-rZkRE0qyy12r5_ZJS_FR4jMvv0I"
```

**Expected**: Correct relationship data returned

### 7. Edge Cases

#### 7.1 Profile with No Experience
**Test**: LinkedIn profile with empty experience section
**Expected**: Profile created successfully, no company processing

#### 7.2 Experience with Invalid Company URLs
**Test**: Profile with malformed company LinkedIn URLs
**Expected**: Profile created, invalid URLs skipped, valid ones processed

#### 7.3 Large Batch Processing
**Test**: Batch with maximum 10 profiles
**Expected**: All profiles processed successfully within reasonable time

#### 7.4 Network Failures
**Test**: Simulate Cassidy API failures during company fetching
**Expected**: Profile creation continues, failed companies logged

## Test Execution Plan

### Phase 1: Setup ✅
- [x] Database migration applied
- [x] Code changes deployed
- [x] Helper methods implemented

### Phase 2: Unit Tests
- [ ] Test helper methods in isolation
- [ ] Test database operations
- [ ] Test error handling

### Phase 3: API Tests  
- [ ] Single profile creation tests
- [ ] Batch profile creation tests
- [ ] Error scenario tests
- [ ] Re-ingestion tests

### Phase 4: Integration Tests
- [ ] End-to-end workflows
- [ ] Company relationship queries
- [ ] Performance benchmarks
- [ ] Stress testing

### Phase 5: Production Validation
- [ ] Small-scale production test
- [ ] Monitor logs and metrics
- [ ] Verify data integrity
- [ ] Performance monitoring

## Success Criteria

✅ **Migration**: Database schema updated in both local and production
✅ **Code**: Helper methods implemented and working
✅ **Endpoints**: Clean, unified API endpoints
⏳ **Functionality**: All test scenarios pass
⏳ **Performance**: Reasonable processing times with rate limiting
⏳ **Reliability**: Graceful error handling and recovery
⏳ **Data Integrity**: Correct relationships and no data corruption

## Test Environment Setup

### Local Testing
```bash
# Start local development server
cd /Users/burke/projects/linkedin-ingestion
python main.py

# Server should be running on http://localhost:8000
# API docs available at http://localhost:8000/docs
```

### Required Environment Variables
- `API_KEY`: For authentication
- `CASSIDY_*`: For LinkedIn profile/company fetching  
- `SUPABASE_*`: For database connections
- `OPENAI_API_KEY`: For scoring features (optional for basic tests)

## Test Data Requirements

### Test LinkedIn Profiles
- Valid LinkedIn profile URLs with experience sections
- Profiles with various company types (numeric IDs, slug names)
- Profiles with current and past roles
- Profiles with minimal experience
- Profiles with extensive experience (5+ companies)

### Expected API Rate Limits
- Cassidy API: Respect rate limits with 1-second delays
- LinkedIn data: Use test-friendly profiles to avoid blocking

## Monitoring and Logging

During tests, monitor:
- Application logs for errors/warnings
- Database query performance
- API response times
- Memory usage during batch processing
- Network request patterns to external APIs

## Risk Mitigation

- **Data Loss**: All tests use separate test profiles, not production data
- **Rate Limiting**: Implement delays and respect API limits
- **Database Integrity**: Use transactions where appropriate
- **Rollback Plan**: Keep previous endpoint implementations as backup
- **Monitoring**: Watch for unexpected errors or performance degradation
