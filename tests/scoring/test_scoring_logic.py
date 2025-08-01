"""
Test deterministic scoring logic implementation in app/scoring/scoring_logic.py.

Following TDD approach - tests first before implementation.
"""
import pytest
from app.scoring.scoring_logic import ScoringEngine
from unittest.mock import AsyncMock, MagicMock


class TestScoringEngine:
    """Test suite for ScoringEngine class."""

    @pytest.fixture
    def scoring_engine(self):
        """Create a ScoringEngine instance with mock dependencies."""
        # Mock database and loader
        mock_algorithm_loader = AsyncMock()
        return ScoringEngine(algorithm_loader=mock_algorithm_loader)

    @pytest.mark.asyncio
    async def test_score_calculation_deterministic(self, scoring_engine):
        """Test deterministic scoring calculation for CTO role (same input = same output)."""
        profile_data = {
            "profile_id": "1234",
            "role": "CTO",
            "name": "Jane Doe",
            "linkedin_url": "https://www.linkedin.com/in/janedoe",
            "experience": ["VP Engineering at Tech Co.", "Lead Developer at Dev Co."],
            "education": ["MS Computer Science", "BS Software Engineering"],
            "keywords": ["Leadership", "Development"]
        }

        # Mock algorithm and thresholds for demonstration
        mock_algorithms = [
            {
                'category': 'technical_leadership',
                'algorithm_config': {
                    'keywords': ['CTO', 'VP Engineering'],
                    'experience_weight': 0.4,
                    'title_weight': 0.3,
                    'company_weight': 0.3
                }
            }
        ]
        mock_thresholds = [
            {
                'threshold_type': 'excellent',
                'min_score': 0.85,
                'max_score': 1.00
            },
            {
                'threshold_type': 'good',
                'min_score': 0.70,
                'max_score': 0.84
            }
        ]

        scoring_engine.algorithm_loader.load_algorithms_for_role.return_value = mock_algorithms
        scoring_engine.algorithm_loader.load_thresholds_for_role.return_value = mock_thresholds

        score_result_1 = await scoring_engine.calculate_score(profile_data)
        score_result_2 = await scoring_engine.calculate_score(profile_data)

        assert score_result_1 == score_result_2

    @pytest.mark.asyncio
    async def test_score_range(self, scoring_engine):
        """Test that scores fall within the expected range (0.0 to 1.0)."""
        profile_data = {
            "profile_id": "1234",
            "role": "CTO"
        }

        # Mock algorithm and thresholds for demonstration
        mock_algorithms = [
            {
                'category': 'technical_leadership',
                'algorithm_config': {
                    'keywords': ['CTO', 'VP Engineering'],
                    'experience_weight': 0.4,
                    'title_weight': 0.3,
                    'company_weight': 0.3
                }
            }
        ]
        mock_thresholds = [
            {
                'threshold_type': 'excellent',
                'min_score': 0.85,
                'max_score': 1.00
            },
            {
                'threshold_type': 'good',
                'min_score': 0.70,
                'max_score': 0.84
            }
        ]

        scoring_engine.algorithm_loader.load_algorithms_for_role.return_value = mock_algorithms
        scoring_engine.algorithm_loader.load_thresholds_for_role.return_value = mock_thresholds

        score_result = await scoring_engine.calculate_score(profile_data)

        assert 0.0 <= score_result <= 1.0

    @pytest.mark.asyncio
    async def test_cto_specific_scoring_logic(self, scoring_engine):
        """Test CTO-specific scoring logic with realistic profile data."""
        profile_data = {
            "profile_id": "cto-test-123",
            "role": "CTO",
            "name": "Jane Doe CTO",
            "linkedin_url": "https://www.linkedin.com/in/janedoe",
            "experience": [
                "CTO at Tech Innovations Inc",
                "VP Engineering at Software Solutions", 
                "Senior Engineering Manager at DevCorp",
                "Lead Developer at StartupXYZ"
            ],
            "education": [
                "MS Computer Science from Stanford University",
                "BS Software Engineering from MIT"
            ]
        }

        # Mock CTO algorithms with realistic configuration
        mock_algorithms = [
            {
                'category': 'technical_leadership',
                'algorithm_config': {
                    'keywords': ['CTO', 'Chief Technology Officer', 'VP Engineering', 'Head of Engineering'],
                    'experience_weight': 0.4,
                    'title_weight': 0.3,
                    'company_weight': 0.3
                }
            },
            {
                'category': 'industry_experience',
                'algorithm_config': {
                    'tech_keywords': ['software', 'technology', 'engineering', 'development'],
                    'years_weight': 0.6,
                    'relevance_weight': 0.4
                }
            },
            {
                'category': 'education_background',
                'algorithm_config': {
                    'degrees': {'BS': 0.8, 'MS': 1.0, 'PhD': 1.2},
                    'fields': ['Computer Science', 'Engineering', 'Technology']
                }
            }
        ]
        
        mock_thresholds = [
            {
                'threshold_type': 'excellent',
                'min_score': 0.85,
                'max_score': 1.00
            }
        ]

        scoring_engine.algorithm_loader.load_algorithms_for_role.return_value = mock_algorithms
        scoring_engine.algorithm_loader.load_thresholds_for_role.return_value = mock_thresholds

        score_result = await scoring_engine.calculate_score(profile_data)

        # Verify CTO scoring produces reasonable results
        assert 0.5 <= score_result <= 1.0  # Should score well for CTO profile
        assert isinstance(score_result, float)

    @pytest.mark.asyncio
    async def test_non_cto_role_default_scoring(self, scoring_engine):
        """Test that non-CTO roles use default scoring logic."""
        profile_data = {
            "profile_id": "cio-test-123",
            "role": "CIO",
            "name": "John Smith",
            "experience": ["CIO at Enterprise Corp"]
        }

        mock_algorithms = [
            {
                'category': 'technical_leadership',
                'algorithm_config': {
                    'keywords': ['CIO', 'Chief Information Officer'],
                    'experience_weight': 0.4
                }
            }
        ]
        
        mock_thresholds = []

        scoring_engine.algorithm_loader.load_algorithms_for_role.return_value = mock_algorithms
        scoring_engine.algorithm_loader.load_thresholds_for_role.return_value = mock_thresholds

        score_result = await scoring_engine.calculate_score(profile_data)

        # Should use default scoring (0.5) for non-CTO roles
        assert score_result == 0.5

    @pytest.mark.asyncio
    async def test_empty_profile_data_handling(self, scoring_engine):
        """Test handling of empty or minimal profile data."""
        profile_data = {
            "profile_id": "empty-test-123",
            "role": "CTO"
        }

        mock_algorithms = [
            {
                'category': 'technical_leadership',
                'algorithm_config': {
                    'keywords': ['CTO'],
                    'experience_weight': 0.4,
                    'title_weight': 0.3
                }
            }
        ]
        
        mock_thresholds = []

        scoring_engine.algorithm_loader.load_algorithms_for_role.return_value = mock_algorithms
        scoring_engine.algorithm_loader.load_thresholds_for_role.return_value = mock_thresholds

        score_result = await scoring_engine.calculate_score(profile_data)

        # Should handle empty data gracefully
        assert 0.0 <= score_result <= 1.0
        assert isinstance(score_result, float)

