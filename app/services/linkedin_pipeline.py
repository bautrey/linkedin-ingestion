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
from app.services.company_service import CompanyService
from app.repositories.company_repository import CompanyRepository
from app.models.canonical.company import CanonicalCompany


class LinkedInDataPipeline(LoggerMixin):
    """Complete pipeline for LinkedIn data ingestion and storage"""
    
    def __init__(self):
        self.cassidy_client = CassidyClient()
        self.db_client = SupabaseClient() if self._has_db_config() else None
        self.embedding_service = EmbeddingService() if self._has_openai_config() else None
        
        # Initialize company service for enhanced profile ingestion
        if self.db_client:
            # We'll initialize the company service lazily when needed
            self.company_service = None  # Will be initialized lazily
        else:
            self.company_service = None
        
        self.logger.info(
            "LinkedIn pipeline initialized",
            has_database=self.db_client is not None,
            has_embeddings=self.embedding_service is not None,
            has_company_service=self.company_service is not None
        )
    
    def _has_db_config(self) -> bool:
        """Check if database configuration is available"""
        return bool(settings.SUPABASE_URL and settings.SUPABASE_ANON_KEY)
    
    def _has_openai_config(self) -> bool:
        """Check if OpenAI configuration is available"""
        return bool(settings.OPENAI_API_KEY)
    
    async def _ensure_company_service(self):
        """Lazily initialize company service when needed"""
        if self.company_service is None and self.db_client:
            # Create company repository with SupabaseClient instance
            company_repo = CompanyRepository(self.db_client)
            self.company_service = CompanyService(company_repo)
    
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
    
    # Enhanced Profile Ingestion with Company Processing
    
    async def ingest_profile_with_companies(
        self,
        linkedin_url: str,
        store_in_db: bool = True,
        generate_embeddings: bool = True
    ) -> Dict[str, Any]:
        """
        Enhanced profile ingestion pipeline with company data extraction and processing.
        
        Args:
            linkedin_url: LinkedIn profile URL
            store_in_db: Whether to store in database
            generate_embeddings: Whether to generate vector embeddings
            
        Returns:
            Pipeline result with profile data and processed company information
        """
        pipeline_id = str(uuid.uuid4())
        start_time = datetime.utcnow()
        
        self.logger.info(
            "Starting enhanced profile ingestion with company processing",
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
            
            # Step 2: Extract and process company data
            companies_processed = []
            try:
                if self.db_client:
                    # Ensure company service is initialized
                    await self._ensure_company_service()
                    
                    if self.company_service:
                        self.logger.info("Processing company data from profile", pipeline_id=pipeline_id)
                        
                        # Extract company data from profile
                        company_data_list = self._extract_company_data_from_profile(profile)
                        
                        if company_data_list:
                            # Use CompanyService to process companies (create/update with deduplication)
                            processing_results = await self.company_service.batch_process_companies(company_data_list)
                            
                            # Convert results for response
                            for process_result in processing_results:
                                if process_result["success"]:
                                    companies_processed.append({
                                        "company_id": process_result["company_id"],
                                        "company_name": process_result["company_name"],
                                        "action": process_result["action"]  # created/updated
                                    })
                            
                            self.logger.info(
                                "Company processing completed",
                                pipeline_id=pipeline_id,
                                companies_processed=len(companies_processed)
                            )
                        else:
                            self.logger.info("No company data found in profile", pipeline_id=pipeline_id)
                            
            except Exception as e:
                error_msg = f"Company processing failed: {str(e)}"
                self.logger.warning(error_msg, pipeline_id=pipeline_id)
                result["errors"].append({
                    "error": error_msg,
                    "error_type": type(e).__name__,
                    "timestamp": datetime.utcnow().isoformat()
                })
                # Continue with profile processing even if company processing fails
            
            result["companies"] = companies_processed
            
            # Step 3: Generate embeddings if enabled
            if generate_embeddings and self.embedding_service:
                self.logger.info("Generating embeddings", pipeline_id=pipeline_id)
                
                # Profile embedding
                profile_embedding = await self.embedding_service.embed_profile(profile)
                result["embeddings"]["profile"] = len(profile_embedding)
            else:
                profile_embedding = None
            
            # Step 4: Store profile in database if enabled
            if store_in_db and self.db_client:
                self.logger.info("Storing profile in database", pipeline_id=pipeline_id)
                
                # Store profile
                profile_id = await self.db_client.store_profile(profile, profile_embedding)
                result["storage_ids"]["profile"] = profile_id
                
                # TODO: Link profile to companies in profile_companies junction table
                # This would be implemented when we add the profile-company linking logic
            
            # Pipeline completed successfully
            result["status"] = "completed"
            result["completed_at"] = datetime.utcnow().isoformat()
            
            self.logger.info(
                "Enhanced profile ingestion completed successfully",
                pipeline_id=pipeline_id,
                profile_name=getattr(profile, 'full_name', getattr(profile, 'name', 'Unknown')),
                companies_count=len(companies_processed),
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
                "Enhanced profile ingestion failed",
                pipeline_id=pipeline_id,
                error=str(e),
                error_type=type(e).__name__
            )
            raise
        
        return result
    
    async def batch_ingest_profiles_with_companies(
        self,
        linkedin_urls: List[str],
        max_concurrent: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Batch process multiple LinkedIn profiles with company data extraction.
        
        Args:
            linkedin_urls: List of LinkedIn profile URLs
            max_concurrent: Maximum concurrent processing
            
        Returns:
            List of pipeline results with company data
        """
        self.logger.info(
            "Starting batch enhanced profile ingestion",
            urls_count=len(linkedin_urls),
            max_concurrent=max_concurrent
        )
        
        # Create semaphore to limit concurrency
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_single_profile(url: str) -> Dict[str, Any]:
            async with semaphore:
                try:
                    return await self.ingest_profile_with_companies(url)
                except Exception as e:
                    self.logger.error(
                        "Batch enhanced profile processing failed",
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
            "Batch enhanced profile ingestion completed",
            total=len(linkedin_urls),
            successful=successful,
            failed=failed
        )
        
        return processed_results
    
    def _extract_company_id_from_linkedin_url(self, linkedin_url: str) -> Optional[str]:
        """
        Extract company ID from LinkedIn company URL.
        
        Args:
            linkedin_url: LinkedIn company URL (e.g., "https://www.linkedin.com/company/5116524")
            
        Returns:
            Company ID string or None if not found
        """
        if not linkedin_url:
            return None
            
        try:
            # Handle different LinkedIn URL formats:
            # https://www.linkedin.com/company/5116524
            # https://www.linkedin.com/company/fortium-partners
            # https://linkedin.com/company/5116524/
            import re
            
            # Extract the part after /company/
            match = re.search(r'/company/([^/?]+)', linkedin_url)
            if match:
                company_identifier = match.group(1)
                
                # If it's numeric, return it directly (this is the company ID)
                if company_identifier.isdigit():
                    return company_identifier
                else:
                    # If it's a company name/slug, we can't convert it to ID without API call
                    # For now, return the slug - this may need enhancement later
                    return company_identifier
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Failed to extract company ID from URL {linkedin_url}: {str(e)}")
            return None

    def _extract_company_data_from_profile(self, profile: LinkedInProfile) -> List[CanonicalCompany]:
        """
        Extract company data from LinkedIn profile and convert to CanonicalCompany models.
        
        Args:
            profile: LinkedInProfile from Cassidy API
            
        Returns:
            List of CanonicalCompany instances
        """
        companies = []
        seen_urls = set()
        
        # Extract current company data
        if profile.company and profile.company.strip():
            company_data = {
                "company_name": profile.company.strip(),
                "linkedin_url": profile.company_linkedin_url,
                "domain": profile.company_domain,
                "employee_count": profile.company_employee_count,
                "employee_range": profile.company_employee_range,
                "industries": [profile.company_industry] if profile.company_industry else [],
                "description": profile.company_description,
                "website": profile.company_website,
                "logo_url": profile.company_logo_url,
                "year_founded": int(profile.company_year_founded) if profile.company_year_founded and profile.company_year_founded.isdigit() else None
            }
            
            # Extract company ID from LinkedIn URL
            if company_data["linkedin_url"]:
                company_data["company_id"] = self._extract_company_id_from_linkedin_url(company_data["linkedin_url"])
            
            # Only add if we have a LinkedIn URL (required for deduplication)
            if company_data["linkedin_url"]:
                try:
                    canonical_company = CanonicalCompany(**{k: v for k, v in company_data.items() if v is not None})
                    companies.append(canonical_company)
                    seen_urls.add(company_data["linkedin_url"])
                except Exception as e:
                    self.logger.warning(f"Failed to create CanonicalCompany from current company data: {str(e)}")
        
        # Extract company data from experience entries
        if hasattr(profile, 'experiences') and profile.experiences:
            for exp in profile.experiences:
                if (exp.company and exp.company.strip() and 
                    exp.company_linkedin_url and 
                    exp.company_linkedin_url not in seen_urls):
                    
                    exp_company_data = {
                        "company_name": exp.company.strip(),
                        "linkedin_url": exp.company_linkedin_url,
                        "logo_url": getattr(exp, 'company_logo_url', None)
                    }
                    
                    # Extract company ID from LinkedIn URL
                    exp_company_data["company_id"] = self._extract_company_id_from_linkedin_url(exp.company_linkedin_url)
                    
                    try:
                        canonical_company = CanonicalCompany(**{k: v for k, v in exp_company_data.items() if v is not None})
                        companies.append(canonical_company)
                        seen_urls.add(exp.company_linkedin_url)
                    except Exception as e:
                        self.logger.warning(f"Failed to create CanonicalCompany from experience data: {str(e)}")
        
        self.logger.debug(f"Extracted {len(companies)} companies from profile")
        return companies
