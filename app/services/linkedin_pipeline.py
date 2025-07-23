"""
Complete LinkedIn data ingestion pipeline

Orchestrates the entire flow from Cassidy API to database storage with vector embeddings
"""

import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import uuid

from app.core.logging import LoggerMixin
from app.core.config import settings
from app.cassidy.client import CassidyClient
from app.cassidy.models import LinkedInProfile, CompanyProfile
from app.database import SupabaseClient, EmbeddingService


class LinkedInDataPipeline(LoggerMixin):
    """Complete pipeline for LinkedIn data ingestion and storage"""
    
    def __init__(self):
        self.cassidy_client = CassidyClient()
        self.db_client = SupabaseClient() if self._has_db_config() else None
        self.embedding_service = EmbeddingService() if self._has_openai_config() else None
        
        self.logger.info(
            "LinkedIn pipeline initialized",
            has_database=self.db_client is not None,
            has_embeddings=self.embedding_service is not None
        )
    
    def _has_db_config(self) -> bool:
        """Check if database configuration is available"""
        return bool(settings.SUPABASE_URL and settings.SUPABASE_ANON_KEY)
    
    def _has_openai_config(self) -> bool:
        """Check if OpenAI configuration is available"""
        return bool(settings.get('OPENAI_API_KEY', None))  # Assuming this would be in settings
    
    async def ingest_profile(
        self, 
        linkedin_url: str,
        store_in_db: bool = True,
        generate_embeddings: bool = True
    ) -> Dict[str, Any]:
        """
        Complete profile ingestion pipeline
        
        Args:
            linkedin_url: LinkedIn profile URL
            store_in_db: Whether to store in database
            generate_embeddings: Whether to generate vector embeddings
            
        Returns:
            Pipeline result with profile data and metadata
        """
        pipeline_id = str(uuid.uuid4())
        start_time = datetime.utcnow()
        
        self.logger.info(
            "Starting profile ingestion",
            pipeline_id=pipeline_id,
            linkedin_url=linkedin_url,
            store_in_db=store_in_db,
            generate_embeddings=generate_embeddings
        )
        
        result = {
            "pipeline_id": pipeline_id,
            "linkedin_url": linkedin_url,
            "started_at": start_time.isoformat(),
            "status": "processing",
            "profile": None,
            "companies": [],
            "embeddings": {},
            "storage_ids": {},
            "errors": []
        }
        
        try:
            # Step 1: Fetch profile from Cassidy API
            self.logger.info("Fetching profile from Cassidy", pipeline_id=pipeline_id)
            profile = await self.cassidy_client.fetch_profile(linkedin_url)
            result["profile"] = profile.dict()
            
            # Step 2: Fetch related company data
            companies = []
            if settings.ENABLE_COMPANY_INGESTION and profile.experience:
                self.logger.info("Fetching company data", pipeline_id=pipeline_id)
                company_urls = self._extract_company_urls(profile)
                companies = await self._fetch_companies(company_urls)
                result["companies"] = [c.dict() for c in companies]
            
            # Step 3: Generate embeddings if enabled
            if generate_embeddings and self.embedding_service:
                self.logger.info("Generating embeddings", pipeline_id=pipeline_id)
                
                # Profile embedding
                profile_embedding = await self.embedding_service.embed_profile(profile)
                result["embeddings"]["profile"] = len(profile_embedding)  # Store dimension, not actual values
                
                # Company embeddings
                company_embeddings = []
                for company in companies:
                    embedding = await self.embedding_service.embed_company(company)
                    company_embeddings.append(embedding)
                
                result["embeddings"]["companies"] = len(company_embeddings)
            else:
                profile_embedding = None
                company_embeddings = []
            
            # Step 4: Store in database if enabled
            if store_in_db and self.db_client:
                self.logger.info("Storing data in database", pipeline_id=pipeline_id)
                
                # Store profile
                profile_id = await self.db_client.store_profile(profile, profile_embedding)
                result["storage_ids"]["profile"] = profile_id
                
                # Store companies
                company_ids = []
                for i, company in enumerate(companies):
                    embedding = company_embeddings[i] if company_embeddings else None
                    company_id = await self.db_client.store_company(company, embedding)
                    company_ids.append(company_id)
                
                result["storage_ids"]["companies"] = company_ids
            
            # Pipeline completed successfully
            result["status"] = "completed"
            result["completed_at"] = datetime.utcnow().isoformat()
            
            self.logger.info(
                "Profile ingestion completed successfully",
                pipeline_id=pipeline_id,
                profile_name=profile.name,
                companies_count=len(companies),
                has_embeddings=generate_embeddings and self.embedding_service is not None,
                stored_in_db=store_in_db and self.db_client is not None
            )
            
        except Exception as e:
            result["status"] = "failed"
            result["completed_at"] = datetime.utcnow().isoformat()
            result["errors"].append({
                "error": str(e),
                "error_type": type(e).__name__,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            self.logger.error(
                "Profile ingestion failed",
                pipeline_id=pipeline_id,
                error=str(e),
                error_type=type(e).__name__
            )
            raise
        
        return result
    
    async def batch_ingest_profiles(
        self, 
        linkedin_urls: List[str],
        max_concurrent: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Batch process multiple LinkedIn profiles
        
        Args:
            linkedin_urls: List of LinkedIn profile URLs
            max_concurrent: Maximum concurrent processing
            
        Returns:
            List of pipeline results
        """
        self.logger.info(
            "Starting batch profile ingestion",
            urls_count=len(linkedin_urls),
            max_concurrent=max_concurrent
        )
        
        # Create semaphore to limit concurrency
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_single_profile(url: str) -> Dict[str, Any]:
            async with semaphore:
                try:
                    return await self.ingest_profile(url)
                except Exception as e:
                    self.logger.error(
                        "Batch profile processing failed",
                        linkedin_url=url,
                        error=str(e)
                    )
                    return {
                        "linkedin_url": url,
                        "status": "failed",
                        "errors": [{"error": str(e), "error_type": type(e).__name__}]
                    }
        
        # Process all profiles concurrently with limit
        tasks = [process_single_profile(url) for url in linkedin_urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to error results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "linkedin_url": linkedin_urls[i],
                    "status": "failed",
                    "errors": [{"error": str(result), "error_type": type(result).__name__}]
                })
            else:
                processed_results.append(result)
        
        successful = sum(1 for r in processed_results if r.get("status") == "completed")
        failed = len(processed_results) - successful
        
        self.logger.info(
            "Batch profile ingestion completed",
            total=len(linkedin_urls),
            successful=successful,
            failed=failed
        )
        
        return processed_results
    
    async def find_similar_profiles(
        self, 
        profile: LinkedInProfile,
        limit: int = 10,
        similarity_threshold: float = None
    ) -> List[Dict[str, Any]]:
        """
        Find profiles similar to given profile using vector search
        
        Args:
            profile: Reference profile for similarity search
            limit: Maximum number of similar profiles
            similarity_threshold: Minimum similarity score
            
        Returns:
            List of similar profiles with similarity scores
        """
        if not self.db_client or not self.embedding_service:
            raise ValueError("Database and embedding service required for similarity search")
        
        self.logger.info(
            "Finding similar profiles",
            reference_profile=profile.name,
            limit=limit
        )
        
        # Generate embedding for reference profile
        query_embedding = await self.embedding_service.embed_profile(profile)
        
        # Search for similar profiles
        similar_profiles = await self.db_client.find_similar_profiles(
            query_embedding,
            limit=limit,
            similarity_threshold=similarity_threshold
        )
        
        self.logger.info(
            "Similar profiles found",
            count=len(similar_profiles),
            reference_profile=profile.name
        )
        
        return similar_profiles
    
    async def get_pipeline_health(self) -> Dict[str, Any]:
        """
        Check health of all pipeline components
        
        Returns:
            Health status of pipeline components
        """
        health_status = {
            "pipeline": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {}
        }
        
        # Check Cassidy API health
        try:
            cassidy_health = await self.cassidy_client.health_check()
            health_status["components"]["cassidy"] = cassidy_health
        except Exception as e:
            health_status["components"]["cassidy"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["pipeline"] = "degraded"
        
        # Check database health
        if self.db_client:
            try:
                db_health = await self.db_client.health_check()
                health_status["components"]["database"] = db_health
            except Exception as e:
                health_status["components"]["database"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                health_status["pipeline"] = "degraded"
        else:
            health_status["components"]["database"] = {
                "status": "not_configured",
                "message": "Database client not initialized"
            }
        
        # Check embedding service
        if self.embedding_service:
            health_status["components"]["embeddings"] = {
                "status": "configured",
                "model": self.embedding_service.model,
                "dimension": settings.VECTOR_DIMENSION
            }
        else:
            health_status["components"]["embeddings"] = {
                "status": "not_configured",
                "message": "Embedding service not initialized"
            }
        
        return health_status
    
    def _extract_company_urls(self, profile: LinkedInProfile) -> List[str]:
        """Extract company LinkedIn URLs from profile experience"""
        company_urls = []
        
        # Get from current company
        if profile.current_company and profile.current_company.get('linkedin_url'):
            company_urls.append(profile.current_company['linkedin_url'])
        
        # Get from experience
        for exp in profile.experience:
            if exp.get('company_linkedin_url'):
                company_urls.append(exp['company_linkedin_url'])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_urls = []
        for url in company_urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)
        
        return unique_urls[:5]  # Limit to 5 companies to avoid rate limits
    
    async def _fetch_companies(self, company_urls: List[str]) -> List[CompanyProfile]:
        """Fetch company profiles from URLs"""
        companies = []
        
        for url in company_urls:
            try:
                company = await self.cassidy_client.fetch_company(url)
                companies.append(company)
                
                # Small delay to respect rate limits
                await asyncio.sleep(1)
                
            except Exception as e:
                self.logger.warning(
                    "Failed to fetch company",
                    company_url=url,
                    error=str(e)
                )
                continue
        
        return companies
