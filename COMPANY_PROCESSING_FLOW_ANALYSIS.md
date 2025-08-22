# Company Processing Flow Analysis

## Current System Architecture

### Flow 1: LinkedInDataPipeline (Shows in logs but NOT used by API)
```
LinkedInDataPipeline.ingest_profile_with_companies()
├── Step 1: Fetch profile from Cassidy API
├── Step 2: Extract company URLs from profile
├── Step 3: Call _fetch_companies(company_urls)
│   ├── For each URL: cassidy_client.fetch_company(url)
│   └── Returns list of CompanyProfile objects
├── Step 4: Convert to CanonicalCompany format
├── Step 5: company_service.batch_process_companies() 
│   └── STORES COMPANIES IN DATABASE ✅
└── Step 6: Store profile in database
```

### Flow 2: ProfileController.create_profile() (Used by API but BROKEN)
```
ProfileController.create_profile()
├── Step 1: linkedin_workflow.process_profile() 
│   └── Returns profile data (no company processing)
├── Step 2: Store profile in database
├── Step 3: IF include_companies:
│   ├── Extract company URLs from experience
│   ├── For each URL: cassidy_client.fetch_company(url) 
│   │   └── THIS WORKS - gets company data
│   ├── Convert to CanonicalCompany format
│   ├── company_service.batch_process_companies()
│   │   └── THIS SHOULD STORE BUT DOESN'T ❌
│   └── Create profile-company links
└── Return response
```

## The Problem

**ProfileController calls the working pieces individually but they don't work together**

### What the logs show:
- "Batch company fetch completed failed=0 successful=5 total_requested=5"
- This comes from LinkedInDataPipeline._fetch_companies() 
- But ProfileController NEVER calls LinkedInDataPipeline

### What actually happens in ProfileController:
1. Fetches companies via Cassidy API (works)
2. Calls company_service.batch_process_companies() (should store companies)
3. Companies disappear somewhere in step 2

## Code Location Analysis

### LinkedInDataPipeline (app/services/linkedin_pipeline.py)
- Lines 465-485: `_fetch_companies()` method
- Line 471: `company = await self.cassidy_client.fetch_company(url)`
- Lines 184-201: Company storage logic that WORKS

### ProfileController (main.py)
- Lines 583-590: Duplicate company fetching
- Line 584: `company_profile = await self.cassidy_client.fetch_company(company_url)`
- Lines 624-626: `processing_results = await company_service.batch_process_companies(canonical_companies)`
- Line 626: Companies should be stored here but aren't

## Root Cause Hypothesis

The issue is NOT in:
- Cassidy API calls (working in both places)
- CompanyService.batch_process_companies() (working in LinkedInDataPipeline)

The issue IS in:
- ProfileController's conversion from CompanyProfile to CanonicalCompany
- OR ProfileController's await/async handling of company_service calls
- OR missing database transaction/commit in ProfileController context

## Next Investigation Steps

1. Check if ProfileController is properly awaiting async calls
2. Check if CanonicalCompany conversion is failing silently
3. Check if database transactions are being committed
4. Compare working LinkedInDataPipeline company storage vs broken ProfileController
