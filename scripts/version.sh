#!/bin/bash
set -e

echo "🔧 Generating version information..."

# Railway provides these environment variables automatically:
# - RAILWAY_GIT_COMMIT_SHA
# - RAILWAY_GIT_BRANCH  
# - RAILWAY_GIT_AUTHOR
# - RAILWAY_GIT_MESSAGE
# - RAILWAY_SERVICE_ID
# - RAILWAY_ENVIRONMENT_NAME
# - RAILWAY_DEPLOYMENT_ID

# Generate timestamp
BUILD_TIME=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Define clean base version for user-facing display
BASE_VERSION="2.1.0"
APP_NAME="linkedin-ingestion"

# Get git information (Railway provides these, fallback to local git if available)
GIT_COMMIT=${RAILWAY_GIT_COMMIT_SHA:-$(git rev-parse HEAD 2>/dev/null || echo "unknown")}
GIT_COMMIT_SHORT=${GIT_COMMIT:0:8}
GIT_BRANCH=${RAILWAY_GIT_BRANCH:-$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")}
GIT_AUTHOR=${RAILWAY_GIT_AUTHOR:-$(git log -1 --format='%an' 2>/dev/null || echo "unknown")}
GIT_MESSAGE=${RAILWAY_GIT_MESSAGE:-$(git log -1 --format='%s' 2>/dev/null || echo "unknown")}

# Railway deployment information
SERVICE_ID=${RAILWAY_SERVICE_ID:-"local"}
ENVIRONMENT=${RAILWAY_ENVIRONMENT_NAME:-"development"}
DEPLOYMENT_ID=${RAILWAY_DEPLOYMENT_ID:-"local-build"}

# Generate semantic version
if [ "$ENVIRONMENT" = "production" ]; then
    VERSION="$BASE_VERSION+$GIT_COMMIT_SHORT"
else
    VERSION="$BASE_VERSION-$ENVIRONMENT+$GIT_COMMIT_SHORT"
fi

# Generate version.json with comprehensive metadata
cat > version.json << EOF
{
  "version": "$VERSION",
  "base_version": "$BASE_VERSION",
  "build_time": "$BUILD_TIME",
  "git": {
    "commit": "$GIT_COMMIT",
    "commit_short": "$GIT_COMMIT_SHORT",
    "branch": "$GIT_BRANCH",
    "author": "$GIT_AUTHOR",
    "message": "$GIT_MESSAGE"
  },
  "deployment": {
    "service_id": "$SERVICE_ID",
    "environment": "$ENVIRONMENT",
    "deployment_id": "$DEPLOYMENT_ID",
    "platform": "railway"
  },
  "app": {
    "name": "linkedin-ingestion",
    "description": "LinkedIn Profile and Company Data Ingestion Service"
  }
}
EOF

echo "📦 Generated version: $VERSION"
echo "🔍 Git commit: $GIT_COMMIT_SHORT"
echo "🌿 Git branch: $GIT_BRANCH"
echo "⏰ Build time: $BUILD_TIME"
echo "🚂 Environment: $ENVIRONMENT"

# Create a simple version file for quick access
echo "$VERSION" > VERSION

# Update the config.py file with the generated version
if [ -f "app/core/config.py" ]; then
    # Create a backup
    cp app/core/config.py app/core/config.py.bak
    
    # Replace the VERSION line with our generated version
    sed -i.tmp "s/VERSION:.*=.*/VERSION: str = \"$VERSION\"/" app/core/config.py
    rm -f app/core/config.py.tmp
    
    echo "✅ Updated app/core/config.py with version: $VERSION"
fi

# Create version info for admin UI
cat > admin-ui/version.json << EOF
{
  "version": "$VERSION",
  "build_time": "$BUILD_TIME",
  "git_commit": "$GIT_COMMIT_SHORT",
  "git_branch": "$GIT_BRANCH",
  "environment": "$ENVIRONMENT"
}
EOF

echo "✅ Version generation completed successfully!"
