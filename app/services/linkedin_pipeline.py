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
        
        # Initialize company service for profile ingestion with company processing
        if self.db_client:
            # Initialize company service immediately
            try:
                company_repo = CompanyRepository(self.db_client)
                self.company_service = CompanyService(company_repo)
            except Exception as e:
                self.logger.warning(f"Failed to initialize company service: {str(e)}")
                self.company_service = None
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
        return bool(getattr(settings, 'OPENAI_API_KEY', None))
    
    async def _ensure_company_service(self):
        """Ensure company service is available (already initialized in __init__)"""
        if self.company_service is None and self.db_client:
            self.logger.warning("Company service was not initialized during startup, initializing now")
            try:
                company_repo = CompanyRepository(self.db_client)
                self.company_service = CompanyService(company_repo)
                self.logger.info("Company service initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize company service: {str(e)}")
                self.company_service = None
        
        if self.company_service is None:
            self.logger.error("Company service is not available - company processing will be skipped")
    
    async def ingest_profile(
        self, 
        linkedin_url: str,
        store_in_db: bool = True,
        generate_embeddings: bool = True
    ) -> Dict[str, Any]:
        """
        Complete unified profile ingestion pipeline with company processing
        
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
            "🚀 PIPELINE_START: Profile ingestion initiated",
            pipeline_id=pipeline_id,
            linkedin_url=linkedin_url,
            store_in_db=store_in_db,
            generate_embeddings=generate_embeddings,
            process_type="PROFILE_INGESTION"
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
            
            # Step 2: Process company data using CompanyService
            companies_processed = []
            try:
                if self.db_client and settings.ENABLE_COMPANY_INGESTION:
                    # Ensure company service is initialized
                    await self._ensure_company_service()
                    
                    if self.company_service:
                        self.logger.info(
                            "🏢 COMPANY_START: Initiating company data processing", 
                            pipeline_id=pipeline_id,
                            process_type="COMPANY_PROCESSING"
                        )
                        
                        # Extract company URLs from profile experience
                        company_urls = self._extract_company_urls(profile)
                        
                        if company_urls:
                            self.logger.info(
                                "Found company URLs to fetch",
                                pipeline_id=pipeline_id,
                                company_count=len(company_urls),
                                company_urls=company_urls[:3]  # Log first 3 for debugging
                            )
                            
                            # Fetch detailed company data from Cassidy API
                            cassidy_companies = await self._fetch_companies(company_urls)
                            
                            if cassidy_companies:
                                self.logger.info(
                                    "Successfully fetched companies from Cassidy API",
                                    pipeline_id=pipeline_id,
                                    companies_fetched=len(cassidy_companies)
                                )
                                
                                # Convert Cassidy CompanyProfile objects to CanonicalCompany for database storage
                                canonical_companies = []
                                for cassidy_company in cassidy_companies:
                                    try:
                                        # Convert CompanyProfile to CanonicalCompany format
                                        canonical_data = {
                                            "company_name": cassidy_company.company_name,
                                            "company_id": cassidy_company.company_id,
                                            "linkedin_url": cassidy_company.linkedin_url,
                                            "description": cassidy_company.description,
                                            "website": cassidy_company.website,
                                            "domain": cassidy_company.domain,
                                            "employee_count": cassidy_company.employee_count,
                                            "employee_range": cassidy_company.employee_range,
                                            "year_founded": cassidy_company.year_founded,
                                            "industries": cassidy_company.industries or [],
                                            "hq_city": cassidy_company.hq_city,
                                            "hq_region": cassidy_company.hq_region,
                                            "hq_country": cassidy_company.hq_country,
                                            "logo_url": cassidy_company.logo_url,
                                        }
                                        
                                        # Filter out None values and create CanonicalCompany
                                        filtered_data = {k: v for k, v in canonical_data.items() if v is not None}
                                        canonical_company = CanonicalCompany(**filtered_data)
                                        canonical_companies.append(canonical_company)
                                    except Exception as e:
                                        self.logger.warning(
                                            "Failed to convert Cassidy company to canonical format",
                                            pipeline_id=pipeline_id,
                                            company_name=getattr(cassidy_company, 'company_name', 'Unknown'),
                                            error=str(e)
                                        )
                                        continue
                                
                                # Use CompanyService to process companies (create/update with deduplication)
                                if canonical_companies:
                                    processing_results = await self.company_service.batch_process_companies(canonical_companies)
                                    
                                    # Convert results for response
                                    for process_result in processing_results:
                                        if process_result["success"]:
                                            companies_processed.append({
                                                "company_id": process_result["company_id"],
                                                "company_name": process_result["company_name"],
                                                "action": process_result["action"]  # created/updated
                                            })
                                    
                                    self.logger.info(
                                        "🏁 COMPANY_COMPLETE: Company data processing finished successfully",
                                        pipeline_id=pipeline_id,
                                        companies_processed=len(companies_processed),
                                        process_type="COMPANY_PROCESSING",
                                        status="SUCCESS"
                                    )
                            else:
                                self.logger.warning("No companies fetched from Cassidy API", pipeline_id=pipeline_id)
                        else:
                            self.logger.info("No company URLs found in profile", pipeline_id=pipeline_id)
                            
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
                result["embeddings"]["profile"] = len(profile_embedding)  # Store dimension, not actual values
            else:
                profile_embedding = None
            
            # Step 4: Store profile in database if enabled
            if store_in_db and self.db_client:
                self.logger.info("Storing data in database", pipeline_id=pipeline_id)
                
                # Store profile
                profile_id = await self.db_client.store_profile(profile, profile_embedding)
                result["storage_ids"]["profile"] = profile_id
                
                # TODO: Link profile to companies in profile_companies junction table
                # This would be implemented when we add the profile-company linking logic
            
            # Pipeline completed successfully
            result["status"] = "completed"
            result["completed_at"] = datetime.utcnow().isoformat()
            
            self.logger.info(
                "🏁 PIPELINE_COMPLETE: Profile ingestion finished successfully",
                pipeline_id=pipeline_id,
                profile_name=getattr(profile, 'full_name', getattr(profile, 'name', 'Unknown')),
                companies_count=len(companies_processed),
                has_embeddings=generate_embeddings and self.embedding_service is not None,
                stored_in_db=store_in_db and self.db_client is not None,
                process_type="PROFILE_INGESTION",
                status="SUCCESS"
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
        self.logger.info(f"DEBUG: Starting company URL extraction from profile: {getattr(profile, 'full_name', 'Unknown')}")
        company_urls = []
        
        # Get from current company - current_company is a dictionary property
        if hasattr(profile, 'current_company') and profile.current_company:
            linkedin_url = profile.current_company.get('linkedin_url')
            if linkedin_url:
                self.logger.info(f"DEBUG: Found current company URL: {linkedin_url}")
                company_urls.append(linkedin_url)
        
        # Get from experience - using attribute access since ExperienceEntry is a Pydantic model
        if hasattr(profile, 'experience') and profile.experience:
            self.logger.info(f"DEBUG: Profile has {len(profile.experience)} experience entries")
            for i, exp in enumerate(profile.experience):
                if hasattr(exp, 'company_linkedin_url') and exp.company_linkedin_url:
                    self.logger.info(f"DEBUG: Experience {i+1}: Found company URL: {exp.company_linkedin_url} (Company: {getattr(exp, 'company', 'Unknown')})")
                    company_urls.append(exp.company_linkedin_url)
                else:
                    self.logger.info(f"DEBUG: Experience {i+1}: No company URL found (Company: {getattr(exp, 'company', 'Unknown')})")
        
        self.logger.info(f"DEBUG: Total company URLs found before deduplication: {len(company_urls)}")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_urls = []
        for url in company_urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)
            else:
                self.logger.info(f"DEBUG: Skipping duplicate URL: {url}")
        
        self.logger.info(f"DEBUG: Unique company URLs after deduplication: {len(unique_urls)}")
        
        # Apply rate limit filtering for now (we'll remove this later after debugging)
        filtered_urls = unique_urls[:5]  # Limit to 5 companies to avoid rate limits
        if len(unique_urls) > 5:
            self.logger.info(f"DEBUG: Rate limiting applied - processing first 5 of {len(unique_urls)} companies")
            
        self.logger.info(f"DEBUG: Final company URLs to fetch: {len(filtered_urls)}")
        for i, url in enumerate(filtered_urls):
            self.logger.info(f"DEBUG: Company URL {i+1}: {url}")
            
        return filtered_urls
    
    async def _fetch_companies(self, company_urls: List[str]) -> List[CompanyProfile]:
        """Fetch company profiles from URLs"""
        self.logger.info(f"DEBUG: Starting company fetch for {len(company_urls)} URLs")
        companies = []
        
        for i, url in enumerate(company_urls):
            self.logger.info(f"DEBUG: Fetching company {i+1}/{len(company_urls)}: {url}")
            try:
                self.logger.info(f"DEBUG: Calling Cassidy API for company: {url}")
                company = await self.cassidy_client.fetch_company(url)
                self.logger.info(f"DEBUG: Successfully fetched company: {getattr(company, 'company_name', 'Unknown')} from {url}")
                companies.append(company)
                
                # Small delay to respect rate limits
                self.logger.info(f"DEBUG: Adding 1 second delay before next company fetch")
                await asyncio.sleep(1)
                
            except Exception as e:
                self.logger.error(
                    f"DEBUG: Failed to fetch company {i+1}/{len(company_urls)}",
                    company_url=url,
                    error=str(e),
                    error_type=type(e).__name__
                )
                continue
        
        self.logger.info(f"DEBUG: Company fetch completed - successfully fetched {len(companies)} out of {len(company_urls)} companies")
        return companies
    
    def convert_cassidy_to_canonical(self, cassidy_companies: List[CompanyProfile]) -> List[CanonicalCompany]:
        """
        Convert Cassidy CompanyProfile objects to CanonicalCompany format
        
        Args:
            cassidy_companies: List of CompanyProfile objects from Cassidy API
            
        Returns:
            List of CanonicalCompany objects ready for database storage
        """
        self.logger.info(f"DEBUG: convert_cassidy_to_canonical starting with {len(cassidy_companies)} companies")
        canonical_companies = []
        for i, cassidy_company in enumerate(cassidy_companies):
            try:
                self.logger.info(f"DEBUG: Converting company {i+1}/{len(cassidy_companies)}: {getattr(cassidy_company, 'company_name', 'Unknown')}")
                
                # Convert CompanyProfile to CanonicalCompany format
                canonical_data = {
                    "company_name": cassidy_company.company_name,
                    "company_id": cassidy_company.company_id,
                    "linkedin_url": cassidy_company.linkedin_url,
                    "description": cassidy_company.description,
                    "website": cassidy_company.website,
                    "domain": cassidy_company.domain,
                    "employee_count": cassidy_company.employee_count,
                    "employee_range": cassidy_company.employee_range,
                    "year_founded": cassidy_company.year_founded,
                    "industries": cassidy_company.industries or [],
                    "hq_city": cassidy_company.hq_city,
                    "hq_region": cassidy_company.hq_region,
                    "hq_country": cassidy_company.hq_country,
                    "logo_url": cassidy_company.logo_url,
                }
                
                self.logger.info(f"DEBUG: Company data before filtering: {len([k for k, v in canonical_data.items() if v is not None])} non-None fields")
                
                # Filter out None values and create CanonicalCompany
                filtered_data = {k: v for k, v in canonical_data.items() if v is not None}
                self.logger.info(f"DEBUG: Creating CanonicalCompany with {len(filtered_data)} fields")
                
                canonical_company = CanonicalCompany(**filtered_data)
                canonical_companies.append(canonical_company)
                
                self.logger.info(f"DEBUG: Successfully converted company {i+1}: {canonical_company.company_name}")
            except Exception as e:
                self.logger.warning(
                    "Failed to convert Cassidy company to canonical format",
                    company_name=getattr(cassidy_company, 'company_name', 'Unknown'),
                    error=str(e)
                )
                continue
        
        self.logger.info(f"DEBUG: convert_cassidy_to_canonical completed with {len(canonical_companies)} canonical companies")
        return canonical_companies
    
    # Enhanced Profile Ingestion with Company Processing
    
    async def ingest_profile_with_companies(
        self,
        linkedin_url: str,
        store_in_db: bool = True,
        generate_embeddings: bool = True
    ) -> Dict[str, Any]:
        """
        Profile ingestion pipeline with company data extraction and processing.
        
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
            "Starting profile ingestion with company processing",
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
            
            # Step 2: Fetch company data from Cassidy API and process
            companies_processed = []
            try:
                if self.db_client and settings.ENABLE_COMPANY_INGESTION:
                    # Ensure company service is initialized
                    await self._ensure_company_service()
                    
                    if self.company_service:
                        self.logger.info("Fetching company data from Cassidy API", pipeline_id=pipeline_id)
                        
                        # Extract company URLs from profile experience
                        company_urls = self._extract_company_urls(profile)
                        
                        if company_urls:
                            self.logger.info(
                                "Found company URLs to fetch",
                                pipeline_id=pipeline_id,
                                company_count=len(company_urls),
                                company_urls=company_urls[:3]  # Log first 3 for debugging
                            )
                            
                            # Fetch detailed company data from Cassidy API
                            cassidy_companies = await self._fetch_companies(company_urls)
                            
                            if cassidy_companies:
                                self.logger.info(
                                    "Successfully fetched companies from Cassidy API",
                                    pipeline_id=pipeline_id,
                                    companies_fetched=len(cassidy_companies)
                                )
                                
                                # Convert Cassidy CompanyProfile objects to CanonicalCompany for database storage
                                canonical_companies = []
                                for cassidy_company in cassidy_companies:
                                    try:
                                        # Convert CompanyProfile to CanonicalCompany format
                                        canonical_data = {
                                            "company_name": cassidy_company.company_name,
                                            "company_id": cassidy_company.company_id,
                                            "linkedin_url": cassidy_company.linkedin_url,
                                            "description": cassidy_company.description,
                                            "website": cassidy_company.website,
                                            "domain": cassidy_company.domain,
                                            "employee_count": cassidy_company.employee_count,
                                            "employee_range": cassidy_company.employee_range,
                                            "year_founded": cassidy_company.year_founded,
                                            "industries": cassidy_company.industries or [],
                                            "hq_city": cassidy_company.hq_city,
                                            "hq_region": cassidy_company.hq_region,
                                            "hq_country": cassidy_company.hq_country,
                                            "logo_url": cassidy_company.logo_url,
                                        }
                                        
                                        # Filter out None values and create CanonicalCompany
                                        filtered_data = {k: v for k, v in canonical_data.items() if v is not None}
                                        canonical_company = CanonicalCompany(**filtered_data)
                                        canonical_companies.append(canonical_company)
                                    except Exception as e:
                                        self.logger.warning(
                                            "Failed to convert Cassidy company to canonical format",
                                            pipeline_id=pipeline_id,
                                            company_name=getattr(cassidy_company, 'company_name', 'Unknown'),
                                            error=str(e)
                                        )
                                        continue
                                
                                # Use CompanyService to process companies (create/update with deduplication)
                                if canonical_companies:
                                    processing_results = await self.company_service.batch_process_companies(canonical_companies)
                                    
                                    # Convert results for response
                                    for process_result in processing_results:
                                        if process_result["success"]:
                                            companies_processed.append({
                                                "company_id": process_result["company_id"],
                                                "company_name": process_result["company_name"],
                                                "action": process_result["action"]  # created/updated
                                            })
                                    
                                    self.logger.info(
                                        "Company processing completed with Cassidy data",
                                        pipeline_id=pipeline_id,
                                        companies_processed=len(companies_processed)
                                    )
                            else:
                                self.logger.warning("No companies fetched from Cassidy API", pipeline_id=pipeline_id)
                        else:
                            self.logger.info("No company URLs found in profile", pipeline_id=pipeline_id)
                            
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
                "Profile ingestion completed successfully",
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
                "Profile ingestion failed",
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
            "Starting batch profile ingestion",
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
                "domain": self._extract_domain_from_company_data(profile.company_domain, profile.company_website),
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
                extracted_id = self._extract_company_id_from_linkedin_url(company_data["linkedin_url"])
                company_data["company_id"] = extracted_id
                self.logger.debug(f"Extracted company ID: {extracted_id} from URL: {company_data['linkedin_url']}")
            
            # Only add if we have a LinkedIn URL (required for deduplication)
            if company_data["linkedin_url"]:
                try:
                    # Filter out None values but keep empty strings for company_id (better than None for DB)
                    filtered_data = {k: v for k, v in company_data.items() if v is not None}
                    # Ensure company_id is included and never None/empty for DB constraint
                    if "company_id" not in filtered_data or not filtered_data.get("company_id"):
                        # Use a fallback if extraction failed - this shouldn't happen with our regex but ensures DB compatibility
                        filtered_data["company_id"] = "unknown"
                    
                    canonical_company = CanonicalCompany(**filtered_data)
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
                        "logo_url": getattr(exp, 'company_logo_url', None),
                        "domain": self._extract_domain_from_experience(exp)
                    }
                    
                    # Extract company ID from LinkedIn URL
                    extracted_id = self._extract_company_id_from_linkedin_url(exp.company_linkedin_url)
                    exp_company_data["company_id"] = extracted_id
                    self.logger.debug(f"Extracted company ID: {extracted_id} from experience URL: {exp.company_linkedin_url}")
                    
                    try:
                        # Filter out None values but ensure company_id is preserved
                        filtered_data = {k: v for k, v in exp_company_data.items() if v is not None}
                        # Ensure company_id is included and never None/empty for DB constraint  
                        if "company_id" not in filtered_data or not filtered_data.get("company_id"):
                            # Use a fallback if extraction failed - this shouldn't happen with our regex but ensures DB compatibility
                            filtered_data["company_id"] = "unknown"
                        
                        canonical_company = CanonicalCompany(**filtered_data)
                        companies.append(canonical_company)
                        seen_urls.add(exp.company_linkedin_url)
                    except Exception as e:
                        self.logger.warning(f"Failed to create CanonicalCompany from experience data: {str(e)}")
        
        self.logger.debug(f"Extracted {len(companies)} companies from profile")
        return companies
    
    def _extract_domain_from_company_data(self, company_domain: str, company_website: str) -> Optional[str]:
        """
        Extract domain from company data with fallback logic.
        
        Args:
            company_domain: Direct domain from profile
            company_website: Website URL to extract domain from
            
        Returns:
            Extracted domain or None if not available
        """
        # First, try the direct domain
        if company_domain and company_domain.strip():
            return company_domain.strip()
        
        # Fallback to extracting from website URL
        if company_website and company_website.strip():
            try:
                from urllib.parse import urlparse
                parsed = urlparse(company_website.strip())
                if parsed.netloc:
                    domain = parsed.netloc.lower()
                    # Remove www. prefix if present
                    if domain.startswith('www.'):
                        domain = domain[4:]
                    return domain
            except Exception as e:
                self.logger.debug(f"Failed to extract domain from website {company_website}: {str(e)}")
        
        return None
    
    def _extract_domain_from_experience(self, exp) -> Optional[str]:
        """
        Extract domain from experience entry if available.
        
        Args:
            exp: Experience entry object
            
        Returns:
            Extracted domain or None
        """
        # Check if experience has website or domain info
        if hasattr(exp, 'company_website') and exp.company_website:
            try:
                from urllib.parse import urlparse
                parsed = urlparse(exp.company_website.strip())
                if parsed.netloc:
                    domain = parsed.netloc.lower()
                    if domain.startswith('www.'):
                        domain = domain[4:]
                    return domain
            except Exception as e:
                self.logger.debug(f"Failed to extract domain from experience website: {str(e)}")
        
        return None
