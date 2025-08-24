#!/bin/bash

# Railway Logs Environment Setup Script
# Run this to set up your environment variables for the Railway logs system

echo "🚂 Setting up Railway Logs Environment"
echo "═══════════════════════════════════════"

# Set the environment variables
export RAILWAY_TOKEN="5a725b5b-dfae-48ce-98fa-c90b6d7e2714"
export RAILWAY_PROJECT_ID="d586086b-3ecb-404b-ad92-9672d36d1e3f"
export RAILWAY_ENVIRONMENT_ID="cd226704-be4d-469d-8bb9-cb05bdcd1196"
export RAILWAY_SERVICE_ID="7101a8bc-173b-4379-bbba-24ff74b8e9d2"

echo "✅ Railway environment variables set:"
echo "   Project: smooth-mailbox ($RAILWAY_PROJECT_ID)"
echo "   Environment: production ($RAILWAY_ENVIRONMENT_ID)"
echo "   Service: $RAILWAY_SERVICE_ID"
echo ""
echo "🎯 You can now use Railway logs commands:"
echo "   ./safe_logs.sh                           # Default logs"
echo "   ./safe_logs.sh deployment --errors-only  # Only errors"
echo "   ./safe_logs.sh examples errors_last_hour # Error pattern"
echo "   ./safe_logs.sh build --limit 20          # Build logs"
echo ""
echo "💡 To make this permanent, add these to your ~/.zshrc:"
echo "   echo 'export RAILWAY_TOKEN=\"$RAILWAY_TOKEN\"' >> ~/.zshrc"
echo "   echo 'export RAILWAY_PROJECT_ID=\"$RAILWAY_PROJECT_ID\"' >> ~/.zshrc"
echo "   echo 'export RAILWAY_ENVIRONMENT_ID=\"$RAILWAY_ENVIRONMENT_ID\"' >> ~/.zshrc"
echo "   echo 'export RAILWAY_SERVICE_ID=\"$RAILWAY_SERVICE_ID\"' >> ~/.zshrc"
