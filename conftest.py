"""
Global pytest configuration and fixtures for the LinkedIn ingestion project.

This file provides:
- Test environment configuration
- Common fixtures for database, HTTP clients, and test data
- Test isolation and cleanup mechanisms
- Environment-specific test runners
"""

import pytest
import asyncio
import os
import uuid
import httpx
from typing import Dict, Any, Generator, AsyncGenerator
from unittest.mock import Mock, patch
import logging

# Configure logging for tests
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)


def pytest_configure(config):
    """Configure pytest with custom settings."""
    # Set test environment variable
    os.environ["TESTING"] = "true"
    
    # Disable some verbose logging during tests
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def pytest_collection_modifyitems(config, items):
    """
    Modify test collection to add markers based on test patterns and locations.
    
    This automatically categorizes tests based on their location and naming patterns.
    """
    for item in items:
        # Add unit marker to all tests in app/tests/ by default
        if "app/tests" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
            
        # Add integration marker to tests in tests/ directory
        elif "tests/" in str(item.fspath) and "production_workflows" not in str(item.fspath):
            item.add_marker(pytest.mark.integration)
            
        # Add production marker to production workflow tests
        elif "production_workflows" in str(item.fspath):
            item.add_marker(pytest.mark.production)
            item.add_marker(pytest.mark.external)
            item.add_marker(pytest.mark.slow)
            
        # Mark tests with async patterns
        if asyncio.iscoroutinefunction(item.function):
            item.add_marker(pytest.mark.asyncio)
            
        # Mark tests that likely make external calls
        if any(keyword in item.name.lower() for keyword in ["api", "http", "client", "external"]):
            item.add_marker(pytest.mark.external)
            
        # Mark database tests
        if any(keyword in item.name.lower() for keyword in ["db", "database", "repository", "sql"]):
            item.add_marker(pytest.mark.database)
            
        # Mark slow tests based on patterns
        if any(keyword in item.name.lower() for keyword in ["workflow", "integration", "complete", "full"]):
            item.add_marker(pytest.mark.slow)


def pytest_runtest_setup(item):
    """
    Setup hook to skip tests based on environment and markers.
    
    This provides selective test execution based on environment variables.
    """
    # Skip production tests unless explicitly enabled
    if item.get_closest_marker("production"):
        if not os.getenv("RUN_PRODUCTION_TESTS"):
            pytest.skip("Production tests disabled. Set RUN_PRODUCTION_TESTS=1 to enable.")
            
    # Skip external tests unless explicitly enabled
    if item.get_closest_marker("external"):
        if not os.getenv("RUN_EXTERNAL_TESTS"):
            pytest.skip("External tests disabled. Set RUN_EXTERNAL_TESTS=1 to enable.")
            
    # Skip slow tests in fast mode
    if item.get_closest_marker("slow"):
        if os.getenv("FAST_TESTS_ONLY"):
            pytest.skip("Slow tests disabled in fast mode. Unset FAST_TESTS_ONLY to enable.")


@pytest.fixture(scope="session")
def event_loop():
    """
    Create an event loop for the test session.
    
    This ensures all async tests run in the same event loop.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture
def mock_http_client():
    """
    Provide a mock HTTP client for testing external API interactions.
    
    This prevents actual HTTP calls during unit tests.
    """
    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = Mock()
        mock_client.return_value.__aenter__.return_value = mock_instance
        mock_client.return_value.__aexit__.return_value = None
        yield mock_instance


@pytest.fixture
async def http_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """
    Provide a real HTTP client for integration tests.
    
    This client has proper timeout and cleanup handling.
    """
    timeout = httpx.Timeout(30.0, connect=10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        yield client


@pytest.fixture
def test_data_factory():
    """
    Factory for generating consistent test data.
    
    This provides reusable test data patterns across different test suites.
    """
    class TestDataFactory:
        @staticmethod
        def profile_data(linkedin_url: str = None) -> Dict[str, Any]:
            """Generate test profile data."""
            return {
                "profile_id": f"test-{uuid.uuid4().hex[:8]}",
                "full_name": "Test User",
                "linkedin_url": linkedin_url or f"https://linkedin.com/in/test-{uuid.uuid4().hex[:8]}",
                "headline": "Test Engineer",
                "summary": "Test summary",
                "experiences": [],
                "educations": []
            }
            
        @staticmethod
        def company_data(company_name: str = None) -> Dict[str, Any]:
            """Generate test company data."""
            return {
                "company_name": company_name or f"Test Company {uuid.uuid4().hex[:8]}",
                "company_id": f"test-company-{uuid.uuid4().hex[:8]}",
                "linkedin_url": f"https://linkedin.com/company/test-{uuid.uuid4().hex[:8]}",
                "industries": ["Technology", "Software"],
                "employee_count": 100,
                "year_founded": 2020
            }
            
        @staticmethod
        def template_data(name: str = None) -> Dict[str, Any]:
            """Generate test template data."""
            return {
                "name": name or f"Test Template {uuid.uuid4().hex[:8]}",
                "category": "TEST",
                "prompt_text": "Test prompt for scoring evaluation",
                "description": "Test template description"
            }
    
    return TestDataFactory()


@pytest.fixture
def cleanup_registry():
    """
    Registry for tracking resources that need cleanup after tests.
    
    This ensures proper cleanup of created resources, preventing test pollution.
    """
    registry = {
        "profiles": [],
        "companies": [],
        "templates": [],
        "jobs": []
    }
    
    yield registry
    
    # Cleanup logic would go here - for now just log what would be cleaned
    for resource_type, resources in registry.items():
        if resources:
            print(f"Would clean up {len(resources)} {resource_type}: {resources}")


@pytest.fixture
def production_config():
    """
    Production environment configuration for integration tests.
    
    This provides centralized configuration for production test endpoints.
    """
    return {
        "base_url": "https://smooth-mailbox-production.up.railway.app",
        "api_headers": {"x-api-key": "li_HieZz-IjBp0uE7d-rZkRE0qyy12r5_ZJS_FR4jMvv0I"},
        "timeout": 30.0,
        "max_retries": 3,
        "test_profile_id": "435ccbf7-6c5e-4e2d-bdc3-052a244d7121"
    }


@pytest.fixture
def mock_external_services():
    """
    Mock all external service dependencies for unit tests.
    
    This fixture mocks LinkedIn API, OpenAI API, and other external dependencies.
    """
    mocks = {}
    
    # Mock LinkedIn/Cassidy API
    with patch("app.cassidy.client.CassidyClient") as mock_cassidy:
        mock_cassidy_instance = Mock()
        mock_cassidy.return_value = mock_cassidy_instance
        mocks["cassidy"] = mock_cassidy_instance
        
        # Mock OpenAI API
        with patch("openai.AsyncOpenAI") as mock_openai:
            mock_openai_instance = Mock()
            mock_openai.return_value = mock_openai_instance
            mocks["openai"] = mock_openai_instance
            
            yield mocks


# Test runner helper functions
def run_unit_tests():
    """Run only unit tests (fast, isolated)."""
    import subprocess
    return subprocess.run([
        "python", "-m", "pytest", 
        "app/tests/", 
        "-m", "unit and not slow",
        "-v", "--tb=short"
    ])


def run_integration_tests():
    """Run integration tests (may use mocked external services)."""
    import subprocess
    return subprocess.run([
        "python", "-m", "pytest", 
        "tests/", 
        "-m", "integration and not production",
        "-v", "--tb=short"
    ])


def run_production_tests():
    """Run production tests (requires live services)."""
    import subprocess
    return subprocess.run([
        "python", "-m", "pytest", 
        "tests/production_workflows/", 
        "-m", "production",
        "-v", "--tb=short", 
        "--timeout=300"
    ], env={**os.environ, "RUN_PRODUCTION_TESTS": "1", "RUN_EXTERNAL_TESTS": "1"})


if __name__ == "__main__":
    print("Test configuration loaded successfully.")
    print("Available test runners:")
    print("- run_unit_tests(): Fast, isolated unit tests")
    print("- run_integration_tests(): Integration tests with mocks")
    print("- run_production_tests(): End-to-end production tests")
