"""
Application configuration using Pydantic Settings
"""

import json
import os
from typing import List, Optional, Dict, Any
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""
    
    model_config = SettingsConfigDict(
        env_file=[".env.production", ".env"],  # Try production first, fallback to .env
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"  # Ignore extra environment variables
    )

    # Application
    VERSION: str = "2.1.0-development+b6f734e"
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
    
    # Stage-Based Model Configuration
    STAGE_2_MODEL: str = Field(default="gpt-3.5-turbo", description="Model for Stage 2 screening (cost-effective)")
    STAGE_3_MODEL: str = Field(default="gpt-4o-mini", description="Model for Stage 3 role compatibility (fast screening)")
    
    # Stage 3 Role Compatibility Template
    ROLE_COMPATIBILITY_TEMPLATE: str = Field(
        default="""
You are an executive recruiter specializing in C-level technology roles. Analyze this LinkedIn profile and determine which executive role (CTO, CIO, CISO) this person is best suited for, if any.

**Role Definitions:**
- **CTO (Chief Technology Officer)**: Technical leadership, engineering teams, software development, technology strategy, product development
- **CIO (Chief Information Officer)**: Enterprise IT operations, business technology alignment, IT strategy, infrastructure management, digital transformation
- **CISO (Chief Information Security Officer)**: Cybersecurity leadership, risk management, compliance, security architecture, incident response

**Evaluation Criteria:**
1. **Experience Match**: Does their background align with the role requirements?
2. **Leadership Level**: Have they led teams/organizations at an appropriate scale?
3. **Technical Depth**: Do they have the right technical background for the role?
4. **Strategic Focus**: Have they made strategic decisions in the relevant domain?

**Instructions:**
- Analyze the profile against ALL THREE roles
- Assign compatibility scores (0.0-1.0) for each role
- Determine if they meet minimum executive standards (0.4+ threshold)
- Return the BEST matching role or "NONE" if no role meets the threshold

**Response Format (JSON only):**
{
  "recommended_role": "CTO|CIO|CISO|NONE",
  "passes_gate": true|false,
  "compatibility_scores": {
    "CTO": 0.0-1.0,
    "CIO": 0.0-1.0,
    "CISO": 0.0-1.0
  },
  "confidence": 0.0-1.0,
  "key_factors": ["list of 2-3 key factors supporting the recommendation"],
  "reasoning": "brief explanation of why this role was selected or why they failed"
}
""",
        description="Template for Stage 3 role compatibility checking"
    )
    
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
    
    # Version information (loaded from version.json if available)
    _version_info: Optional[Dict[str, Any]] = None

    def __init__(self, **data):
        super().__init__(**data)
        self._load_version_info()
    
    def _load_version_info(self) -> None:
        """Load version information from version.json file"""
        version_file = "version.json"
        if os.path.exists(version_file):
            try:
                with open(version_file, 'r') as f:
                    self._version_info = json.load(f)
                # Update VERSION field with the loaded version
                if self._version_info and "version" in self._version_info:
                    self.VERSION = self._version_info["version"]
            except (json.JSONDecodeError, FileNotFoundError, IOError) as e:
                # Fallback to default version if file doesn't exist or is invalid
                self._version_info = None
    
    @property
    def version_info(self) -> Dict[str, Any]:
        """Get comprehensive version information"""
        if self._version_info:
            return self._version_info
        return {
            "version": self.VERSION,
            "base_version": self.VERSION,
            "build_time": "unknown",
            "git": {
                "commit": "unknown",
                "commit_short": "unknown",
                "branch": "unknown",
                "author": "unknown",
                "message": "unknown"
            },
            "deployment": {
                "service_id": "unknown",
                "environment": self.ENVIRONMENT,
                "deployment_id": "unknown",
                "platform": "unknown"
            },
            "app": {
                "name": "linkedin-ingestion",
                "description": "LinkedIn Profile and Company Data Ingestion Service"
            }
        }
    
    @property
    def git_commit(self) -> str:
        """Get git commit hash"""
        return self.version_info.get("git", {}).get("commit", "unknown")
    
    @property
    def git_commit_short(self) -> str:
        """Get short git commit hash"""
        return self.version_info.get("git", {}).get("commit_short", "unknown")
    
    @property
    def git_branch(self) -> str:
        """Get git branch"""
        return self.version_info.get("git", {}).get("branch", "unknown")
    
    @property
    def build_time(self) -> str:
        """Get build timestamp"""
        return self.version_info.get("build_time", "unknown")
    
    @property
    def deployment_environment(self) -> str:
        """Get deployment environment"""
        return self.version_info.get("deployment", {}).get("environment", self.ENVIRONMENT)

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
