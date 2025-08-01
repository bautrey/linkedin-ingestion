# Railway Deployment Guide - LinkedIn Ingestion Service

## ✅ AUTO-DEPLOY ENABLED

**Good News:** This project now uses Railway's GitHub auto-deploy feature!

## 🎯 Current Deployment Process

### 1. Find the Correct Railway URL
```bash
# This command shows RAILWAY_PUBLIC_DOMAIN which is the correct URL
railway variables

# Look for this line:
# RAILWAY_PUBLIC_DOMAIN │ smooth-mailbox-production.up.railway.app
```

**CORRECT URL:** `https://smooth-mailbox-production.up.railway.app`
**WRONG URL:** `https://smooth-mailbox.railway.app` (this doesn't work)

### 2. Deploy Code Changes (AUTO-DEPLOY)
```bash
# ✅ SIMPLE AUTO-DEPLOY PROCESS:

# 1. Make your code changes
# 2. Commit and push to GitHub
git add .
git commit -m "your changes"
git push origin master

# 3. Railway automatically deploys (~60-70 seconds)
# No manual railway commands needed!

# 4. Wait for deployment to complete
sleep 70

# 5. Test the deployment
curl -s "https://smooth-mailbox-production.up.railway.app/api/v1/health"
```

### 3. Monitor Deployment
```bash
# Check deployment status in Railway dashboard
railway open

# Or check status via CLI
railway status

# View recent deployments (will show "GitHub" as source)
```

### 4. Test Deployment
```bash
# Test root endpoint first
curl -s "https://smooth-mailbox-production.up.railway.app/"

# Should return JSON with service info, not Railway's default page

# Test health endpoint
curl -s "https://smooth-mailbox-production.up.railway.app/api/v1/health"

# Test secured endpoint without API key (should return 403)
curl -s -X POST "https://smooth-mailbox-production.up.railway.app/api/v1/profiles/ingest" \
  -H "Content-Type: application/json" \
  -d '{"linkedin_url": "https://linkedin.com/in/test"}'

# Test secured endpoint with API key (should process request)
curl -s -X POST "https://smooth-mailbox-production.up.railway.app/api/v1/profiles/ingest" \
  -H "Content-Type: application/json" \
  -H "x-api-key: li_HieZz-IjBp0uE7d-rZkRE0qyy12r5_ZJS_FR4jMvv0I" \
  -d '{"linkedin_url": "https://linkedin.com/in/test"}'
```

## 🔧 Local Testing First

**ALWAYS test locally before deploying:**

```bash
# Start local server
python main.py &

# Wait for startup
sleep 3

# Test locally
curl -s "http://localhost:8000/"
curl -s "http://localhost:8000/api/v1/health"

# Test API security locally
curl -s -X POST "http://localhost:8000/api/v1/profiles/ingest" \
  -H "Content-Type: application/json" \
  -d '{"linkedin_url": "https://linkedin.com/in/test"}'

# Should return 403 Forbidden

curl -s -X POST "http://localhost:8000/api/v1/profiles/ingest" \
  -H "Content-Type: application/json" \
  -H "x-api-key: li_HieZz-IjBp0uE7d-rZkRE0qyy12r5_ZJS_FR4jMvv0I" \
  -d '{"linkedin_url": "https://linkedin.com/in/test"}'

# Should process request (may fail on invalid LinkedIn URL)

# Stop local server
kill %1
```

## 📋 Deployment Checklist

- [ ] Test changes locally first
- [ ] Commit and push code changes
- [ ] Wait 60+ seconds for deployment
- [ ] Get correct URL with `railway variables`
- [ ] Test root endpoint returns JSON (not Railway default page)
- [ ] Test API endpoints work as expected
- [ ] Test API security (403 without key, processes with key)

## 🐛 Common Issues & Solutions

### Issue: Service returns Railway default page
**Cause:** Testing wrong URL or deployment not complete
**Solution:** 
1. Use `railway variables` to get correct URL
2. Wait longer for deployment to complete
3. Check if Procfile and main.py are correct

### Issue: 404 on all endpoints
**Cause:** App structure issues or import problems
**Solution:**
1. Test locally first to verify app works
2. Check imports in main.py match project structure
3. Verify Procfile points to correct entry point

### Issue: Can't tell if deployment succeeded
**Cause:** Using hanging railway commands
**Solution:**
1. Never use `railway logs` or `railway up`
2. Test with curl commands instead
3. Use `railway variables` and `railway status`

## 🔑 API Security Configuration

**Generated API Key:** `li_HieZz-IjBp0uE7d-rZkRE0qyy12r5_ZJS_FR4jMvv0I`

**Make.com HTTP Module Settings:**
- **URL:** `https://smooth-mailbox-production.up.railway.app/api/v1/profiles/ingest`
- **Method:** POST
- **Headers:**
  - `Content-Type`: `application/json`
  - `x-api-key`: `li_HieZz-IjBp0uE7d-rZkRE0qyy12r5_ZJS_FR4jMvv0I`
- **Body:** `{"linkedin_url": "{{32.LinkedIn.value}}"}`

## 📝 Environment Variables

Key environment variables set in Railway:
- `API_KEY`: `li_HieZz-IjBp0uE7d-rZkRE0qyy12r5_ZJS_FR4jMvv0I`
- All other variables from app/core/config.py

## 🎯 Success Indicators

**Deployment is successful when:**
1. Root URL returns JSON service info (not Railway default page)
2. Health endpoint returns status info
3. Protected endpoints return 403 without API key
4. Protected endpoints process requests with correct API key
5. No import errors or application startup failures

**Deployment has failed when:**
1. Railway default page is shown
2. All endpoints return 404
3. Application startup errors in logs (if viewable)

---

## 📚 Reference Commands

```bash
# Safe Railway commands (don't hang)
railway status
railway variables
railway open

# Dangerous Railway commands (AVOID - they hang)
railway logs
railway up

# Testing commands
curl -s "https://smooth-mailbox-production.up.railway.app/"
curl -s "https://smooth-mailbox-production.up.railway.app/api/v1/health"

# Local testing
python main.py &
curl -s "http://localhost:8000/"
kill %1
```

This guide prevents the common deployment issues we experienced and ensures reliable Railway deployments.
