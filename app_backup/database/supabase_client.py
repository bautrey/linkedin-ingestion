"""
Supabase client for LinkedIn profile and company data storage

Handles vector storage, retrieval, and similarity search using pgvector
"""

import json
import uuid
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from supabase import acreate_client, AsyncClient

from app.core.config import settings
from app.core.logging import LoggerMixin
from app.cassidy.models import LinkedInProfile, CompanyProfile


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
            self.client = await acreate_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_ANON_KEY
            )
            self._client_initialized = True
    
    async def store_profile(
        self, 
        profile: LinkedInProfile, 
        embedding: Optional[List[float]] = None
    ) -> str:
        """
        Store LinkedIn profile in Supabase with optional vector embedding
        
        Args:
            profile: LinkedInProfile instance to store
            embedding: Optional vector embedding for similarity search
            
        Returns:
            str: Unique record ID
        """
        await self._ensure_client()
        self.logger.info("Storing LinkedIn profile", profile_id=profile.id, profile_name=profile.name)
        
        # Generate a unique record ID
        record_id = str(uuid.uuid4())
        
        # Prepare profile data for storage
        profile_data = {
            "id": record_id,
            "linkedin_id": profile.id,
            "name": profile.name,
            "url": str(profile.url),
            "position": profile.position,
            "about": profile.about,
            "city": profile.city,
            "country_code": profile.country_code,
            "followers": profile.followers,
            "connections": profile.connections,
            "experience": [exp.model_dump() if hasattr(exp, 'model_dump') else (exp.dict() if hasattr(exp, 'dict') else exp) for exp in profile.experience],
            "education": [edu.model_dump() if hasattr(edu, 'model_dump') else (edu.dict() if hasattr(edu, 'dict') else edu) for edu in profile.education],
            "certifications": [cert.model_dump() if hasattr(cert, 'model_dump') else (cert.dict() if hasattr(cert, 'dict') else cert) for cert in profile.certifications],
            "current_company": profile.current_company if isinstance(profile.current_company, dict) else (profile.current_company.model_dump() if hasattr(profile.current_company, 'model_dump') else profile.current_company.dict()) if profile.current_company else None,
            "timestamp": profile.timestamp.isoformat() if profile.timestamp else datetime.utcnow().isoformat(),
            "created_at": datetime.utcnow().isoformat(),
            "embedding": embedding
        }
        
        try:
            # Insert into profiles table
            result = await self.client.table("linkedin_profiles").insert(profile_data).execute()
            
            self.logger.info(
                "Profile stored successfully",
                record_id=record_id,
                linkedin_id=profile.id,
                has_embedding=embedding is not None
            )
            
            return record_id
            
        except Exception as e:
            self.logger.error(
                "Failed to store profile",
                profile_id=profile.id,
                error=str(e),
                error_type=type(e).__name__
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
            "locations": [loc.dict() if hasattr(loc, 'dict') else loc for loc in company.locations],
            "funding_info": company.funding_info.dict() if company.funding_info else None,
            "created_at": datetime.utcnow().isoformat(),
            "embedding": embedding
        }
        
        try:
            # Insert into companies table
            result = await self.client.table("companies").insert(company_data).execute()
            
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
            result = await self.client.table("linkedin_profiles").select("*").eq("linkedin_id", linkedin_id).execute()
            
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
            result = await self.client.table("companies").select("*").eq("linkedin_company_id", company_id).execute()
            
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
            result = await self.client.table("linkedin_profiles").select("*").order("created_at", desc=True).limit(limit).execute()
            
            profiles = result.data or []
            self.logger.info("Recent profiles retrieved", count=len(profiles))
            
            return profiles
            
        except Exception as e:
            self.logger.error("Failed to fetch recent profiles", error=str(e))
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
            result = await self.client.table("linkedin_profiles").select("id").limit(1).execute()
            
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
