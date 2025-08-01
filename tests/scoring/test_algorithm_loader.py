"""
Tests for scoring algorithm and threshold loading functionality.

Following TDD approach - tests first before implementation.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.scoring.algorithm_loader import (
    AlgorithmLoader,
    ScoringConfigNotFoundError,
    ScoringConfigCache
)
from app.scoring.models import ScoringAlgorithm, ScoringThreshold


class TestAlgorithmLoader:
    """Test suite for AlgorithmLoader class."""
    
    @pytest.fixture
    def mock_supabase_client(self):
        """Mock Supabase client for testing."""
        # Supabase client.table() is synchronous, only execute() is async
        return MagicMock()
    
    @pytest.fixture
    def algorithm_loader(self, mock_supabase_client):
        """Create AlgorithmLoader instance with mocked dependencies."""
        return AlgorithmLoader(supabase_client=mock_supabase_client)
    
    @pytest.mark.asyncio
    async def test_load_algorithms_for_role_success(self, algorithm_loader, mock_supabase_client):
        """Test successful loading of algorithms for a specific role."""
        # Mock Supabase table response
        mock_result = MagicMock()
        mock_result.data = [
            {
                "role": "CTO",
                "category": "technical_leadership",
                "algorithm_config": {"keywords": ["CTO", "VP Engineering"], "weight": 1.0},
                "version": 1
            },
            {
                "role": "CTO",
                "category": "industry_experience",
                "algorithm_config": {"tech_keywords": ["software", "technology"], "weight": 0.8},
                "version": 1
            }
        ]
        
        # Mock the Supabase table chain - table() is sync, but execute() is async
        mock_table = MagicMock()
        mock_select = MagicMock()
        mock_eq1 = MagicMock()
        mock_eq2 = MagicMock()
        mock_order = MagicMock()
        
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq1
        mock_eq1.eq.return_value = mock_eq2
        mock_eq2.order.return_value = mock_order
        mock_order.execute = AsyncMock(return_value=mock_result)
        
        mock_supabase_client.table.return_value = mock_table
        
        algorithms = await algorithm_loader.load_algorithms_for_role("CTO")
        
        assert len(algorithms) == 2
        assert algorithms[0].role == "CTO"
        assert algorithms[0].category == "technical_leadership"
        assert algorithms[1].category == "industry_experience"
    
    @pytest.mark.asyncio
    async def test_load_algorithms_for_invalid_role(self, algorithm_loader, mock_supabase_client):
        """Test error handling when role has no algorithms configured."""
        # Mock empty response
        mock_result = MagicMock()
        mock_result.data = []
        
        # Mock the Supabase table chain
        mock_table = MagicMock()
        mock_select = MagicMock()
        mock_eq1 = MagicMock()
        mock_eq2 = MagicMock()
        mock_order = MagicMock()
        
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq1
        mock_eq1.eq.return_value = mock_eq2
        mock_eq2.order.return_value = mock_order
        mock_order.execute = AsyncMock(return_value=mock_result)
        
        mock_supabase_client.table.return_value = mock_table
        
        with pytest.raises(ScoringConfigNotFoundError) as exc_info:
            await algorithm_loader.load_algorithms_for_role("INVALID_ROLE")
        
        assert "No algorithms found for role: INVALID_ROLE" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_load_thresholds_for_role_success(self, algorithm_loader, mock_supabase_client):
        """Test successful loading of thresholds for a specific role."""
        # Mock Supabase table response
        mock_result = MagicMock()
        mock_result.data = [
            {
                "role": "CTO",
                "threshold_type": "excellent",
                "min_score": 0.85,
                "max_score": 1.00
            },
            {
                "role": "CTO",
                "threshold_type": "good",
                "min_score": 0.70,
                "max_score": 0.84
            }
        ]
        
        # Mock the Supabase table chain
        mock_table = MagicMock()
        mock_select = MagicMock()
        mock_eq1 = MagicMock()
        mock_eq2 = MagicMock()
        mock_order = MagicMock()
        
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq1
        mock_eq1.eq.return_value = mock_eq2
        mock_eq2.order.return_value = mock_order
        mock_order.execute = AsyncMock(return_value=mock_result)
        mock_supabase_client.table.return_value = mock_table
        
        thresholds = await algorithm_loader.load_thresholds_for_role("CTO")
        
        assert len(thresholds) == 2
        assert thresholds[0].role == "CTO"
        assert thresholds[0].threshold_type == "excellent"
        assert thresholds[1].threshold_type == "good"
    
    @pytest.mark.asyncio
    async def test_load_thresholds_for_invalid_role(self, algorithm_loader, mock_supabase_client):
        """Test error handling when role has no thresholds configured."""
        # Mock empty response
        mock_result = MagicMock()
        mock_result.data = []
        
        # Mock the Supabase table chain
        mock_table = MagicMock()
        mock_select = MagicMock()
        mock_eq1 = MagicMock()
        mock_eq2 = MagicMock()
        mock_order = MagicMock()
        
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq1
        mock_eq1.eq.return_value = mock_eq2
        mock_eq2.order.return_value = mock_order
        mock_order.execute = AsyncMock(return_value=mock_result)
        
        mock_supabase_client.table.return_value = mock_table
        
        with pytest.raises(ScoringConfigNotFoundError) as exc_info:
            await algorithm_loader.load_thresholds_for_role("INVALID_ROLE")
        
        assert "No thresholds found for role: INVALID_ROLE" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_load_scoring_categories_success(self, algorithm_loader, mock_supabase_client):
        """Test successful loading of scoring categories."""
        # Mock Supabase table response
        mock_result = MagicMock()
        mock_result.data = [
            {
                "name": "technical_leadership",
                "description": "Technical leadership experience",
                "weight": 1.0,
                "is_active": True
            },
            {
                "name": "industry_experience",
                "description": "Industry domain experience", 
                "weight": 0.9,
                "is_active": True
            }
        ]
        
        # Mock the Supabase table chain (categories has one less eq() call)
        mock_table = MagicMock()
        mock_select = MagicMock()
        mock_eq = MagicMock()
        mock_order = MagicMock()
        
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.order.return_value = mock_order
        mock_order.execute = AsyncMock(return_value=mock_result)
        
        mock_supabase_client.table.return_value = mock_table
        
        categories = await algorithm_loader.load_scoring_categories()
        
        assert len(categories) == 2
        assert categories[0]["name"] == "technical_leadership"
        assert categories[1]["name"] == "industry_experience"
        assert categories[0]["weight"] == 1.0
    
    @pytest.mark.asyncio
    async def test_database_connection_error(self, algorithm_loader, mock_supabase_client):
        """Test handling of database connection errors."""
        mock_supabase_client.table.side_effect = Exception("Database connection failed")
        
        with pytest.raises(Exception) as exc_info:
            await algorithm_loader.load_algorithms_for_role("CTO")
        
        assert "Database connection failed" in str(exc_info.value)


class TestScoringConfigCache:
    """Test suite for ScoringConfigCache class."""
    
    @pytest.fixture
    def cache(self):
        """Create ScoringConfigCache instance."""
        return ScoringConfigCache()
    
    def test_cache_algorithms_and_retrieve(self, cache):
        """Test caching and retrieving algorithms."""
        test_algorithms = [
            ScoringAlgorithm(
                role="CTO",
                category="technical_leadership",
                algorithm_config={"weight": 1.0},
                version=1
            )
        ]
        
        # Cache algorithms
        cache.cache_algorithms("CTO", test_algorithms)
        
        # Retrieve from cache
        cached_algorithms = cache.get_algorithms("CTO")
        
        assert cached_algorithms is not None
        assert len(cached_algorithms) == 1
        assert cached_algorithms[0].role == "CTO"
    
    def test_cache_thresholds_and_retrieve(self, cache):
        """Test caching and retrieving thresholds."""
        test_thresholds = [
            ScoringThreshold(
                role="CTO",
                threshold_type="excellent",
                min_score=0.85,
                max_score=1.00
            )
        ]
        
        # Cache thresholds
        cache.cache_thresholds("CTO", test_thresholds)
        
        # Retrieve from cache
        cached_thresholds = cache.get_thresholds("CTO")
        
        assert cached_thresholds is not None
        assert len(cached_thresholds) == 1
        assert cached_thresholds[0].role == "CTO"
    
    def test_cache_miss_returns_none(self, cache):
        """Test that cache miss returns None."""
        assert cache.get_algorithms("NONEXISTENT_ROLE") is None
        assert cache.get_thresholds("NONEXISTENT_ROLE") is None
    
    def test_cache_invalidation(self, cache):
        """Test cache invalidation functionality."""
        test_algorithms = [
            ScoringAlgorithm(
                role="CTO",
                category="test",
                algorithm_config={"weight": 1.0},
                version=1
            )
        ]
        
        # Cache and verify
        cache.cache_algorithms("CTO", test_algorithms)
        assert cache.get_algorithms("CTO") is not None
        
        # Invalidate and verify
        cache.invalidate("CTO")
        assert cache.get_algorithms("CTO") is None
        assert cache.get_thresholds("CTO") is None
    
    def test_cache_ttl_expiration(self, cache):
        """Test cache TTL expiration (if implemented)."""
        # This test may need to be adjusted based on actual TTL implementation
        test_algorithms = [
            ScoringAlgorithm(
                role="CTO",
                category="test",
                algorithm_config={"weight": 1.0},
                version=1
            )
        ]
        
        cache.cache_algorithms("CTO", test_algorithms)
        cached = cache.get_algorithms("CTO")
        
        assert cached is not None
        # TTL testing would require time manipulation or shorter TTL for testing


class TestIntegrationAlgorithmLoader:
    """Integration tests for AlgorithmLoader with real-like scenarios."""
    
    @pytest.mark.asyncio
    async def test_load_complete_role_configuration(self):
        """Test loading complete configuration for a role."""
        # This would be an integration test that requires actual database
        # For now, we'll mark it as a placeholder for future implementation
        pytest.skip("Integration test - requires actual database connection")
    
    @pytest.mark.asyncio
    async def test_caching_integration(self):
        """Test that caching works correctly in real scenarios."""
        # Integration test placeholder
        pytest.skip("Integration test - requires actual database connection")
