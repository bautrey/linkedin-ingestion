# Production Deployment Checklist

This checklist ensures all required configurations and verifications are completed before deploying the LinkedIn Ingestion Service to production on Railway.

## Pre-Deployment Setup

### 1. Environment Configuration ✅
- [x] Created `.env.production` with production-specific settings
- [x] Created `railway.toml` deployment configuration
- [ ] Verified all environment variables are properly set

### 2. Railway Service Variables Setup
The following environment variables must be configured in the Railway dashboard:

#### Database Configuration
- [ ] `DATABASE_URL` - Railway PostgreSQL connection string
- [ ] `SUPABASE_URL` - Supabase project URL
- [ ] `SUPABASE_ANON_KEY` - Supabase anonymous key
- [ ] `SUPABASE_SERVICE_KEY` - Supabase service role key

#### API Keys & Security
- [ ] `API_KEY` - Production API key for service authentication
- [ ] `OPENAI_API_KEY` - OpenAI API key for LLM scoring functionality

#### External Service URLs
- [ ] `CASSIDY_PROFILE_WORKFLOW_URL` - Cassidy LinkedIn profile workflow endpoint
- [ ] `CASSIDY_COMPANY_WORKFLOW_URL` - Cassidy company data workflow endpoint

#### Domain Configuration
- [ ] `ALLOWED_ORIGINS` - Production domains for CORS (Railway app URL + custom domain)

### 3. Database Migration
- [ ] Run database migrations: `python scripts/migrate.py`
- [ ] Verify all tables exist and are properly configured
- [ ] Test database connectivity with production credentials

### 4. Dependency Management
- [ ] Ensure `requirements.txt` is up to date
- [ ] Verify no development-only dependencies in production

## Deployment Process

### 1. Code Preparation
- [ ] Merge latest changes to main branch
- [ ] Update version in `version.json` (if applicable)
- [ ] Tag release version in git
- [ ] Push to repository

### 2. Railway Deployment
- [ ] Connect Railway to GitHub repository
- [ ] Configure auto-deploy from main branch
- [ ] Set up PostgreSQL plugin in Railway
- [ ] Configure all required environment variables
- [ ] Deploy service

### 3. Post-Deployment Verification

#### Health Checks
- [ ] Verify health endpoint responds: `GET /api/v1/health`
- [ ] Check service logs for startup errors
- [ ] Confirm database connectivity

#### API Endpoint Testing
- [ ] Test profile endpoints: `GET /api/v1/profiles`
- [ ] Test enhanced ingestion: `POST /api/v1/profiles/enhanced`
- [ ] Test batch enhanced ingestion: `POST /api/v1/profiles/batch-enhanced`
- [ ] Test company endpoints: `GET /api/v1/companies`
- [ ] Test template endpoints: `GET /api/v1/templates`

#### Authentication & Security
- [ ] Verify API key authentication works
- [ ] Test rate limiting functionality
- [ ] Confirm CORS configuration

#### Integration Testing
- [ ] Test Cassidy AI workflow integration
- [ ] Verify OpenAI API integration (if enabled)
- [ ] Test vector search functionality (if enabled)

### 4. Make.com Integration Verification
- [ ] Test existing Make.com workflows still function
- [ ] Verify webhook endpoints are accessible
- [ ] Check Make.com automation scenarios
- [ ] Validate data format compatibility

## Monitoring & Observability

### 1. Logging Setup
- [ ] Verify structured JSON logging is enabled
- [ ] Check log levels are appropriate for production
- [ ] Ensure sensitive data is not logged

### 2. Performance Monitoring
- [ ] Monitor API response times
- [ ] Check database query performance
- [ ] Verify memory and CPU usage
- [ ] Monitor Cassidy AI workflow response times

### 3. Error Tracking
- [ ] Set up error alerting (if applicable)
- [ ] Monitor error rates and types
- [ ] Track failed ingestion attempts

## Production Hardening

### 1. Security
- [ ] Rotate API keys if needed
- [ ] Verify no debug information exposed
- [ ] Confirm rate limiting is enforced
- [ ] Check input validation on all endpoints

### 2. Performance
- [ ] Configure appropriate worker count
- [ ] Set proper timeout values
- [ ] Optimize database connections
- [ ] Enable async processing features

### 3. Reliability
- [ ] Set up health check monitoring
- [ ] Configure restart policies
- [ ] Test failover scenarios
- [ ] Verify backup procedures

## Rollback Plan

### In Case of Issues
- [ ] Document rollback procedure
- [ ] Keep previous working version tagged
- [ ] Have database rollback plan (if schema changes)
- [ ] Prepare communication plan for stakeholders

## Post-Deployment Tasks

### 1. Documentation Updates
- [ ] Update README with production URLs
- [ ] Document any new environment variables
- [ ] Update API documentation with production examples

### 2. Team Communication
- [ ] Notify team of successful deployment
- [ ] Share production URLs and access information
- [ ] Update project management tools

### 3. Follow-up Monitoring
- [ ] Monitor for 24-48 hours post-deployment
- [ ] Check Make.com automation performance
- [ ] Review user feedback and error reports
- [ ] Plan next iteration improvements

## Environment-Specific Notes

### Railway Configuration
- **Build Command**: `pip install -r requirements.txt && python scripts/migrate.py --check-only`
- **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 2`
- **Health Check**: `/api/v1/health` (30s timeout, 30s interval)
- **Port**: Uses Railway's `$PORT` environment variable

### Production Settings
- **Environment**: `ENVIRONMENT=production`
- **Debug**: `DEBUG=false` 
- **Workers**: 2 (optimized for Railway resource limits)
- **Rate Limits**: 100 requests/minute (increased from development)
- **Logging**: JSON format for structured logs

---

**Last Updated**: 2024-01-XX
**Version**: 2.1.0-development+ae6d5ec9
