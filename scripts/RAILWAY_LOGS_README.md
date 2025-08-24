# Railway Logs - Terminal-Safe Log Retrieval System

A robust alternative to `railway logs` that prevents terminal hanging by using Railway's GraphQL API instead of the CLI streaming interface.

## 🚨 Problem Solved

The `railway logs` CLI command streams logs indefinitely and can hang your terminal, especially in Warp. This system:

- ✅ **Never hangs** - Uses bounded time windows instead of infinite streams
- ✅ **No Ctrl+C required** - Commands exit cleanly
- ✅ **Faster queries** - Direct API access with filtering
- ✅ **More features** - HTTP logs, advanced filtering, JSON output
- ✅ **Better UX** - Color-coded output, common patterns, time ranges

## 📦 Installation & Setup

### 1. Required Dependencies

Add to your `requirements.txt`:
```txt
requests>=2.28.0
```

Or install directly:
```bash
pip install requests
```

### 2. Railway API Token Setup

You need a Railway API token. Run the setup helper:

```bash
python3 scripts/setup_railway_token.py
```

**Option A: Use CLI Token (Easiest)**
```bash
# This should find your existing CLI token
python3 scripts/setup_railway_token.py
```

**Option B: Create Personal Token**
1. Go to https://railway.app/account/tokens
2. Create a new token
3. Set environment variable:
```bash
export RAILWAY_TOKEN="your_token_here"
# Add to ~/.zshrc for persistence
echo 'export RAILWAY_TOKEN="your_token_here"' >> ~/.zshrc
```

**Option C: Project Token**
1. In your Railway project dashboard
2. Go to Settings → Tokens
3. Create a new project token
4. Set environment variable as above

### 3. Verify Setup

```bash
# Test the GraphQL client
python3 scripts/railway_graphql.py

# Should show:
# ✅ Railway GraphQL client initialized successfully
# Project: d586086b-3ecb-404b-ad92-9672d36d1e3f
# Environment: cd226704-be4d-469d-8bb9-cb05bdcd1196
# Service: 7101a8bc-173b-4379-bbba-24ff74b8e9d2
```

## 🚀 Quick Start

### Method 1: Updated Shell Script (Easiest)

Your existing `safe_logs.sh` is now upgraded:

```bash
# Basic usage (deployment logs from last hour)
./safe_logs.sh

# Show only errors
./safe_logs.sh deployment --errors-only

# Get HTTP logs from last 30 minutes
./safe_logs.sh http --last-minutes 30

# Use pre-built patterns
./safe_logs.sh examples errors_last_hour
./safe_logs.sh examples http_5xx
./safe_logs.sh examples database_errors

# Show help
./safe_logs.sh help
```

### Method 2: Direct Python Scripts

```bash
# Direct CLI usage
python3 scripts/railway_logs.py deployment --limit 100
python3 scripts/railway_logs.py http --status-code 500
python3 scripts/railway_logs.py all --json --last-hours 2

# Pre-built patterns
python3 scripts/railway_examples.py errors_last_hour
python3 scripts/railway_examples.py slow_requests
```

## 📋 Usage Examples

### Common Scenarios

```bash
# 🔍 Debugging errors
./safe_logs.sh deployment --errors-only --last-hours 2

# 🌐 HTTP monitoring
./safe_logs.sh http --status-code ">=400" --last-minutes 30

# 📦 Build failures
./safe_logs.sh build --filter "failed OR error" --last-days 1

# 🔄 Recent activity (all logs)
./safe_logs.sh all --limit 100 --last-hours 1

# 📊 JSON export for analysis
./safe_logs.sh deployment --json --last-hours 6 > logs.json
```

### Pre-built Patterns

```bash
# Quick error detection
./safe_logs.sh examples errors_last_hour

# HTTP error monitoring  
./safe_logs.sh examples http_5xx

# Database issues
./safe_logs.sh examples database_errors

# Performance monitoring
./safe_logs.sh examples slow_requests

# Infrastructure monitoring
./safe_logs.sh examples memory_warnings

# Deployment tracking
./safe_logs.sh examples deployment_failures
./safe_logs.sh examples recent_builds
```

### Advanced Filtering

```bash
# Custom time ranges
./safe_logs.sh deployment --since "2023-08-24T10:00:00Z" --until "2023-08-24T11:00:00Z"

# Railway filter syntax
./safe_logs.sh deployment --filter "@level:error OR timeout OR \"500 Internal Server Error\""

# HTTP-specific filters
./safe_logs.sh http --method POST --status-code 500
./safe_logs.sh http --filter "@path:/api/v1/users AND @httpStatus:>=400"

# Combining options
./safe_logs.sh deployment --errors-only --filter "database" --last-hours 4 --limit 200
```

## 🛠️ API Reference

### RailwayGraphQL Class

```python
from scripts.railway_graphql import RailwayGraphQL

client = RailwayGraphQL()

# Get deployment logs
logs = client.get_deployment_logs(
    start_date=datetime(2023, 8, 24, 10, 0),
    end_date=datetime(2023, 8, 24, 11, 0),
    limit=200,
    log_filter="@level:error"
)

# Get HTTP logs
http_logs = client.get_http_logs(
    limit=100,
    log_filter="@httpStatus:>=500"
)

# Get build logs
build_logs = client.get_build_logs(
    limit=50,
    log_filter="failed OR error"
)
```

### Command Line Interface

```bash
# Available log types
python3 scripts/railway_logs.py {deployment|build|http|all} [options]

# Time options
--last-minutes N    # Last N minutes
--last-hours N      # Last N hours  
--last-days N       # Last N days
--since "ISO-DATE"  # Custom start time
--until "ISO-DATE"  # Custom end time

# Filtering options
--errors-only       # Only errors and warnings (deployment logs)
--filter "FILTER"   # Custom Railway filter syntax
--status-code CODE  # HTTP status code filter (http logs)
--method METHOD     # HTTP method filter (http logs)

# Output options
--limit N          # Maximum entries (default: 100)
--json             # JSON output format
```

## 🔧 Migration from CLI

| Old Command | New Command |
|-------------|-------------|
| `railway logs` | `./safe_logs.sh` |
| `railway logs \| head -20` | `./safe_logs.sh --limit 20` |
| `railway logs --deployment` | `./safe_logs.sh deployment` |
| `railway logs --build` | `./safe_logs.sh build` |
| `timeout 10s railway logs` | `./safe_logs.sh --last-minutes 5` |

## 🚨 Troubleshooting

### "Railway API token not found"
```bash
# Check if token is set
echo $RAILWAY_TOKEN

# Run setup helper
python3 scripts/setup_railway_token.py

# Manual setup
export RAILWAY_TOKEN="your_token_here"
```

### "Missing Railway configuration" 
```bash
# Ensure you're in a Railway project directory
railway status

# Check environment variables
env | grep RAILWAY_
```

### "No logs found"
```bash
# Try expanding time range
./safe_logs.sh --last-hours 24

# Remove filters to see all logs
./safe_logs.sh deployment --limit 200

# Check different log types
./safe_logs.sh all --last-hours 6
```

### "GraphQL errors" or "Authentication failed"
```bash
# Refresh Railway login
railway login

# Create new API token
# Visit: https://railway.app/account/tokens
```

## 🔄 Rate Limits & Performance

- **Rate Limits**: 1000 requests/hour, 10-50 RPS (plan dependent)
- **Automatic Backoff**: Built-in exponential backoff on rate limits
- **Batch Size**: Default 100-200 logs per request
- **Time Windows**: Always uses bounded ranges to prevent infinite queries
- **Caching**: Use `--json` output for processing/analysis without re-fetching

## 📈 Advanced Features

### JSON Processing

```bash
# Export for analysis
./safe_logs.sh all --json --last-hours 6 > analysis.json

# Process with jq
./safe_logs.sh deployment --json --errors-only | jq '.[] | select(.message | contains("timeout"))'

# Count error types
./safe_logs.sh deployment --json --errors-only | jq -r '.message' | sort | uniq -c | sort -nr
```

### Custom Patterns

Create your own pattern in `scripts/railway_examples.py`:

```python
def custom_api_errors(self):
    """Find API-specific errors"""
    class Args:
        log_type = 'deployment'
        filter = '"API" AND ("error" OR "failed" OR "exception")'
        last_hours = 2
        # ... other args
    
    logs = self.cli.get_deployment_logs(Args())
    # ... format and display
```

## 🔒 Security Notes

- API tokens have full project access - keep them secure
- Use project tokens (more restricted) instead of personal tokens when possible
- Never commit tokens to version control
- Consider token rotation for production environments

## 🆘 Support

For issues:
1. Check Railway API status: https://status.railway.app/
2. Verify token permissions in Railway dashboard
3. Try different time ranges or log types
4. Check network connectivity to `backboard.railway.app`

## 📚 Railway Filter Syntax Reference

```bash
# Level filtering
"@level:error"              # Only errors
"@level:error OR @level:warn"  # Errors and warnings

# HTTP filtering  
"@httpStatus:500"           # Exact status code
"@httpStatus:>=400"         # Status code range
"@method:POST"              # HTTP method
"@path:/api/v1/users"       # URL path

# Text filtering
'"exact phrase"'            # Exact phrase match
"database OR postgres"      # OR conditions  
"error AND timeout"         # AND conditions
"NOT success"               # Negation

# Time-based (handled by API parameters, not filters)
--last-hours 2              # Last 2 hours
--since "2023-08-24T10:00:00Z"  # Custom start time
```

---

🎉 **You now have a robust, terminal-safe Railway logs system!** 

No more hanging terminals, no more Ctrl+C, just reliable log access through Railway's GraphQL API.
