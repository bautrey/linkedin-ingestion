#!/bin/bash

# LinkedIn Ingestion Test Runners
# 
# This script provides different test execution modes for development and CI/CD.
# Use these commands to run tests in different environments and configurations.

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Ensure virtual environment is activated
activate_venv() {
    if [[ "$VIRTUAL_ENV" == "" ]]; then
        if [[ -f "venv/bin/activate" ]]; then
            print_status "Activating virtual environment..."
            source venv/bin/activate
        else
            print_error "Virtual environment not found. Please create one with 'python -m venv venv'"
            exit 1
        fi
    fi
}

# Install test dependencies
install_test_deps() {
    print_status "Installing/upgrading test dependencies..."
    pip install -q --upgrade pytest pytest-asyncio pytest-mock pytest-timeout httpx
}

# Unit Tests - Fast, isolated, no external dependencies
run_unit_tests() {
    print_status "Running unit tests (fast, isolated)..."
    python -m pytest app/tests/ \
        -m "unit and not slow and not external" \
        -v --tb=short \
        --durations=5 \
        --color=yes
    
    local exit_code=$?
    if [[ $exit_code -eq 0 ]]; then
        print_success "Unit tests completed successfully"
    else
        print_error "Unit tests failed"
    fi
    return $exit_code
}

# Fast Tests - Quick feedback during development
run_fast_tests() {
    print_status "Running fast tests (< 5 seconds each)..."
    FAST_TESTS_ONLY=1 python -m pytest app/tests/ \
        -m "not slow and not external and not production" \
        -v --tb=short \
        --durations=3 \
        --color=yes
    
    local exit_code=$?
    if [[ $exit_code -eq 0 ]]; then
        print_success "Fast tests completed successfully"
    else
        print_error "Fast tests failed"
    fi
    return $exit_code
}

# Integration Tests - May use database or mocked external services
run_integration_tests() {
    print_status "Running integration tests (with mocked external services)..."
    python -m pytest tests/ \
        -m "integration and not production and not external" \
        -v --tb=short \
        --durations=10 \
        --color=yes
    
    local exit_code=$?
    if [[ $exit_code -eq 0 ]]; then
        print_success "Integration tests completed successfully"
    else
        print_error "Integration tests failed"
    fi
    return $exit_code
}

# All Non-Production Tests
run_all_safe_tests() {
    print_status "Running all safe tests (unit + integration, no production dependencies)..."
    python -m pytest app/tests/ tests/ \
        -m "not production and not external" \
        -v --tb=short \
        --durations=10 \
        --color=yes
    
    local exit_code=$?
    if [[ $exit_code -eq 0 ]]; then
        print_success "All safe tests completed successfully"
    else
        print_error "Some safe tests failed"
    fi
    return $exit_code
}

# Production Tests - Requires live services (use sparingly)
run_production_tests() {
    print_warning "Running production tests (requires live services)..."
    print_warning "These tests may take 5+ minutes and require network access..."
    
    RUN_PRODUCTION_TESTS=1 RUN_EXTERNAL_TESTS=1 python -m pytest tests/production_workflows/ \
        -m "production" \
        -v --tb=short \
        --timeout=300 \
        --durations=0 \
        --color=yes
    
    local exit_code=$?
    if [[ $exit_code -eq 0 ]]; then
        print_success "Production tests completed successfully"
    else
        print_error "Production tests failed"
    fi
    return $exit_code
}

# External API Tests - Tests that make real API calls
run_external_tests() {
    print_warning "Running external API tests (makes real API calls)..."
    
    RUN_EXTERNAL_TESTS=1 python -m pytest \
        -m "external and not production" \
        -v --tb=short \
        --timeout=60 \
        --durations=5 \
        --color=yes
    
    local exit_code=$?
    if [[ $exit_code -eq 0 ]]; then
        print_success "External API tests completed successfully"
    else
        print_error "External API tests failed"
    fi
    return $exit_code
}

# Test specific services or components
run_cassidy_tests() {
    print_status "Running Cassidy adapter tests..."
    python -m pytest \
        -k "cassidy" \
        -v --tb=short \
        --color=yes
}

run_scoring_tests() {
    print_status "Running scoring system tests..."
    python -m pytest \
        -m "scoring" \
        -v --tb=short \
        --color=yes
}

run_database_tests() {
    print_status "Running database integration tests..."
    python -m pytest \
        -m "database and not production" \
        -v --tb=short \
        --color=yes
}

# CI/CD Test Runner
run_ci_tests() {
    print_status "Running CI/CD test suite..."
    print_status "Stage 1: Fast unit tests"
    run_unit_tests || return 1
    
    print_status "Stage 2: Integration tests"
    run_integration_tests || return 1
    
    print_success "CI/CD test suite completed successfully"
}

# Test Coverage Analysis
run_coverage_tests() {
    print_status "Running tests with coverage analysis..."
    
    # Install coverage if not present
    pip install -q coverage pytest-cov
    
    python -m pytest app/tests/ \
        --cov=app \
        --cov-report=html \
        --cov-report=term-missing \
        -m "not production and not external" \
        -v
    
    print_success "Coverage report generated in htmlcov/"
}

# Performance/Load Testing
run_performance_tests() {
    print_status "Running performance tests..."
    python -m pytest \
        -k "performance or load or stress" \
        -v --tb=short \
        --durations=0 \
        --color=yes
}

# Help function
show_help() {
    echo "LinkedIn Ingestion Test Runners"
    echo "Usage: $0 [command]"
    echo ""
    echo "Development Commands:"
    echo "  unit              Run unit tests (fast, isolated)"
    echo "  fast              Run fast tests only (< 5 seconds each)"
    echo "  integration       Run integration tests (mocked external services)"
    echo "  all               Run all safe tests (unit + integration)"
    echo ""
    echo "Service-Specific Commands:"
    echo "  cassidy           Run Cassidy adapter tests"
    echo "  scoring           Run scoring system tests"
    echo "  database          Run database integration tests"
    echo ""
    echo "Advanced Commands:"
    echo "  production        Run production tests (requires live services)"
    echo "  external          Run external API tests (makes real API calls)"
    echo "  ci                Run CI/CD test suite"
    echo "  coverage          Run tests with coverage analysis"
    echo "  performance       Run performance/load tests"
    echo ""
    echo "Environment Variables:"
    echo "  RUN_PRODUCTION_TESTS=1    Enable production tests"
    echo "  RUN_EXTERNAL_TESTS=1      Enable external API tests"
    echo "  FAST_TESTS_ONLY=1         Run only fast tests"
    echo ""
    echo "Examples:"
    echo "  $0 unit                   # Quick feedback during development"
    echo "  $0 all                    # Full test suite without external dependencies"
    echo "  $0 ci                     # CI/CD pipeline tests"
    echo "  RUN_PRODUCTION_TESTS=1 $0 production  # Full production validation"
}

# Main execution logic
main() {
    activate_venv
    
    case "${1:-help}" in
        "unit")
            install_test_deps
            run_unit_tests
            ;;
        "fast")
            install_test_deps
            run_fast_tests
            ;;
        "integration")
            install_test_deps
            run_integration_tests
            ;;
        "all")
            install_test_deps
            run_all_safe_tests
            ;;
        "production")
            install_test_deps
            run_production_tests
            ;;
        "external")
            install_test_deps
            run_external_tests
            ;;
        "cassidy")
            install_test_deps
            run_cassidy_tests
            ;;
        "scoring")
            install_test_deps
            run_scoring_tests
            ;;
        "database")
            install_test_deps
            run_database_tests
            ;;
        "ci")
            install_test_deps
            run_ci_tests
            ;;
        "coverage")
            install_test_deps
            run_coverage_tests
            ;;
        "performance")
            install_test_deps
            run_performance_tests
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            print_error "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

# Execute main function
main "$@"
