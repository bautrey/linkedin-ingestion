"""
V1.8 Fortium Fit Scoring API Models
Pydantic models for scoring requests, responses, and database configuration
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Literal
from pydantic import BaseModel, Field, field_validator, ConfigDict
from decimal import Decimal


class ScoringRequest(BaseModel):
    """Request model for profile scoring"""
    profile_id: str = Field(..., description="LinkedIn profile ID to score")
    role: Literal["CTO", "CIO", "CISO"] = Field(..., description="Role to score against")
    
    class Config:
        str_strip_whitespace = True


class CategoryScore(BaseModel):
    """Individual category score details"""
    category: str = Field(..., description="Scoring category name")
    score: float = Field(..., ge=0.0, le=1.0, description="Category score (0.0-1.0)")
    weight: float = Field(..., ge=0.0, le=2.0, description="Category weight in overall score")
    details: Optional[str] = Field(None, description="Detailed scoring explanation")
    
    class Config:
        validate_assignment = True


class ScoringResponse(BaseModel):
    """Complete scoring response model"""
    profile_id: str = Field(..., description="Profile ID that was scored")
    role: Literal["CTO", "CIO", "CISO"] = Field(..., description="Role scored against")
    overall_score: float = Field(..., ge=0.0, le=1.0, description="Overall fit score")
    category_scores: List[CategoryScore] = Field(..., description="Individual category scores")
    threshold_level: Literal["excellent", "good", "fair", "poor"] = Field(..., description="Score threshold level")
    summary: str = Field(..., description="Human-readable scoring summary")
    recommendations: List[str] = Field(default_factory=list, description="Actionable recommendations")
    alternative_roles: List[str] = Field(default_factory=list, description="Alternative role suggestions")
    algorithm_version: int = Field(..., description="Algorithm version used")
    scored_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat(), description="Scoring timestamp")
    
    class Config:
        validate_assignment = True


class ScoringThreshold(BaseModel):
    """Scoring threshold configuration from database"""
    role: Literal["CTO", "CIO", "CISO"] = Field(..., description="Role for threshold")
    threshold_type: Literal["excellent", "good", "fair", "poor"] = Field(..., description="Threshold level")
    min_score: float = Field(..., ge=0.0, le=1.0, description="Minimum score for this threshold")
    max_score: float = Field(..., ge=0.0, le=1.0, description="Maximum score for this threshold")
    
    @field_validator('max_score')
    @classmethod
    def max_score_greater_than_min(cls, v, info):
        """Ensure max_score is greater than min_score"""
        if info.data and 'min_score' in info.data and v <= info.data['min_score']:
            raise ValueError('max_score must be greater than min_score')
        return v
    
    model_config = ConfigDict(validate_assignment=True)


class ScoringAlgorithm(BaseModel):
    """Scoring algorithm configuration from database"""
    role: Literal["CTO", "CIO", "CISO"] = Field(..., description="Role for algorithm")
    category: str = Field(..., description="Scoring category")
    algorithm_config: Dict[str, Any] = Field(..., description="Algorithm configuration JSON")
    version: int = Field(..., ge=1, description="Algorithm version")
    
    class Config:
        validate_assignment = True


class ProfileScore(BaseModel):
    """Profile score for database storage"""
    profile_id: str = Field(..., description="Profile ID")
    role: Literal["CTO", "CIO", "CISO"] = Field(..., description="Role scored")
    overall_score: float = Field(..., ge=0.0, le=1.0, description="Overall score")
    category_scores: Dict[str, float] = Field(..., description="Category scores as JSON")
    summary: Optional[str] = Field(None, description="Scoring summary")
    recommendations: Optional[List[str]] = Field(None, description="Recommendations list")
    alternative_roles: Optional[List[str]] = Field(None, description="Alternative roles")
    algorithm_version: int = Field(..., description="Algorithm version used")
    scored_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc), description="Scoring timestamp")
    
    class Config:
        validate_assignment = True


class ScoringConfig(BaseModel):
    """Complete scoring configuration loaded from database"""
    algorithms: Dict[str, ScoringAlgorithm] = Field(..., description="Algorithms by category")
    thresholds: List[ScoringThreshold] = Field(..., description="Score thresholds")
    categories: List[str] = Field(..., description="Available scoring categories")
    
    class Config:
        validate_assignment = True
