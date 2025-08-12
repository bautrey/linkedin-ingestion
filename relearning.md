# LinkedIn Ingestion Project - Relearning Notes

## API Authentication 
**Date**: 2025-08-12
**Key Learning**: The production API requires authentication using the `x-api-key` header.

- **API Key**: `li_HieZz-IjBp0uE7d-rZkRE0qyy12r5_ZJS_FR4jMvv0I`
- **Header Format**: `x-api-key: li_HieZz-IjBp0uE7d-rZkRE0qyy12r5_ZJS_FR4jMvv0I`
- **Found In**: Session file `sessions/linkedin-ingestion-session-2025-07-25-165400.md` lines 16, 33, 63-64
- **Usage Pattern**: 
  ```bash
  curl -X POST "https://smooth-mailbox-production.up.railway.app/api/v1/profiles/{id}/score" \
    -H "Content-Type: application/json" \
    -H "x-api-key: li_HieZz-IjBp0uE7d-rZkRE0qyy12r5_ZJS_FR4jMvv0I" \
    -d '{"prompt": "...", "model": "gpt-3.5-turbo"}'
  ```

## V1.85 LLM Scoring Issues
**Date**: 2025-08-12
**Issue**: Scoring job creation fails with "JSON could not be generated, code 404"

- **Root Cause**: Database migration for `scoring_jobs` table was not applied to production Supabase database
- **Error**: `{"detail":{"error_code":"JOB_CREATION_FAILED","message":"Failed to create scoring job","details":{"profile_id":"...","error":"{'message': 'JSON could not be generated', 'code': 404, 'hint': 'Refer to full message for details', 'details': \"b'{}'\"}"}}}}`
- **Tested Profile IDs**: 
  - `cc6291b5-9c98-4131-9bd6-b0276f359d70` (failed)
  - `435ccbf7-6c5e-4e2d-bdc3-052a244d7121` (failed - valid profile from /profiles API)
- **Status**: ✅ RESOLVED - Database migration successfully applied to production
- **Solution Applied**: Used Supabase CLI to push migration to production
- **Migration File**: Contains complete table creation with indexes, constraints, RLS policies
- **Resolution Details**:
  - Fixed PostgreSQL syntax issue: `CREATE TRIGGER IF NOT EXISTS` → `DROP TRIGGER IF EXISTS` + `CREATE TRIGGER`
  - Used correct CLI command: `supabase db push --password "dvm2rjq6ngk@GZN-wth"`
  - Migration applied successfully with all constraints and indexes

## Railway Deployment Monitoring
**Date**: 2025-08-12
**Issue**: No good way to monitor Railway deployment status without locking terminal

- **Problem**: Commands like `railway logs` lock the terminal and require Ctrl+C
- **Need**: Better command pattern for monitoring deployment progress
- **Current Workaround**: Check health endpoint periodically
- **TODO**: Investigate `railway logs --build` with proper timeout/pagination
