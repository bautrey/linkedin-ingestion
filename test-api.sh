#!/bin/bash

# LinkedIn Ingestion API Test Script
# Quick validation of all endpoints

API_KEY="li_HieZz-IjBp0uE7d-rZkRE0qyy12r5_ZJS_FR4jMvv0I"
BASE_URL="https://smooth-mailbox-production.up.railway.app"

echo "🚀 Testing LinkedIn Ingestion API..."
echo "========================================="

echo -e "\n1. 🏠 Root endpoint:"
curl -s "$BASE_URL/" | head -3
echo ""

echo -e "\n2. ❤️ Health check:"
curl -s "$BASE_URL/api/v1/health" | jq '.status, .database.status' 2>/dev/null || echo "Health check completed"

echo -e "\n3. 📋 Profiles list (first profile):"
curl -s -H "x-api-key: $API_KEY" "$BASE_URL/api/v1/profiles?limit=1" | jq '.data[0].name // "No profiles found"' 2>/dev/null || echo "Profiles endpoint tested"

echo -e "\n4. 🔍 LinkedIn URL search:"
LINKEDIN_URL="https://www.linkedin.com/in/jessicacriscione/"
curl -s -H "x-api-key: $API_KEY" "$BASE_URL/api/v1/profiles?linkedin_url=$LINKEDIN_URL" | jq '.data[0].name // "Profile not found"' 2>/dev/null || echo "LinkedIn URL search tested"

echo -e "\n5. 🔒 Security test (should return 403):"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/profiles")
if [ "$HTTP_CODE" = "403" ]; then
    echo "✅ Security working (403 without API key)"
else
    echo "❌ Security issue (got $HTTP_CODE instead of 403)"
fi

echo -e "\n========================================="
echo "🎉 API tests complete!"
echo "Base URL: $BASE_URL"
echo "API Key: ${API_KEY:0:10}..."
