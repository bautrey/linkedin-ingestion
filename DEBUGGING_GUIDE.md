# LinkedIn Ingestion Service - Debugging Guide

## Memory Server Integration

### Overview
The Memory Keeper MCP server is a critical tool for debugging and knowledge retention across development sessions. It's visible in Warp terminal as a running service with green status indicator.

### Core Tools
- **`create_entities`**: Store new findings, issues, solutions, patterns
- **`create_relations`**: Link related concepts and dependencies  
- **`add_observations`**: Update existing entities with new information
- **`search_nodes`**: Find previously stored debugging solutions
- **`read_graph`**: Explore the full knowledge graph
- **`open_nodes`**: Access detailed entity information

### Usage Patterns
```javascript
// Store a new debugging finding
call_mcp_tool("create_entities", {
  "entities": [{
    "entityType": "issue",
    "name": "API Connection Problem", 
    "observations": ["Details about the issue and solution"]
  }]
})

// Search for past solutions
call_mcp_tool("search_nodes", {
  "query": "API connection"
})
```

## Common Debugging Scenarios

### 1. UI Shows "No Data Found" or Empty Lists

**Root Cause Patterns:**
- API connectivity issues
- Wrong API endpoints (localhost vs production)
- Template rendering conditions failing
- Data structure assumptions

**Debugging Steps:**
1. Check server logs for API call traces
2. Verify environment variables in `.env` file
3. Test API endpoints directly with curl
4. Add temporary debug output to templates
5. Inspect network requests in browser dev tools

**Recent Example:**
- **Issue**: Scoring jobs showing "No scoring jobs found"
- **Cause**: Template condition `jobs && jobs.length > 0` was working correctly, but data wasn't being enriched
- **Solution**: Debug logging revealed the issue, fixed by adding profile name enrichment

### 2. Missing Profile Names or "Unknown Profile"

**Root Cause:**
- API response structure assumptions
- Missing data enrichment
- Incorrect field extraction

**Solution Pattern:**
```javascript
// Add enrichment in route handlers
const enrichedJobs = await Promise.all(
  jobs.slice(0, 20).map(async (job) => {
    if (job.profile_id) {
      const profileResponse = await apiClient.get(`/profiles/${job.profile_id}`);
      job.profile_name = profileResponse.data?.name || 'Unknown Profile';
    }
    return job;
  })
);
```

### 3. Environment Variable Issues

**Common Typos:**
- `FASAPI_BASE_URL` → `FASTAPI_BASE_URL`
- Missing protocol: `smooth-mailbox-production.up.railway.app` → `https://smooth-mailbox-production.up.railway.app`

**Verification:**
```bash
# Check current values
echo "FASTAPI_BASE_URL: $FASTAPI_BASE_URL"

# Test API connectivity
curl -H "X-API-Key: $API_KEY" "$FASTAPI_BASE_URL/api/v1/health"
```

### 4. API Testing Best Practices

**Always Test Production First:**
- Use Railway deployment URL: `https://smooth-mailbox-production.up.railway.app`
- Include proper API key in headers: `X-API-Key: li_HieZz-IjBp0uE7d-rZkRE0qyy12r5_ZJS_FR4jMvv0I`
- Don't assume localhost issues when production API is available

**Example Commands:**
```bash
# Test scoring jobs endpoint
curl -s -H "X-API-Key: li_HieZz-IjBp0uE7d-rZkRE0qyy12r5_ZJS_FR4jMvv0I" \
  "https://smooth-mailbox-production.up.railway.app/api/v1/scoring-jobs" | jq '.jobs[0]'

# Test profile endpoint  
curl -s -H "X-API-Key: li_HieZz-IjBp0uE7d-rZkRE0qyy12r5_ZJS_FR4jMvv0I" \
  "https://smooth-mailbox-production.up.railway.app/api/v1/profiles/{id}" | jq '.name'
```

## Systematic Debugging Approach

### 1. Gather Information
- Check server logs: `tail -f logs/server.log`
- Test API directly with curl
- Inspect browser network requests
- Add temporary debug logging

### 2. Verify Assumptions
- API endpoint URLs
- Response data structures  
- Environment variable values
- Template condition logic

### 3. Document in Memory Server
```javascript
// Store the debugging pattern for future reference
call_mcp_tool("create_entities", {
  "entities": [{
    "entityType": "debugging_pattern",
    "name": "UI Empty State Debugging",
    "observations": [
      "Issue: UI shows no data",
      "Steps: 1) Check logs 2) Test API 3) Verify templates",
      "Common causes: API connectivity, data structure assumptions",
      "Solution: Add debug output, test production endpoints"
    ]
  }]
})
```

### 4. Avoid Repeating Mistakes
- Search memory server before debugging: `search_nodes("similar issue")`
- Test production APIs before assuming connection issues
- Add meaningful logging instead of restarting services unnecessarily
- Document successful solutions for future reference

## Production Environment Details

**FastAPI Backend:**
- URL: `https://smooth-mailbox-production.up.railway.app`
- API Key: `li_HieZz-IjBp0uE7d-rZkRE0qyy12r5_ZJS_FR4jMvv0I` 
- Base Path: `/api/v1`

**Admin UI:**
- Local Port: `3003`
- Logs: `logs/server.log`, `logs/admin-ui.log`
- Environment: `.env` file (check for typos)

**Key Endpoints:**
- `/scoring-jobs` - Get all scoring jobs with stats
- `/profiles/{id}` - Get profile details by ID
- `/templates` - Get available scoring templates
