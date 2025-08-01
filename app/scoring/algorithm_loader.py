"""
Algorithm loader for scoring configuration.

Loads scoring algorithms, thresholds, and categories from database with caching.
"""
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime, timedelta
from supabase import AsyncClient
from app.scoring.models import ScoringAlgorithm, ScoringThreshold

logger = logging.getLogger(__name__)


class ScoringConfigNotFoundError(Exception):
    """Raised when scoring configuration is not found for a role."""
    pass


class ScoringConfigCache:
    """In-memory cache for scoring configuration with TTL."""
    
    def __init__(self, ttl_minutes: int = 60):
        """Initialize cache with TTL in minutes."""
        self._algorithms_cache: Dict[str, tuple] = {}  # role -> (algorithms, timestamp)
        self._thresholds_cache: Dict[str, tuple] = {}  # role -> (thresholds, timestamp)
        self._categories_cache: Optional[tuple] = None  # (categories, timestamp)
        self.ttl = timedelta(minutes=ttl_minutes)
    
    def _is_expired(self, timestamp: datetime) -> bool:
        """Check if cached item is expired."""
        return datetime.now() - timestamp > self.ttl
    
    def cache_algorithms(self, role: str, algorithms: List[ScoringAlgorithm]) -> None:
        """Cache algorithms for a role."""
        self._algorithms_cache[role] = (algorithms, datetime.now())
        logger.debug(f"Cached {len(algorithms)} algorithms for role: {role}")
    
    def get_algorithms(self, role: str) -> Optional[List[ScoringAlgorithm]]:
        """Get cached algorithms for a role."""
        if role not in self._algorithms_cache:
            return None
        
        algorithms, timestamp = self._algorithms_cache[role]
        if self._is_expired(timestamp):
            del self._algorithms_cache[role]
            logger.debug(f"Expired algorithms cache for role: {role}")
            return None
        
        logger.debug(f"Cache hit for algorithms, role: {role}")
        return algorithms
    
    def cache_thresholds(self, role: str, thresholds: List[ScoringThreshold]) -> None:
        """Cache thresholds for a role."""
        self._thresholds_cache[role] = (thresholds, datetime.now())
        logger.debug(f"Cached {len(thresholds)} thresholds for role: {role}")
    
    def get_thresholds(self, role: str) -> Optional[List[ScoringThreshold]]:
        """Get cached thresholds for a role."""
        if role not in self._thresholds_cache:
            return None
        
        thresholds, timestamp = self._thresholds_cache[role]
        if self._is_expired(timestamp):
            del self._thresholds_cache[role]
            logger.debug(f"Expired thresholds cache for role: {role}")
            return None
        
        logger.debug(f"Cache hit for thresholds, role: {role}")
        return thresholds
    
    def invalidate(self, role: str) -> None:
        """Invalidate cache for a specific role."""
        self._algorithms_cache.pop(role, None)
        self._thresholds_cache.pop(role, None)
        logger.debug(f"Invalidated cache for role: {role}")
    
    def clear_all(self) -> None:
        """Clear all cached data."""
        self._algorithms_cache.clear()
        self._thresholds_cache.clear()
        self._categories_cache = None
        logger.debug("Cleared all cache data")


class AlgorithmLoader:
    """Loads scoring algorithms and configuration from database."""
    
    def __init__(self, supabase_client: AsyncClient, cache: Optional[ScoringConfigCache] = None):
        """Initialize with Supabase client and optional cache."""
        self.supabase_client = supabase_client
        self.cache = cache or ScoringConfigCache()
    
    async def load_algorithms_for_role(self, role: str) -> List[ScoringAlgorithm]:
        """
        Load scoring algorithms for a specific role.
        
        Args:
            role: Target role (CTO, CIO, CISO)
            
        Returns:
            List of ScoringAlgorithm objects
            
        Raises:
            ScoringConfigNotFoundError: If no algorithms found for role
        """
        # Check cache first
        cached_algorithms = self.cache.get_algorithms(role)
        if cached_algorithms is not None:
            return cached_algorithms
        
        logger.info(f"Loading algorithms from database for role: {role}")
        
        try:
            # Query database for algorithms using Supabase
            table = self.supabase_client.table("scoring_algorithms")
            result = await table.select("role, category, algorithm_config, version").eq("role", role).eq("is_active", True).order("category").execute()
            
            if not result.data:
                raise ScoringConfigNotFoundError(f"No algorithms found for role: {role}")
            
            # Convert to ScoringAlgorithm objects
            algorithms = []
            for row in result.data:
                algorithm = ScoringAlgorithm(
                    role=row["role"],
                    category=row["category"],
                    algorithm_config=row["algorithm_config"],
                    version=row["version"]
                )
                algorithms.append(algorithm)
            
            # Cache the results
            self.cache.cache_algorithms(role, algorithms)
            
            logger.info(f"Loaded {len(algorithms)} algorithms for role: {role}")
            return algorithms
            
        except Exception as e:
            logger.error(f"Error loading algorithms for role {role}: {str(e)}")
            raise
    
    async def load_thresholds_for_role(self, role: str) -> List[ScoringThreshold]:
        """
        Load scoring thresholds for a specific role.
        
        Args:
            role: Target role (CTO, CIO, CISO)
            
        Returns:
            List of ScoringThreshold objects
            
        Raises:
            ScoringConfigNotFoundError: If no thresholds found for role
        """
        # Check cache first
        cached_thresholds = self.cache.get_thresholds(role)
        if cached_thresholds is not None:
            return cached_thresholds
        
        logger.info(f"Loading thresholds from database for role: {role}")
        
        try:
            # Query database for thresholds using Supabase
            table = self.supabase_client.table("scoring_thresholds")
            result = await table.select("role, threshold_type, min_score, max_score").eq("role", role).eq("is_active", True).order("min_score", desc=True).execute()
            
            if not result.data:
                raise ScoringConfigNotFoundError(f"No thresholds found for role: {role}")
            
            # Convert to ScoringThreshold objects
            thresholds = []
            for row in result.data:
                threshold = ScoringThreshold(
                    role=row["role"],
                    threshold_type=row["threshold_type"],
                    min_score=float(row["min_score"]),
                    max_score=float(row["max_score"])
                )
                thresholds.append(threshold)
            
            # Cache the results
            self.cache.cache_thresholds(role, thresholds)
            
            logger.info(f"Loaded {len(thresholds)} thresholds for role: {role}")
            return thresholds
            
        except Exception as e:
            logger.error(f"Error loading thresholds for role {role}: {str(e)}")
            raise
    
    async def load_scoring_categories(self) -> List[Dict[str, Any]]:
        """
        Load all active scoring categories.
        
        Returns:
            List of category dictionaries with name, description, weight
        """
        logger.info("Loading scoring categories from database")
        
        try:
            # Query database for categories using Supabase
            table = self.supabase_client.table("scoring_categories")
            result = await table.select("name, description, weight, is_active").eq("is_active", True).order("name").execute()
            
            # Convert to dictionaries
            categories = []
            for row in result.data:
                category = {
                    "name": row["name"],
                    "description": row["description"],
                    "weight": float(row["weight"]),
                    "is_active": row["is_active"]
                }
                categories.append(category)
            
            logger.info(f"Loaded {len(categories)} scoring categories")
            return categories
            
        except Exception as e:
            logger.error(f"Error loading scoring categories: {str(e)}")
            raise
    
    async def get_complete_role_config(self, role: str) -> Dict[str, Any]:
        """
        Load complete scoring configuration for a role.
        
        Args:
            role: Target role (CTO, CIO, CISO)
            
        Returns:
            Dictionary with algorithms, thresholds, and categories
        """
        logger.info(f"Loading complete configuration for role: {role}")
        
        try:
            # Load all components concurrently if needed, or sequentially for now
            algorithms = await self.load_algorithms_for_role(role)
            thresholds = await self.load_thresholds_for_role(role)
            categories = await self.load_scoring_categories()
            
            config = {
                "role": role,
                "algorithms": [alg.model_dump() for alg in algorithms],
                "thresholds": [th.model_dump() for th in thresholds],
                "categories": categories,
                "loaded_at": datetime.now().isoformat()
            }
            
            logger.info(f"Complete configuration loaded for role: {role}")
            return config
            
        except Exception as e:
            logger.error(f"Error loading complete config for role {role}: {str(e)}")
            raise
