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

## Supabase Production Migrations - DEFINITIVE PROCESS
**Date**: 2025-08-12
**NEVER FORGET**: This process was figured out multiple times - use it every time

### The ONLY Way to Apply Schema Changes to Production Supabase

**Step 1: Create Migration File**
```bash
# Create migration in supabase/migrations/
supabase migration new [description]
# OR manually create: supabase/migrations/YYYYMMDDHHMMSS_[description].sql
```

**Step 2: Apply to Production**
```bash
# NEVER use psql, pooler, or connection strings
# ALWAYS use Supabase CLI with production password from .env
source .env
supabase db push --password "$SUPABASE_PASSWORD"
```

**Step 3: Handle PostgreSQL Syntax Issues**
- PostgreSQL does NOT support `CREATE TRIGGER IF NOT EXISTS`
- Use: `DROP TRIGGER IF EXISTS [name] ON [table]; CREATE TRIGGER [name]...`
- Always test trigger syntax in migration files

**Critical Commands That DON'T Work**:
- ❌ `psql "postgresql://postgres:password@host:port/db"`
- ❌ `psql -h aws-0-us-west-1.pooler.supabase.com`
- ❌ Any direct PostgreSQL connection attempts
- ❌ MCP tools or API-based approaches

**The ONLY Command That Works**:
- ✅ `supabase db push --password "$SUPABASE_PASSWORD"` (after sourcing .env)

**Environment Setup**:
```bash
# Check project is linked
supabase projects list
# Should show: ● yirtidxcgkkoizwqpdfv | bautrey's Project

# Verify migration directory exists
ls supabase/migrations/

# Load environment variables (password should be in .env file)
source .env
supabase db push --password "$SUPABASE_PASSWORD"
```

**Password**: Stored in `.env` file as `SUPABASE_PASSWORD=...`

---

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
  - Used correct CLI command: `supabase db push --password "$SUPABASE_PASSWORD"` (from .env file)
  - Migration applied successfully with all constraints and indexes
- **Production Test**: Job creation works (job ID: ee55144a-258b-49c8-88e7-26f2a0ea6152)
- **V1.85 Progress**: Tasks 1-3 fully implemented per commit d222a87 (60% complete)
- **Current Blocker**: Task 4 - Async job processing system (jobs stuck in "processing" status)
- **Next Session Focus**: Implement background worker to process scoring jobs

## Railway Deployment Monitoring
**Date**: 2025-08-12
**Issue**: No good way to monitor Railway deployment status without locking terminal

- **Problem**: Commands like `railway logs` lock the terminal and require Ctrl+C
- **Need**: Better command pattern for monitoring deployment progress
- **Current Workaround**: Check health endpoint periodically
- **TODO**: Investigate `railway logs --build` with proper timeout/pagination
