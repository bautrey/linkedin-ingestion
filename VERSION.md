# Versioning System Documentation

## Overview

The LinkedIn Ingestion Service uses an automated versioning system that integrates with Railway deployments and GitHub Actions to provide real-time version information across both the backend API and admin UI.

## Version Format

Our versioning follows semantic versioning with deployment-specific extensions:

### Production
```
2.1.0+abc1234
```

### Development/Staging  
```
2.1.0-development+abc1234
```

Where:
- `2.1.0` = Base semantic version (major.minor.patch)
- `development` = Environment name (omitted for production)
- `abc1234` = Short git commit hash (8 characters)

## System Architecture

### Build-Time Version Generation
- **Script**: `scripts/version.sh`
- **Trigger**: Railway build process (via `nixpacks.toml`)
- **Output**: 
  - `version.json` (backend)
  - `admin-ui/version.json` (frontend)
  - Updated `app/core/config.py`

### Runtime Version Access
- **Backend Endpoint**: `/api/version` (public, no auth required)
- **Admin UI Endpoint**: `/version` 
- **Available in Templates**: `res.locals.versionInfo`

## Railway Integration

### Environment Variables Used
Railway automatically provides these during builds:

```bash
RAILWAY_GIT_COMMIT_SHA      # Full commit hash
RAILWAY_GIT_BRANCH          # Git branch name  
RAILWAY_GIT_AUTHOR          # Commit author
RAILWAY_GIT_MESSAGE         # Commit message
RAILWAY_SERVICE_ID          # Railway service identifier
RAILWAY_ENVIRONMENT_NAME    # Environment (production/staging)
RAILWAY_DEPLOYMENT_ID       # Unique deployment ID
```

### Build Process
1. Railway detects code changes
2. `nixpacks.toml` runs `scripts/version.sh`
3. Version info is injected into application
4. Application starts with current version metadata

## GitHub Actions Integration

### Workflow: `.github/workflows/version-tag.yml`
- **Triggers**: Push to `master`/`main` branch
- **Actions**: 
  - Generates version info
  - Creates GitHub release
  - Tags repository
  - Updates deployment status

### Release Format
```
Tag: v2.1.0-development+abc1234
Title: LinkedIn Ingestion v2.1.0-development+abc1234
Body: Includes version details, deployment info, API endpoints
```

## API Endpoints

### Backend Version Info
```http
GET /api/version
```

**Response:**
```json
{
  "version": "2.1.0-development+ae6d5ec9",
  "service": "LinkedIn Ingestion Service", 
  "timestamp": "2025-08-19T21:32:01Z",
  "base_version": "2.1.0",
  "build_time": "2025-08-19T21:32:01Z",
  "git": {
    "commit": "ae6d5ec9ca14b38d1ee6178dab8ba92db21892f9",
    "commit_short": "ae6d5ec9", 
    "branch": "master",
    "author": "Burke Autrey",
    "message": "Session hibernation: Complete testing infrastructure established"
  },
  "deployment": {
    "service_id": "local",
    "environment": "development",
    "deployment_id": "local-build",
    "platform": "railway"
  },
  "app": {
    "name": "linkedin-ingestion",
    "description": "LinkedIn Profile and Company Data Ingestion Service"
  }
}
```

### Admin UI Version Info
```http
GET /version
```

**Response:**
```json
{
  "version": "2.1.0-development+ae6d5ec9",
  "build_time": "2025-08-19T21:32:01Z",
  "git_commit": "ae6d5ec9",
  "git_branch": "master", 
  "environment": "development",
  "admin_ui_version": "1.0.0",
  "uptime": 42.7,
  "timestamp": "2025-08-19T21:35:00Z"
}
```

## Frontend Integration

### Version Display
The admin UI automatically displays version information in:
- Navigation bar or footer
- About/Version modal
- Server logs and health checks

### Template Access
All EJS templates have access to version info via:
```javascript
<%= versionInfo.version %>
<%= versionInfo.git_commit %>  
<%= versionInfo.build_time %>
```

## File Structure

```
linkedin-ingestion/
├── scripts/
│   └── version.sh                    # Version generation script
├── nixpacks.toml                     # Railway build configuration  
├── railway.json                      # Railway deployment config
├── version.json                      # Generated version metadata (backend)
├── admin-ui/
│   ├── version.json                  # Generated version metadata (frontend)
│   └── server.js                     # Version fetching logic
├── app/core/config.py               # Dynamic version loading
├── main.py                          # /api/version endpoint
└── .github/workflows/
    └── version-tag.yml              # Automated tagging workflow
```

## Development Workflow

### Local Testing
```bash
# Test version generation
cd linkedin-ingestion
bash scripts/version.sh

# Check generated files
cat version.json
cat admin-ui/version.json

# Verify backend endpoint
curl http://localhost:8000/api/version

# Verify admin UI endpoint  
curl http://localhost:3003/version
```

### Railway Deployment
1. Push changes to `master` branch
2. GitHub Actions creates release and tags
3. Railway detects push and starts build
4. Build script runs `scripts/version.sh` 
5. Application starts with version info
6. Endpoints serve current version data

## Troubleshooting

### Version Info Not Updating
1. **Check build logs** in Railway dashboard
2. **Verify script execution**: Look for version.sh output in logs
3. **Check environment variables**: Ensure Railway git vars are available
4. **Validate file generation**: version.json should exist

### Backend Endpoint Returns Default Version
1. **File missing**: version.json not generated during build
2. **Permissions**: Script may not be executable (check chmod +x)
3. **Build script error**: Check Railway build logs for errors
4. **Config loading**: Verify app/core/config.py loads version.json

### Admin UI Shows Stale Version
1. **Backend unreachable**: Admin UI falls back to local version.json
2. **Cache issues**: Restart admin UI service
3. **Network timeout**: Check FASTAPI_BASE_URL environment variable
4. **Version refresh**: Version info updates every 5 minutes

### GitHub Actions Workflow Fails
1. **Permissions**: Ensure `contents: write` permission is set
2. **Script path**: Verify scripts/version.sh exists and is executable
3. **JSON parsing**: Check version.json format is valid
4. **Token access**: GITHUB_TOKEN should be automatically available

## Environment Variables

### Required for Railway
```bash
# Automatically provided by Railway:
RAILWAY_GIT_COMMIT_SHA=full-commit-hash
RAILWAY_GIT_BRANCH=master
RAILWAY_GIT_AUTHOR="Your Name"
RAILWAY_GIT_MESSAGE="Commit message"
RAILWAY_SERVICE_ID=service-uuid
RAILWAY_ENVIRONMENT_NAME=production
RAILWAY_DEPLOYMENT_ID=deployment-uuid

# Optional customization:
FASTAPI_BASE_URL=https://your-api.up.railway.app
```

### Admin UI Configuration
```bash
FASTAPI_BASE_URL=http://localhost:8000    # Backend API URL
NODE_ENV=production                       # Environment mode
PORT=3003                                # Admin UI port
```

## Version Strategy

### Semantic Versioning
- **Major** (X.y.z): Breaking changes, incompatible API changes
- **Minor** (x.Y.z): New features, backwards compatible
- **Patch** (x.y.Z): Bug fixes, backwards compatible

### Environment-Specific Versions
- **Production**: Clean versions (2.1.0+abc1234)
- **Staging**: Tagged with environment (2.1.0-staging+abc1234) 
- **Development**: Tagged with environment (2.1.0-development+abc1234)

### Git Integration
- **Commit Hash**: Always included for traceability
- **Branch Name**: Included in deployment metadata
- **Author/Message**: Available in detailed version info

## Deployment Checklist

### Before Deployment
- [ ] Version script is executable (`chmod +x scripts/version.sh`)
- [ ] Railway configuration includes version.sh in watchPatterns
- [ ] nixpacks.toml includes version script in build phase
- [ ] Backend config.py properly loads version.json
- [ ] Admin UI server.js fetches version from backend

### After Deployment
- [ ] `/api/version` returns current version information
- [ ] Admin UI `/version` endpoint works
- [ ] Version info visible in admin UI interface
- [ ] Railway environment variables are captured
- [ ] GitHub release created successfully (if main branch)

### Validation Commands
```bash
# Check backend version
curl https://your-app.up.railway.app/api/version

# Check admin UI version  
curl https://your-admin.up.railway.app/version

# Verify git commit matches deployment
git log --oneline -1
```

## Security Considerations

### Public Endpoints
- Version endpoints are intentionally public for monitoring
- No sensitive information exposed (API keys, secrets, etc.)
- Git commit hashes are safe to expose for traceability

### Information Disclosure
- Environment names are exposed (development/staging/production)
- Service IDs and deployment IDs are visible
- Consider if this information should be restricted in production

### Monitoring Integration
- Version endpoints can be used for health checks
- Deployment tracking and rollback decisions
- Automated monitoring alerts based on version changes

---

This versioning system provides complete transparency into deployment status while maintaining security and enabling effective operations monitoring.
