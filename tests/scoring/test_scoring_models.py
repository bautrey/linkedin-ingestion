"""
Tests for V1.8 scoring engine data models
Tests Pydantic models for scoring requests/responses and database configuration
"""

import pytest
from decimal import Decimal
from typing import Dict, Any, List
from pydantic import ValidationError

from app.scoring.models import (
    ScoringRequest,
    ScoringResponse,
    CategoryScore,
    ScoringThreshold,
    ScoringAlgorithm,
    ProfileScore
)


class TestScoringModels:
    """Test suite for scoring engine data models"""
    
    def test_scoring_request_valid(self):
        """Test valid scoring request model"""
        request = ScoringRequest(
            profile_id="test-profile-123",
            role="CTO"
        )
        
        assert request.profile_id == "test-profile-123"
        assert request.role == "CTO"
    
    def test_scoring_request_invalid_role(self):
        """Test scoring request with invalid role"""
        with pytest.raises(ValidationError) as exc_info:
            ScoringRequest(
                profile_id="test-profile-123",
                role="INVALID_ROLE"
            )
        
        error = exc_info.value.errors()[0]
        assert "role" in error["loc"]
        assert "Input should be 'CTO', 'CIO' or 'CISO'" in error["msg"]
    
    def test_category_score_model(self):
        """Test category score model validation"""
        category_score = CategoryScore(
            category="technical_leadership",
            score=0.85,
            weight=1.0,
            details="Strong technical leadership experience"
        )
        
        assert category_score.category == "technical_leadership"
        assert category_score.score == 0.85
        assert category_score.weight == 1.0
        assert category_score.details == "Strong technical leadership experience"
    
    def test_category_score_invalid_range(self):
        """Test category score with invalid score range"""
        with pytest.raises(ValidationError) as exc_info:
            CategoryScore(
                category="technical_leadership",
                score=1.5,  # Invalid: > 1.0
                weight=1.0
            )
        
        error = exc_info.value.errors()[0]
        assert "score" in error["loc"]
        assert "less than or equal to 1" in error["msg"]
    
    def test_scoring_response_model(self):
        """Test complete scoring response model"""
        category_scores = [
            CategoryScore(
                category="technical_leadership",
                score=0.85,
                weight=1.0,
                details="Strong CTO experience"
            ),
            CategoryScore(
                category="industry_experience",
                score=0.75,
                weight=1.0,
                details="Good industry knowledge"
            )
        ]
        
        response = ScoringResponse(
            profile_id="test-profile-123",
            role="CTO",
            overall_score=0.80,
            category_scores=category_scores,
            threshold_level="good",
            summary="Good fit for CTO role with strong technical leadership",
            recommendations=["Consider for senior technical roles"],
            alternative_roles=["VP Engineering", "Head of Engineering"],
            algorithm_version=1,
            scored_at="2025-08-01T13:00:00Z"
        )
        
        assert response.profile_id == "test-profile-123"
        assert response.role == "CTO"
        assert response.overall_score == 0.80
        assert len(response.category_scores) == 2
        assert response.threshold_level == "good"
        assert "technical leadership" in response.summary
        assert len(response.recommendations) == 1
        assert len(response.alternative_roles) == 2
    
    def test_scoring_threshold_model(self):
        """Test scoring threshold model"""
        threshold = ScoringThreshold(
            role="CTO",
            threshold_type="excellent",
            min_score=0.85,
            max_score=1.00
        )
        
        assert threshold.role == "CTO"
        assert threshold.threshold_type == "excellent"
        assert threshold.min_score == 0.85
        assert threshold.max_score == 1.00
    
    def test_scoring_algorithm_model(self):
        """Test scoring algorithm model"""
        algorithm_config = {
            "keywords": ["CTO", "Chief Technology Officer"],
            "experience_weight": 0.4,
            "title_weight": 0.3,
            "company_weight": 0.3
        }
        
        algorithm = ScoringAlgorithm(
            role="CTO",
            category="technical_leadership",
            algorithm_config=algorithm_config,
            version=1
        )
        
        assert algorithm.role == "CTO"
        assert algorithm.category == "technical_leadership"
        assert algorithm.algorithm_config == algorithm_config
        assert algorithm.version == 1
    
    def test_profile_score_model(self):
        """Test profile score storage model"""
        category_scores_data = {
            "technical_leadership": 0.85,
            "industry_experience": 0.75,
            "company_scale": 0.80
        }
        
        profile_score = ProfileScore(
            profile_id="test-profile-123",
            role="CTO",
            overall_score=0.80,
            category_scores=category_scores_data,
            summary="Good CTO fit",
            recommendations=["Technical leadership role"],
            alternative_roles=["VP Engineering"],
            algorithm_version=1
        )
        
        assert profile_score.profile_id == "test-profile-123"
        assert profile_score.role == "CTO"
        assert profile_score.overall_score == 0.80
        assert profile_score.category_scores["technical_leadership"] == 0.85
        assert profile_score.summary == "Good CTO fit"
        assert len(profile_score.recommendations) == 1
        assert len(profile_score.alternative_roles) == 1
    
    def test_model_serialization(self):
        """Test Pydantic V2 model serialization"""
        request = ScoringRequest(
            profile_id="test-profile-123",
            role="CTO"
        )
        
        # Test model_dump (Pydantic V2)
        data = request.model_dump()
        assert data["profile_id"] == "test-profile-123"
        assert data["role"] == "CTO"
        
        # Test JSON serialization
        json_str = request.model_dump_json()
        assert "test-profile-123" in json_str
        assert "CTO" in json_str
    
    def test_deterministic_results(self):
        """Test that same inputs produce identical model outputs"""
        request1 = ScoringRequest(profile_id="test-123", role="CTO")
        request2 = ScoringRequest(profile_id="test-123", role="CTO")
        
        assert request1.model_dump() == request2.model_dump()
        assert request1 == request2
