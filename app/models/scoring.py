"""
V1.85 LLM Scoring Models

Pydantic models for scoring job management, requests, and responses.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, Optional, List
import uuid

from pydantic import BaseModel, Field, field_validator, ConfigDict


class JobStatus(str, Enum):
    """Scoring job status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ScoringJob(BaseModel):
    """
    Database model for scoring jobs
    
    Represents a scoring job in the database with all metadata and results.
    """
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        use_enum_values=True
    )
    
    id: Optional[str] = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique job identifier"
    )
    profile_id: str = Field(
        ...,
        description="UUID of the LinkedIn profile to score"
    )
    status: JobStatus = Field(
        default=JobStatus.PENDING,
        description="Current job status"
    )
    prompt: str = Field(
        ...,
        min_length=1,
        description="LLM evaluation prompt"
    )
    model_name: str = Field(
        default="gpt-3.5-turbo",
        description="OpenAI model used for scoring"
    )
    
    # LLM Response Data
    llm_response: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Raw LLM response data"
    )
    parsed_score: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Parsed scoring results"
    )
    
    # Error Handling
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if job failed"
    )
    retry_count: int = Field(
        default=0,
        ge=0,
        le=10,
        description="Number of retry attempts"
    )
    
    # Timestamps
    created_at: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Job creation timestamp"
    )
    started_at: Optional[datetime] = Field(
        default=None,
        description="Job processing start timestamp"
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="Job completion timestamp"
    )
    updated_at: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Last update timestamp"
    )
    
    @field_validator('prompt')
    @classmethod
    def validate_prompt(cls, v: str) -> str:
        """Ensure prompt is not empty or whitespace only"""
        if not v or not v.strip():
            raise ValueError("Prompt cannot be empty")
        return v.strip()
    
    @field_validator('model_name')
    @classmethod
    def validate_model_name(cls, v: str) -> str:
        """Validate OpenAI model name"""
        valid_models = {
            'gpt-3.5-turbo',
            'gpt-3.5-turbo-16k', 
            'gpt-4',
            'gpt-4-turbo',
            'gpt-4o',
            'gpt-4o-mini'
        }
        if v not in valid_models:
            # Allow model name but log warning for unknown models
            # This provides flexibility for new models
            pass
        return v


class ScoringRequest(BaseModel):
    """
    API request model for creating scoring jobs
    
    Represents the data sent when requesting a new scoring evaluation.
    """
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    prompt: str = Field(
        ...,
        min_length=1,
        description="Complete evaluation prompt with instructions and response format"
    )
    model: str = Field(
        default="gpt-3.5-turbo",
        description="OpenAI model to use for evaluation"
    )
    max_tokens: int = Field(
        default=2000,
        ge=100,
        le=4000,
        description="Maximum tokens in LLM response"
    )
    temperature: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="LLM creativity setting (0=deterministic, 1=creative)"
    )
    
    @field_validator('prompt')
    @classmethod
    def validate_prompt(cls, v: str) -> str:
        """Ensure prompt is not empty"""
        if not v or not v.strip():
            raise ValueError("Prompt cannot be empty")
        return v.strip()


class ScoringResultData(BaseModel):
    """Scoring result data for completed jobs"""
    model_config = ConfigDict(validate_assignment=True)
    
    llm_response: Dict[str, Any] = Field(
        ...,
        description="Raw LLM response object"
    )
    parsed_score: Dict[str, Any] = Field(
        ...,
        description="Structured scoring results"
    )
    model_used: str = Field(
        ...,
        description="OpenAI model that was used"
    )
    tokens_used: int = Field(
        ...,
        ge=0,
        description="Number of tokens consumed"
    )


class ScoringErrorData(BaseModel):
    """Scoring error data for failed jobs"""
    model_config = ConfigDict(validate_assignment=True)
    
    code: str = Field(
        ...,
        description="Error classification code"
    )
    message: str = Field(
        ...,
        description="Human-readable error description"
    )
    retryable: bool = Field(
        ...,
        description="Whether the job can be retried"
    )


class ScoringResponse(BaseModel):
    """
    API response model for scoring job status
    
    Represents the response data when checking job status or results.
    """
    model_config = ConfigDict(
        validate_assignment=True,
        use_enum_values=True,
        exclude_none=True
    )
    
    job_id: str = Field(
        ...,
        description="Unique job identifier"
    )
    status: JobStatus = Field(
        ...,
        description="Current job status"
    )
    profile_id: str = Field(
        ...,
        description="Profile ID being scored"
    )
    
    # Result data (present when completed)
    result: Optional[ScoringResultData] = Field(
        default=None,
        description="Scoring results (only present when status is completed)"
    )
    
    # Error data (present when failed)
    error: Optional[ScoringErrorData] = Field(
        default=None,
        description="Error information (only present when status is failed)"
    )
    
    # Timestamps
    created_at: datetime = Field(
        ...,
        description="Job creation timestamp"
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        description="Last update timestamp"
    )
    started_at: Optional[datetime] = Field(
        default=None,
        description="Processing start timestamp"
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="Completion timestamp (only present when completed)"
    )
    failed_at: Optional[datetime] = Field(
        default=None,
        description="Failure timestamp (only present when failed)"
    )
    
    # Note: Field validation removed to allow flexible response construction
    # The controller logic ensures correct fields are populated based on status


class JobRetryRequest(BaseModel):
    """Request model for retrying failed jobs"""
    model_config = ConfigDict(validate_assignment=True)
    
    # Optional new parameters for retry
    model: Optional[str] = Field(
        default=None,
        description="Override model for retry (optional)"
    )
    max_tokens: Optional[int] = Field(
        default=None,
        ge=100,
        le=4000,
        description="Override max tokens for retry (optional)"
    )


# Export commonly used models
__all__ = [
    'JobStatus',
    'ScoringJob', 
    'ScoringRequest',
    'ScoringResponse',
    'ScoringResultData',
    'ScoringErrorData',
    'JobRetryRequest'
]
