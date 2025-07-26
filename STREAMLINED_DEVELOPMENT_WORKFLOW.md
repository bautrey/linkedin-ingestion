# Streamlined Development Workflow - LinkedIn Ingestion

## 🚀 Efficient Development Process (30-45 minutes per feature)

### Quick Session Recovery (2 minutes)
```bash
# 1. Navigate to project
cd /Users/burke/projects/linkedin-ingestion

# 2. Quick session recovery (use local session-recovery.md)
# Read: linkedin-ingestion-SESSION_HISTORY.md for context
# Read: latest session file from ./sessions/ for details

# 3. Activate environment
source venv/bin/activate
```

### Rapid Local Development (15-20 minutes)
```bash
# 1. Start local server (background)
python main.py &
sleep 3

# 2. Test locally while developing
curl -s "http://localhost:8000/api/v1/health"
curl -s -H "x-api-key: li_HieZz-IjBp0uE7d-rZkRE0qyy12r5_ZJS_FR4jMvv0I" "http://localhost:8000/api/v1/profiles?limit=1"

# 3. Stop when done
kill %1
```

### Efficient Deployment (10-15 minutes)
```bash
# 1. Commit changes
git add .
git commit -m "feat: [feature description]"

# 2. Deploy to Railway (with timeout protection)
railway redeploy &
DEPLOY_PID=$!
sleep 60  # Wait for deployment
kill $DEPLOY_PID 2>/dev/null || true

# 3. Wait additional time for container startup
sleep 30

# 4. Test production immediately
curl -s -H "x-api-key: li_HieZz-IjBp0uE7d-rZkRE0qyy12r5_ZJS_FR4jMvv0I" \
  "https://smooth-mailbox-production.up.railway.app/api/v1/profiles?limit=1"
```

### Quick Validation Checklist (5 minutes)
```bash
# Essential production tests
curl -s "https://smooth-mailbox-production.up.railway.app/"  # Root should return JSON
curl -s "https://smooth-mailbox-production.up.railway.app/api/v1/health"  # Health check
curl -s -H "x-api-key: li_HieZz-IjBp0uE7d-rZkRE0qyy12r5_ZJS_FR4jMvv0I" \
  "https://smooth-mailbox-production.up.railway.app/api/v1/profiles?limit=1"  # API works
```

## 🎯 Time Optimization Lessons

### What Actually Takes Time:
- **Session Recovery**: 2 minutes (when docs are accurate)
- **Core Development**: 15-20 minutes (with local testing)  
- **Deployment**: 10-15 minutes (with proper timeout handling)
- **Validation**: 5 minutes (focused tests)

### What Wastes Time:
- ❌ Inaccurate deployment documentation
- ❌ Railway commands that hang indefinitely
- ❌ Testing wrong URLs or missing API keys
- ❌ Not having session context readily available

## 🛠️ Streamlined Tools & Commands

### Essential Aliases (add to ~/.zshrc)
```bash
alias li-dev="cd /Users/burke/projects/linkedin-ingestion && source venv/bin/activate"
alias li-start="python main.py &"
alias li-stop="kill %1"
alias li-test="curl -s -H 'x-api-key: li_HieZz-IjBp0uE7d-rZkRE0qyy12r5_ZJS_FR4jMvv0I'"
alias li-deploy="railway redeploy & sleep 60; kill $! 2>/dev/null || true; sleep 30"
```

### Quick Test Script
```bash
# Create test-api.sh
#!/bin/bash
API_KEY="li_HieZz-IjBp0uE7d-rZkRE0qyy12r5_ZJS_FR4jMvv0I"
BASE_URL="https://smooth-mailbox-production.up.railway.app"

echo "Testing LinkedIn Ingestion API..."
echo "1. Root endpoint:"
curl -s "$BASE_URL/"
echo -e "\n\n2. Health check:"
curl -s "$BASE_URL/api/v1/health"
echo -e "\n\n3. Profiles list:"
curl -s -H "x-api-key: $API_KEY" "$BASE_URL/api/v1/profiles?limit=1"
echo -e "\n\nAPI tests complete!"
```

## 📋 Feature Development Template

### 1. Session Start (2 min)
- `cd /Users/burke/projects/linkedin-ingestion`
- Read session history for context
- `source venv/bin/activate`

### 2. Develop (15-20 min)
- Start local server: `python main.py &`
- Code changes
- Test locally: `curl localhost:8000/...`
- Stop server: `kill %1`

### 3. Deploy (10-15 min)  
- `git add . && git commit -m "feat: ..."`
- `railway redeploy &` (with timeout)
- Wait 90 seconds total
- Test production

### 4. Validate (5 min)
- Run essential curl tests
- Update AgentOS task status
- Commit documentation updates

**Total: 30-45 minutes per feature**

## 🚨 Critical Rules for Speed

1. **NEVER** use `railway up` or `railway logs` without timeout
2. **ALWAYS** test locally before deploying  
3. **ALWAYS** use the correct production URL with API key
4. **ALWAYS** have session context before starting work
5. **NEVER** assume deployment worked - always test

## 🎉 Success Metrics

- **Feature Implementation**: 15-20 minutes
- **Deployment + Testing**: 15-20 minutes  
- **Documentation Updates**: 5-10 minutes
- **Total Feature Delivery**: 30-45 minutes

This workflow enables rapid feature development while maintaining production quality and proper documentation.
