#!/bin/bash

# Complete LinkedIn Ingestion System Health Check
# Runs both backend production workflow tests and frontend E2E tests

set -e

echo "🔍 LinkedIn Ingestion System Health Check"
echo "========================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if we're in the right directory
if [ ! -f "requirements.txt" ] || [ ! -d "admin-ui" ]; then
    print_error "Please run this script from the linkedin-ingestion project root directory"
    exit 1
fi

# 1. Backend Production Workflow Tests
print_status "Running Backend Production Workflow Tests..."
echo ""

if pytest tests/production_workflows/ -v --tb=short; then
    print_success "Backend production workflow tests passed!"
    BACKEND_STATUS="PASS"
else
    print_error "Backend production workflow tests failed!"
    BACKEND_STATUS="FAIL"
fi

echo ""

# 2. Frontend E2E Tests
print_status "Running Frontend E2E Tests..."
echo ""

cd admin-ui

if npm run test:e2e -- --reporter=line; then
    print_success "Frontend E2E tests passed!"
    FRONTEND_STATUS="PASS"
else
    print_error "Frontend E2E tests failed!"
    FRONTEND_STATUS="FAIL"
fi

cd ..

# 3. Summary
echo ""
echo "========================================"
print_status "System Health Check Summary"
echo "========================================"

if [ "$BACKEND_STATUS" = "PASS" ]; then
    print_success "Backend Production Workflows: HEALTHY"
    echo "  - Profile creation (2-3 min workflows) ✅"
    echo "  - Scoring job completion (OpenAI integration) ✅"  
    echo "  - System health & performance benchmarks ✅"
else
    print_error "Backend Production Workflows: UNHEALTHY"
fi

echo ""

if [ "$FRONTEND_STATUS" = "PASS" ]; then
    print_success "Frontend Admin UI: HEALTHY"
    echo "  - Homepage loading & basic functionality ✅"
    echo "  - Profile management interface ✅"
    echo "  - API connectivity & network stability ✅"
    echo "  - Responsive design & JavaScript health ✅"
else
    print_error "Frontend Admin UI: UNHEALTHY"  
fi

echo ""

# Overall status
if [ "$BACKEND_STATUS" = "PASS" ] && [ "$FRONTEND_STATUS" = "PASS" ]; then
    print_success "🎉 OVERALL SYSTEM STATUS: HEALTHY"
    echo ""
    echo "Your LinkedIn Ingestion system is working properly:"
    echo "• Backend APIs are responding and can handle real workflows"
    echo "• Frontend is accessible and functional"
    echo "• End-to-end user workflows are validated"
    echo ""
    exit 0
else
    print_error "🚨 OVERALL SYSTEM STATUS: DEGRADED"
    echo ""
    echo "Some components need attention:"
    [ "$BACKEND_STATUS" = "FAIL" ] && echo "• Backend production workflows need fixing"
    [ "$FRONTEND_STATUS" = "FAIL" ] && echo "• Frontend interface needs fixing"
    echo ""
    exit 1
fi
