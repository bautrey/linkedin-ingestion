"""
Pytest configuration and fixtures
Configures test environment to use local Supabase instance
"""

import os
import pytest


def pytest_configure(config):
    """Configure pytest to use test environment"""
    # Set environment to use .env.test file
    os.environ["ENVIRONMENT"] = "test"
    
    # Override Pydantic settings to use test env file
    from app.core.config import Settings
    
    # Create test settings that use .env.test
    test_settings = Settings(_env_file=".env.test")
    
    # Replace the global settings with test settings
    import app.core.config
    app.core.config.settings = test_settings


@pytest.fixture(scope="session")
def test_settings():
    """Provide test settings for the entire test session"""
    from app.core.config import Settings
    return Settings(_env_file=".env.test")
