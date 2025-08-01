"""
Pytest configuration and fixtures
Configures test environment to use local Supabase instance
"""

import os
import pytest
from pydantic_settings import SettingsConfigDict


def pytest_configure(config):
    """Configure pytest to use test environment"""
    # Set environment to use .env.test file
    os.environ["ENVIRONMENT"] = "test"
    
    # Load environment variables from .env.test explicitly
    from dotenv import load_dotenv
    load_dotenv(".env.test", override=True)
    
    # Override Pydantic settings to use test env file
    from app.core.config import Settings
    
    # Create test settings that use .env.test
    test_settings = Settings(
        _env_file=".env.test",
        _env_file_encoding="utf-8"
    )
    
    # Replace the global settings with test settings
    import app.core.config
    app.core.config.settings = test_settings


@pytest.fixture(scope="session")
def test_settings():
    """Provide test settings for the entire test session"""
    from app.core.config import Settings
    return Settings(
        _env_file=".env.test",
        _env_file_encoding="utf-8"
    )
