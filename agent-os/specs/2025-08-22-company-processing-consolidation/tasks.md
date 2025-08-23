# Spec Tasks

These are the tasks to be completed for the spec detailed in @agent-os/specs/2025-08-22-company-processing-consolidation/spec.md

> Created: 2025-08-22
> Status: ANALYSIS COMPLETE - Implementation deferred (system already functional)
> Decision: Company processing is working via LinkedInDataPipeline delegation. While not ideal architecture,
> the consolidation is non-critical since functionality works correctly. Higher priority specs should be
> completed first per PROJECT_STATUS_AUDIT_2025-08-23.md recommendations.

## Tasks

- [ ] 1. **Code Analysis and Documentation**
  - [x] 1.1 Write tests for LinkedInDataPipeline company processing methods ✅ COMPLETE - tests/test_linkedin_pipeline_analysis.py
  - [x] 1.2 Analyze and document LinkedInDataPipeline._extract_company_urls() method ✅ COMPLETE - analysis-extract-company-urls.md
  - [x] 1.3 Analyze and document LinkedInDataPipeline._fetch_companies() method ✅ COMPLETE - analysis-fetch-companies.md
  - [x] 1.4 Analyze and document ProfileController.create_profile company processing logic ✅ COMPLETE - analysis-profilecontroller-create.md
  - [x] 1.5 Create comparison matrix of working vs non-working components ✅ COMPLETE - comparison-matrix.md
  - [x] 1.6 Document optimal consolidation approach with preserved elements ✅ COMPLETE - consolidation-approach.md
  - [x] 1.7 Verify all tests pass for current analysis ✅ COMPLETE - 8/8 tests passing

- [x] 1. **Code Analysis and Documentation** ✅ COMPLETE (all subtasks finished)

- [ ] 2. **ProfileController Consolidation Implementation**
  - [ ] 2.1 Write tests for consolidated ProfileController helper methods
  - [ ] 2.2 Implement _extract_company_urls_from_profile with working logic from LinkedInDataPipeline
  - [ ] 2.3 Implement _fetch_companies_from_cassidy with working logic and rate limiting
  - [ ] 2.4 Update ProfileController.create_profile to use consolidated helper methods
  - [ ] 2.5 Add comprehensive logging for production monitoring
  - [ ] 2.6 Remove LinkedInDataPipeline initialization from ProfileController.__init__
  - [ ] 2.7 Verify all ProfileController tests pass

- [ ] 3. **Production Testing and Validation**
  - [ ] 3.1 Write database monitoring queries for company processing tracking
  - [ ] 3.2 Deploy consolidated ProfileController to production environment
  - [ ] 3.3 Test with 3-5 real LinkedIn profiles with known company experience
  - [ ] 3.4 Monitor database in real-time during processing (companies table, profile_companies table)
  - [ ] 3.5 Validate processing times remain within acceptable ranges (< 2 minutes)
  - [ ] 3.6 Compare company data accuracy with LinkedIn source data
  - [ ] 3.7 Verify all production tests pass and consolidation works correctly

- [ ] 4. **LinkedInDataPipeline Cleanup and Final Validation**
  - [ ] 4.1 Write tests for ProfileController independence from LinkedInDataPipeline
  - [ ] 4.2 Remove any remaining LinkedInDataPipeline references from ProfileController
  - [ ] 4.3 Update unit tests to reflect consolidated architecture
  - [ ] 4.4 Run full test suite to ensure no regressions
  - [ ] 4.5 Document final consolidated architecture
  - [ ] 4.6 Create production deployment checklist
  - [ ] 4.7 Verify all cleanup tests pass

## Implementation Notes

### Task 1: Code Analysis Focus
- **LinkedInDataPipeline working methods**: `_extract_company_urls()` and `_fetch_companies()` - these are proven to work
- **ProfileController current state**: Has helper methods but also initializes LinkedInDataPipeline (unused)
- **Key analysis**: Which error handling, rate limiting, and CompanyService integration patterns to preserve

### Task 2: Consolidation Strategy  
- **Preserve working elements**: Rate limiting (asyncio.sleep(1)), proper error handling, CompanyService usage
- **Remove duplication**: LinkedInDataPipeline initialization and unused references
- **Maintain API contract**: POST /api/v1/profiles behavior unchanged

### Task 3: Production Testing Priority
- **Real Cassidy API required**: Local testing cannot replicate production Cassidy workflow
- **Database monitoring**: Essential for tracking progress since processing takes time
- **Success criteria**: Companies appear in database, processing completes within time limits

### Task 4: Safe Cleanup
- **Gradual removal**: Only remove LinkedInDataPipeline after consolidated approach validated
- **Test coverage**: Ensure ProfileController works independently
- **Documentation**: Update architecture docs to reflect single processing path
