# LinkedIn Ingestion Pipeline - Production Deployment Guide

## Overview

This guide covers deploying the complete LinkedIn data ingestion pipeline to production, including database setup, environment configuration, and platform deployment.

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Cassidy API   │───▶│  FastAPI App    │───▶│  Supabase DB    │
│  (LinkedIn      │    │  (Pipeline      │    │  (PostgreSQL    │
│   Scraping)     │    │   Orchestrator) │    │   + pgvector)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   OpenAI API    │
                       │  (Embeddings)   │
                       └─────────────────┘
```

## Prerequisites

1. **Supabase Account**: Sign up at [supabase.com](https://supabase.com)
2. **OpenAI API Key**: Get from [platform.openai.com](https://platform.openai.com)
3. **Railway Account** (or preferred deployment platform)
4. **Cassidy AI Workflow URLs**: From your Cassidy setup

## Step 1: Database Setup

### 1.1 Create Supabase Project

1. Go to [supabase.com](https://supabase.com) and create a new project
2. Choose a project name and database password
3. Wait for the project to be created (takes ~2 minutes)

### 1.2 Enable pgvector Extension

1. Go to your Supabase dashboard
2. Navigate to **Database** → **Extensions**
3. Search for `vector` and enable the `pgvector` extension

### 1.3 Run Database Schema

1. Go to **SQL Editor** in your Supabase dashboard
2. Copy and paste the contents of `app/database/schema.sql`
3. Click **Run** to execute the schema creation

### 1.4 Get Database Credentials

1. Go to **Settings** → **API**
2. Copy the following values:
   - **Project URL** (for `SUPABASE_URL`)
   - **anon public** key (for `SUPABASE_ANON_KEY`)
   - **service_role** key (for `SUPABASE_SERVICE_KEY`)

## Step 2: Environment Configuration

### 2.1 Create Production Environment File

Create a `.env.production` file:

```bash
# Application
ENVIRONMENT=production
DEBUG=false
VERSION=1.0.0

# Cassidy AI Configuration
CASSIDY_PROFILE_WORKFLOW_URL=https://app.cassidyai.com/api/webhook/workflows/YOUR_PROFILE_WORKFLOW_ID?results=true
CASSIDY_COMPANY_WORKFLOW_URL=https://app.cassidyai.com/api/webhook/workflows/YOUR_COMPANY_WORKFLOW_ID?results=true
CASSIDY_TIMEOUT=300
CASSIDY_MAX_RETRIES=3
CASSIDY_BACKOFF_FACTOR=2.0

# Database Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
SUPABASE_SERVICE_KEY=your-service-key-here

# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-api-key-here

# Vector Configuration
VECTOR_DIMENSION=1536
SIMILARITY_THRESHOLD=0.8

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
CASSIDY_RATE_LIMIT=10

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Feature Flags
ENABLE_COMPANY_INGESTION=true
ENABLE_VECTOR_SEARCH=true
ENABLE_ASYNC_PROCESSING=true

# CORS (add your frontend domains)
ALLOWED_ORIGINS=["https://your-frontend-domain.com"]

# Optional: Monitoring
SENTRY_DSN=https://your-sentry-dsn-here
```

### 2.2 Validate Configuration

Run the configuration validation:

```bash
python -c "from app.core.config import settings; print('✓ Configuration valid')"
```

## Step 3: Local Testing

### 3.1 Install Dependencies

```bash
pip install -r requirements.txt
```

### 3.2 Run Tests

```bash
# Run unit tests
python test_basic_functionality.py

# Run database integration tests
python test_complete_pipeline.py
```

### 3.3 Test Health Endpoints

```bash
# Start the server
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Test health endpoint
curl http://localhost:8000/health
```

## Step 4: Railway Deployment

### 4.1 Prepare for Deployment

1. Create `railway.json`:

```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 100,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

2. Create `Procfile`:

```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### 4.2 Deploy to Railway

1. Install Railway CLI:
```bash
npm install -g @railway/cli
```

2. Login and deploy:
```bash
railway login
railway init

# Deploy with timeout protection (prevents hanging)
timeout 90s railway up

# OR use smart completion detection:
railway up | (grep -q -E "(Healthcheck succeeded|Starting Container)" && killall railway)
```

**Important**: `railway up` streams logs indefinitely after deployment completes. Always use timeout or completion detection to prevent hanging.

3. Add environment variables:
```bash
railway variables:set ENVIRONMENT=production
railway variables:set SUPABASE_URL=your-supabase-url
railway variables:set SUPABASE_ANON_KEY=your-anon-key
railway variables:set OPENAI_API_KEY=your-openai-key
# ... add all other environment variables
```

### 4.3 Verify Deployment

1. Check deployment status:
```bash
railway status
```

2. View logs:
```bash
railway logs
```

3. Test the deployed API:
```bash
# CORRECT Production URL (found via railway variables command)
curl https://smooth-mailbox-production.up.railway.app/api/v1/health

# DO NOT USE: https://smooth-mailbox.railway.app (this is wrong)
```

## Step 5: Alternative Deployment Options

### 5.1 Docker Deployment

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t linkedin-ingestion .
docker run -p 8000:8000 --env-file .env.production linkedin-ingestion
```

### 5.2 Heroku Deployment

1. Create `runtime.txt`:
```
python-3.11.6
```

2. Deploy:
```bash
heroku create your-app-name
heroku config:set ENVIRONMENT=production
heroku config:set SUPABASE_URL=your-supabase-url
# ... set all environment variables
git push heroku main
```

## Step 6: Monitoring and Maintenance

### 6.1 Set Up Monitoring

1. **Health Checks**: Configure uptime monitoring for `/health` endpoint
2. **Error Tracking**: Add Sentry DSN to environment variables
3. **Performance Monitoring**: Use Railway metrics or external APM

### 6.2 Database Maintenance

1. **Regular Backups**: Enable Supabase automated backups
2. **Index Monitoring**: Check query performance in Supabase dashboard
3. **Storage Monitoring**: Monitor database size and vector storage usage

### 6.3 API Rate Limiting

Monitor Cassidy API usage and OpenAI token consumption:

```bash
# Check pipeline health
curl https://smooth-mailbox.railway.app/api/v1/pipeline/health

# View recent ingestion stats
curl https://smooth-mailbox.railway.app/api/v1/profiles/recent
```

## Step 7: Usage Examples

### 7.1 Single Profile Ingestion

```bash
curl -X POST "https://smooth-mailbox.railway.app/api/v1/profiles/ingest" \
  -H "Content-Type: application/json" \
  -d '{"linkedin_url": "https://linkedin.com/in/example"}'
```

### 7.2 Batch Profile Ingestion

```bash
curl -X POST "https://smooth-mailbox.railway.app/api/v1/profiles/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "linkedin_urls": [
      "https://linkedin.com/in/example1",
      "https://linkedin.com/in/example2"
    ]
  }'
```

### 7.3 Similarity Search

```bash
curl -X POST "https://smooth-mailbox.railway.app/api/v1/profiles/similar" \
  -H "Content-Type: application/json" \
  -d '{
    "profile_id": "stored-profile-id",
    "limit": 10,
    "similarity_threshold": 0.8
  }'
```

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Verify Supabase URL and keys
   - Check if pgvector extension is enabled
   - Ensure database schema is created

2. **OpenAI API Errors**
   - Verify API key is valid
   - Check rate limits and quotas
   - Monitor token usage costs

3. **Cassidy API Timeouts**
   - Increase `CASSIDY_TIMEOUT` setting
   - Check Cassidy workflow status
   - Verify workflow URLs are correct

4. **Memory Issues**
   - Monitor vector storage usage
   - Consider upgrading Railway plan
   - Implement batch processing limits

### Debugging

Enable debug logging:
```bash
railway variables:set LOG_LEVEL=DEBUG
railway variables:set DEBUG=true
```

View detailed logs:
```bash
railway logs --follow
```

## Security Considerations

1. **Environment Variables**: Never commit API keys to version control
2. **Database Access**: Use service role key only for admin operations
3. **CORS Settings**: Restrict allowed origins in production
4. **Rate Limiting**: Implement proper rate limiting to prevent abuse
5. **Input Validation**: Ensure all LinkedIn URLs are validated
6. **Error Handling**: Don't expose sensitive information in error messages

## Cost Optimization

1. **OpenAI Usage**: Monitor embedding generation costs
2. **Database Storage**: Regular cleanup of old embeddings
3. **Railway Resources**: Monitor CPU and memory usage
4. **Cassidy API**: Optimize batch processing to reduce API calls

## Scaling Considerations

1. **Horizontal Scaling**: Use Railway's auto-scaling features
2. **Database Scaling**: Upgrade Supabase plan as needed
3. **Queue System**: Implement Redis/Celery for large batch jobs
4. **Caching**: Add Redis caching for frequently accessed data

---

## Support

For deployment issues:
1. Check Railway logs: `railway logs`
2. Test individual components: run health checks
3. Verify environment configuration
4. Monitor API quotas and limits

The pipeline is now ready for production use! 🚀
