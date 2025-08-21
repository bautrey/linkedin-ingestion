# Pytest Execution Learning: Production Workflow Hangs

**Date**: 2025-08-21 03:23
**Issue**: Production workflow tests hanging on execution
**Context**: LinkedIn ingestion system with 436 tests

## Problem
- Tests hang immediately on `tests/production_workflows/test_profile_creation_workflow.py`
- No progress indication after collection phase
- User cannot tell if stuck or running normally
- Forces manual interruption with Ctrl+C

## Root Cause Analysis
Production workflow tests likely:
1. Making real API calls to LinkedIn/Cassidy
2. Timeout markers not properly configured (`@pytest.mark.timeout` warnings)
3. Network dependency causing indefinite waits
4. Database connection issues in test environment

## Immediate Solutions
1. **Skip production workflows**: `pytest --ignore=tests/production_workflows/`
2. **Run unit tests only**: `pytest app/tests/`
3. **Check specific test**: Examine what test_profile_creation_workflow.py actually does

## Learning for Future
- Production workflow tests should be isolated and optional
- Use clear timeout markers and mock external dependencies 
- Provide progress indication for long-running tests
- Consider marking production tests with `@pytest.mark.slow` for selective execution

## Project Context
- 436 total tests collected (132 production workflows + 304 unit tests)
- Clean git state on v2.1-company-model-backend branch
- Task 2.1.6 Company API recently completed
- **ISSUE DISCOVERED**: 9 unit test failures, 289 passed

## Unit Test Issues Found
1. **ExperienceEntry validation**: end_month expects string, getting int (6 errors)
2. **Async test configuration**: Enhanced profile ingestion tests not async-enabled (5 failures) 
3. **HTTP status mismatches**: 422 Unprocessable Entity vs expected 400/201 (4 failures)

## Next Actions
1. ✅ Fix ExperienceEntry validation in test fixtures (COMPLETE - fixed validator conflict)
2. ✅ Configure async tests properly with @pytest.mark.asyncio (COMPLETE - all async tests pass)
3. 🚧 Investigate HTTP status code expectations vs reality (5 failures remaining)
4. ✅ Run unit tests first, then address production workflows separately

## Progress Update
- **Fixed**: ExperienceEntry end_month validation conflict in app/cassidy/models.py
- **Fixed**: All enhanced profile ingestion async tests now pass (10/10)
- **Remaining**: 5 failures (down from 9): 1 assertion + 4 HTTP status mismatches
- **Test Status**: 299 passed, 5 failed (98.4% success rate)
