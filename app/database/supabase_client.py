"""
Supabase client for LinkedIn profile and company data storage

Handles vector storage, retrieval, and similarity search using pgvector
"""

import json
import uuid
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
from supabase import acreate_client, AsyncClient, AsyncClientOptions
import httpx

from app.core.config import settings
from app.core.logging import LoggerMixin
from app.cassidy.models import LinkedInProfile, CompanyProfile
from app.models.canonical.profile import CanonicalProfile
from pydantic import HttpUrl


class SupabaseClient(LoggerMixin):
    """Client for interacting with Supabase database and vector storage"""
    
    def __init__(self):
        if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
            raise ValueError("Supabase URL and ANON_KEY must be configured")
        
        # Create async client (lazily initialized)
        self.client: AsyncClient = None
        self._client_initialized = False
        self.vector_dimension = settings.VECTOR_DIMENSION
    
    async def _ensure_client(self):
        """Ensure the async client is initialized"""
        if not self._client_initialized:
            # Create httpx client with proper configuration to avoid deprecation warnings
            http_client = httpx.AsyncClient(
                timeout=30.0,
                verify=True
            )
            
            # Create options with proper httpx client
            options = AsyncClientOptions(
                httpx_client=http_client
            )
            
            self.client = await acreate_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_ANON_KEY,
                options=options
            )
            self._client_initialized = True
    
    def _serialize_model(self, model) -> Dict[str, Any]:
        """Serialize a Pydantic model, converting HttpUrl objects to strings"""
        data = model.model_dump()
        # Convert HttpUrl objects to strings recursively
        return self._convert_httpurl_to_str(data)
    
    def _convert_httpurl_to_str(self, obj) -> Any:
        """Recursively convert HttpUrl objects to strings in nested data structures"""
        if isinstance(obj, HttpUrl):
            return str(obj)
        elif isinstance(obj, dict):
            return {k: self._convert_httpurl_to_str(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_httpurl_to_str(item) for item in obj]
        else:
            return obj
    
    async def store_profile(
        self, 
        profile: CanonicalProfile, 
        embedding: Optional[List[float]] = None
    ) -> str:
        """
        Store LinkedIn profile in Supabase with optional vector embedding
        
        Args:
            profile: CanonicalProfile instance to store
            embedding: Optional vector embedding for similarity search
            
        Returns:
            str: Unique record ID
        """
        await self._ensure_client()
        self.logger.info("Storing LinkedIn profile", profile_id=profile.profile_id, profile_name=profile.full_name)
        
        # Generate a unique record ID
        record_id = str(uuid.uuid4())
        
        # Prepare profile data for storage
        profile_data = {
            "id": record_id,
            "linkedin_id": profile.profile_id,
            "name": profile.full_name,
            "url": str(profile.linkedin_url) if profile.linkedin_url else None,
            "position": profile.job_title,
            "about": profile.about,
            "city": profile.city,
            "country_code": profile.country,  # Using country instead of country_code
            "followers": profile.follower_count,
            "connections": profile.connection_count,
            "profile_image_url": str(profile.profile_image_url) if profile.profile_image_url else None,
            "suggested_role": profile.suggested_role.value if profile.suggested_role else None,
            "experience": [self._serialize_model(exp) for exp in profile.experiences],
            "education": [self._serialize_model(edu) for edu in profile.educations],
            "certifications": [],  # CanonicalProfile doesn't have certifications field
            "current_company": {"name": profile.company} if profile.company else None,
            "timestamp": profile.timestamp.isoformat() if profile.timestamp else datetime.now(timezone.utc).isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "embedding": embedding
        }
        
        try:
            # Insert into profiles table
            table = self.client.table("linkedin_profiles")
            result = await table.insert(profile_data).execute()
            
            self.logger.info(
                "Profile stored successfully",
                record_id=record_id,
                linkedin_id=profile.profile_id,
                has_embedding=embedding is not None
            )
            
            return record_id
            
        except Exception as e:
            self.logger.error(
                "Failed to store profile",
                profile_id=profile.profile_id,
                error=str(e),
                error_type=type(e).__name__
            )
            raise

    async def delete_profile(self, profile_id: str) -> bool:
        """
        Delete profile by record ID

        Args:
            profile_id: Profile record ID

        Returns:
            bool: True if deletion was successful, False otherwise
        """
        await self._ensure_client()
        self.logger.info("Deleting profile by ID", profile_id=profile_id)

        try:
            table = self.client.table("linkedin_profiles")
            result = await table.delete().eq("id", profile_id).execute()

            # Check if any rows were deleted (result.data will contain deleted rows)
            if result.data and len(result.data) > 0:
                self.logger.info("Profile deleted", profile_id=profile_id, deleted_count=len(result.data))
                return True
            else:
                self.logger.warning("Profile not found for deletion", profile_id=profile_id)
                return False

        except Exception as e:
            self.logger.error(
                "Failed to delete profile",
                profile_id=profile_id,
                error=str(e)
            )
            raise
        
    async def store_company(
        self, 
        company: CompanyProfile, 
        embedding: Optional[List[float]] = None
    ) -> str:
        """
        Store company profile in Supabase with optional vector embedding
        
        Args:
            company: CompanyProfile instance to store
            embedding: Optional vector embedding for similarity search
            
        Returns:
            str: Unique record ID
        """
        await self._ensure_client()
        self.logger.info("Storing company profile", company_id=company.company_id, company_name=company.company_name)
        
        # Generate a unique record ID
        record_id = str(uuid.uuid4())
        
        # Prepare company data for storage
        company_data = {
            "id": record_id,
            "linkedin_company_id": company.company_id,
            "company_name": company.company_name,
            "description": company.description,
            "website": company.website,
            "linkedin_url": str(company.linkedin_url) if company.linkedin_url else None,
            "employee_count": company.employee_count,
            "employee_range": company.employee_range,
            "year_founded": company.year_founded,
            "industries": company.industries,
            "hq_city": company.hq_city,
            "hq_region": company.hq_region,
            "hq_country": company.hq_country,
            "locations": [loc.model_dump() for loc in company.locations],
            "funding_info": company.funding_info.model_dump() if company.funding_info else None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "embedding": embedding
        }
        
        try:
            # Insert into companies table
            table = self.client.table("companies")
            result = await table.insert(company_data).execute()
            
            self.logger.info(
                "Company stored successfully",
                record_id=record_id,
                company_id=company.company_id,
                has_embedding=embedding is not None
            )
            
            return record_id
            
        except Exception as e:
            self.logger.error(
                "Failed to store company",
                company_id=company.company_id,
                error=str(e),
                error_type=type(e).__name__
            )
            raise
    
    async def get_profile_by_linkedin_id(self, linkedin_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve profile by LinkedIn ID
        
        Args:
            linkedin_id: LinkedIn profile ID
            
        Returns:
            Profile data or None if not found
        """
        await self._ensure_client()
        self.logger.info("Retrieving profile by LinkedIn ID", linkedin_id=linkedin_id)
        
        try:
            table = self.client.table("linkedin_profiles")
            result = await table.select("*").eq("linkedin_id", linkedin_id).execute()
            
            if result.data:
                self.logger.info("Profile found", linkedin_id=linkedin_id)
                return result.data[0]
            else:
                self.logger.info("Profile not found", linkedin_id=linkedin_id)
                return None
                
        except Exception as e:
            self.logger.error(
                "Failed to retrieve profile",
                linkedin_id=linkedin_id,
                error=str(e)
            )
            raise
    
    async def get_company_by_linkedin_id(self, company_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve company by LinkedIn company ID
        
        Args:
            company_id: LinkedIn company ID
            
        Returns:
            Company data or None if not found
        """
        await self._ensure_client()
        self.logger.info("Retrieving company by LinkedIn ID", company_id=company_id)
        
        try:
            table = self.client.table("companies")
            result = await table.select("*").eq("linkedin_company_id", company_id).execute()
            
            if result.data:
                self.logger.info("Company found", company_id=company_id)
                return result.data[0]
            else:
                self.logger.info("Company not found", company_id=company_id)
                return None
                
        except Exception as e:
            self.logger.error(
                "Failed to retrieve company",
                company_id=company_id,
                error=str(e)
            )
            raise
    
    async def find_similar_profiles(
        self, 
        embedding: List[float], 
        limit: int = 10,
        similarity_threshold: float = None
    ) -> List[Dict[str, Any]]:
        """
        Find similar profiles using vector similarity search
        
        Args:
            embedding: Query vector embedding
            limit: Maximum number of results
            similarity_threshold: Minimum similarity score (uses config default if None)
            
        Returns:
            List of similar profiles with similarity scores
        """
        await self._ensure_client()
        if similarity_threshold is None:
            similarity_threshold = settings.SIMILARITY_THRESHOLD
        
        self.logger.info(
            "Searching for similar profiles",
            embedding_dimension=len(embedding),
            limit=limit,
            threshold=similarity_threshold
        )
        
        try:
            # Use pgvector similarity search
            # This uses the <-> operator for cosine distance in pgvector
            result = await self.client.rpc(
                "match_profiles",
                {
                    "query_embedding": embedding,
                    "match_threshold": 1.0 - similarity_threshold,  # Convert similarity to distance
                    "match_count": limit
                }
            ).execute()
            
            self.logger.info(
                "Similar profiles found",
                count=len(result.data) if result.data else 0
            )
            
            return result.data or []
            
        except Exception as e:
            self.logger.error(
                "Failed to find similar profiles",
                error=str(e)
            )
            raise
    
    async def find_similar_companies(
        self, 
        embedding: List[float], 
        limit: int = 10,
        similarity_threshold: float = None
    ) -> List[Dict[str, Any]]:
        """
        Find similar companies using vector similarity search
        
        Args:
            embedding: Query vector embedding
            limit: Maximum number of results
            similarity_threshold: Minimum similarity score (uses config default if None)
            
        Returns:
            List of similar companies with similarity scores
        """
        await self._ensure_client()
        if similarity_threshold is None:
            similarity_threshold = settings.SIMILARITY_THRESHOLD
        
        self.logger.info(
            "Searching for similar companies",
            embedding_dimension=len(embedding),
            limit=limit,
            threshold=similarity_threshold
        )
        
        try:
            # Use pgvector similarity search for companies
            result = await self.client.rpc(
                "match_companies",
                {
                    "query_embedding": embedding,
                    "match_threshold": 1.0 - similarity_threshold,
                    "match_count": limit
                }
            ).execute()
            
            self.logger.info(
                "Similar companies found",
                count=len(result.data) if result.data else 0
            )
            
            return result.data or []
            
        except Exception as e:
            self.logger.error(
                "Failed to find similar companies",
                error=str(e)
            )
            raise
    
    async def list_recent_profiles(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recently stored profiles
        
        Args:
            limit: Maximum number of profiles to return
            
        Returns:
            List of recent profiles
        """
        await self._ensure_client()
        self.logger.info("Fetching recent profiles", limit=limit)
        
        try:
            table = self.client.table("linkedin_profiles")
            result = await table.order("created_at", desc=True).limit(limit).execute()
            
            profiles = result.data or []
            self.logger.info("Recent profiles retrieved", count=len(profiles))
            
            return profiles
            
        except Exception as e:
            self.logger.error("Failed to fetch recent profiles", error=str(e))
            raise
    
    async def get_profile_by_url(self, linkedin_url: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve profile by LinkedIn URL
        
        Args:
            linkedin_url: LinkedIn profile URL
            
        Returns:
            Profile data or None if not found
        """
        await self._ensure_client()
        self.logger.info("Retrieving profile by LinkedIn URL", linkedin_url=linkedin_url)
        
        try:
            table = self.client.table("linkedin_profiles")
            result = await table.select("*").eq("url", linkedin_url).execute()
            
            if result.data:
                self.logger.info("Profile found by URL", linkedin_url=linkedin_url)
                return result.data[0]
            else:
                self.logger.info("Profile not found by URL", linkedin_url=linkedin_url)
                return None
                
        except Exception as e:
            self.logger.error(
                "Failed to retrieve profile by URL",
                linkedin_url=linkedin_url,
                error=str(e)
            )
            raise
    
    async def get_profile_by_id(self, profile_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve profile by record ID
        
        Args:
            profile_id: Profile record ID
            
        Returns:
            Profile data or None if not found
        """
        await self._ensure_client()
        self.logger.info("Retrieving profile by ID", profile_id=profile_id)
        
        try:
            table = self.client.table("linkedin_profiles")
            result = await table.select("*").eq("id", profile_id).execute()
            
            if result.data:
                self.logger.info("Profile found by ID", profile_id=profile_id)
                return result.data[0]
            else:
                self.logger.info("Profile not found by ID", profile_id=profile_id)
                return None
                
        except Exception as e:
            self.logger.error(
                "Failed to retrieve profile by ID",
                profile_id=profile_id,
                error=str(e)
            )
            raise
    
    async def search_profiles(
        self,
        name: Optional[str] = None,
        company: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Search profiles with optional filters
        
        Args:
            name: Partial name search (case-insensitive)
            company: Partial company name search (case-insensitive)
            limit: Maximum number of profiles to return
            offset: Number of profiles to skip
            
        Returns:
            List of matching profiles
        """
        await self._ensure_client()
        self.logger.info("Searching profiles", name=name, company=company, limit=limit, offset=offset)
        
        try:
            # Start with base query
            table = self.client.table("linkedin_profiles")
            query = table.select("*")
            
            # Add name filter if provided (case-insensitive)
            if name:
                query = query.ilike("name", f"%{name}%")
            
            # Add company filter if provided (search in current_company and experience)
            if company:
                # This is a simplified approach - in production you might want more sophisticated JSON searching
                query = query.or_(f"current_company->>company_name.ilike.%{company}%,position.ilike.%{company}%")
            
            # Add ordering, limit, and offset
            query = query.order("created_at", desc=True).range(offset, offset + limit - 1)
            
            result = await query.execute()
            
            profiles = result.data or []
            self.logger.info("Profile search completed", count=len(profiles))
            
            return profiles
            
        except Exception as e:
            self.logger.error("Failed to search profiles", error=str(e))
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check database connectivity and health
        
        Returns:
            Health check results
        """
        try:
            await self._ensure_client()
            # Simple query to test connectivity - use a basic select without count
            table = self.client.table("linkedin_profiles")
            result = await table.select("id").limit(1).execute()
            
            # Check if we can access the result data
            data_count = len(result.data) if hasattr(result, 'data') and result.data else 0
            
            return {
                "status": "healthy",
                "connection": "established",
                "sample_query_results": data_count,
                "vector_dimension": self.vector_dimension,
                "similarity_threshold": settings.SIMILARITY_THRESHOLD
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "error_type": type(e).__name__
            }
