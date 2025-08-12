"""
Application configuration using Pydantic Settings
"""

from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # Application
    VERSION: str = "2.0.0-cassidy-integration"
    ENVIRONMENT: str = Field(default="development", description="Environment: development, staging, production")
    DEBUG: bool = Field(default=True, description="Enable debug mode")
    
    # API Configuration  
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins"
    )
    API_V1_STR: str = "/api/v1"
    
    # Cassidy AI Configuration
    CASSIDY_PROFILE_WORKFLOW_URL: str = Field(
        default="https://app.cassidyai.com/api/webhook/workflows/cmbv9eaaz00139pa7krnjmoa0?results=true",
        description="Cassidy workflow URL for LinkedIn profile scraping"
    )
    CASSIDY_COMPANY_WORKFLOW_URL: str = Field(
        default="https://app.cassidyai.com/api/webhook/workflows/cmckultwk008bknkgisuk5fef?results=true", 
        description="Cassidy workflow URL for company profile scraping"
    )
    CASSIDY_TIMEOUT: int = Field(default=300, description="Cassidy API timeout in seconds")
    CASSIDY_MAX_RETRIES: int = Field(default=3, description="Maximum retry attempts for Cassidy API")
    CASSIDY_BACKOFF_FACTOR: float = Field(default=2.0, description="Exponential backoff factor")
    
    # Database Configuration
    SUPABASE_URL: Optional[str] = Field(default=None, description="Supabase project URL")
    SUPABASE_ANON_KEY: Optional[str] = Field(default=None, description="Supabase anonymous key")
    SUPABASE_SERVICE_KEY: Optional[str] = Field(default=None, description="Supabase service role key")
    DATABASE_URL: Optional[str] = Field(default=None, description="Direct database connection URL")
    
    # Vector Configuration
    VECTOR_DIMENSION: int = Field(default=1536, description="Vector embedding dimension")
    SIMILARITY_THRESHOLD: float = Field(default=0.8, description="Vector similarity threshold")
    
    # OpenAI Configuration
    OPENAI_API_KEY: Optional[str] = Field(default=None, description="OpenAI API key for LLM scoring")
    OPENAI_DEFAULT_MODEL: str = Field(default="gpt-3.5-turbo", description="Default OpenAI model for scoring")
    OPENAI_MAX_TOKENS: int = Field(default=2000, description="Maximum tokens for OpenAI responses")
    OPENAI_TEMPERATURE: float = Field(default=0.1, description="Temperature for OpenAI requests")
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, description="API rate limit per minute")
    CASSIDY_RATE_LIMIT: int = Field(default=10, description="Cassidy API calls per minute")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FORMAT: str = Field(default="json", description="Log format: json or plain")
    
    # Security
    API_KEY: str = Field(default="li_HieZz-IjBp0uE7d-rZkRE0qyy12r5_ZJS_FR4jMvv0I", description="API key for authentication")
    
    # Feature Flags
    ENABLE_COMPANY_INGESTION: bool = Field(default=True, description="Enable automatic company data ingestion")
    ENABLE_VECTOR_SEARCH: bool = Field(default=True, description="Enable vector similarity search")
    ENABLE_ASYNC_PROCESSING: bool = Field(default=True, description="Enable async profile processing")

    @property
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.ENVIRONMENT == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.ENVIRONMENT == "production"


# Global settings instance
settings = Settings()
