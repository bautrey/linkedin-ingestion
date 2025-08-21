"""Simple test cleanup utilities."""

import asyncio
import logging
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager
import httpx

logger = logging.getLogger(__name__)


class TestCleanupManager:
    """Manages cleanup of test resources."""
    
    def __init__(self):
        self.cleanup_registry = {
            "profiles": [],
            "companies": [],
            "templates": [],
            "scoring_jobs": []
        }
        self._production_config = None
    
    def register_profile(self, profile_id: str):
        """Register a profile for cleanup."""
        if profile_id not in self.cleanup_registry["profiles"]:
            self.cleanup_registry["profiles"].append(profile_id)
            logger.debug(f"Registered profile for cleanup: {profile_id}")
    
    def register_template(self, template_id: str):
        """Register a template for cleanup."""
        if template_id not in self.cleanup_registry["templates"]:
            self.cleanup_registry["templates"].append(template_id)
            logger.debug(f"Registered template for cleanup: {template_id}")
    
    def set_production_config(self, config: Dict[str, Any]):
        """Set production API configuration."""
        self._production_config = config
    
    async def cleanup_all(self, skip_errors: bool = True):
        """Clean up all registered resources."""
        logger.info("Starting test cleanup")
        
        results = {
            "profiles_cleaned": 0,
            "templates_cleaned": 0,
            "errors": []
        }
        
        if self._production_config:
            await self._cleanup_profiles(results, skip_errors)
            await self._cleanup_templates(results, skip_errors)
        
        self.cleanup_registry = {
            "profiles": [],
            "companies": [],
            "templates": [],
            "scoring_jobs": []
        }
        
        return results
    
    async def _cleanup_profiles(self, results: Dict, skip_errors: bool):
        """Clean up profiles."""
        if not self.cleanup_registry["profiles"]:
            return
        
        timeout = httpx.Timeout(30.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            for profile_id in self.cleanup_registry["profiles"]:
                try:
                    response = await client.delete(
                        f"{self._production_config['base_url']}/api/v1/profiles/{profile_id}",
                        headers=self._production_config['api_headers']
                    )
                    if response.status_code in [200, 204, 404]:
                        results["profiles_cleaned"] += 1
                except Exception as e:
                    results["errors"].append(f"Profile cleanup error: {e}")
                    if not skip_errors:
                        raise
    
    async def _cleanup_templates(self, results: Dict, skip_errors: bool):
        """Clean up templates."""
        if not self.cleanup_registry["templates"]:
            return
        
        timeout = httpx.Timeout(30.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            for template_id in self.cleanup_registry["templates"]:
                try:
                    response = await client.delete(
                        f"{self._production_config['base_url']}/api/v1/templates/{template_id}",
                        headers=self._production_config['api_headers']
                    )
                    if response.status_code in [200, 204, 404]:
                        results["templates_cleaned"] += 1
                except Exception as e:
                    results["errors"].append(f"Template cleanup error: {e}")
                    if not skip_errors:
                        raise
