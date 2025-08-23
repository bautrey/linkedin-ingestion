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
            "suggested_role": None,  # Will be set separately via update_profile_suggested_role
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
    
    async def update_profile_suggested_role(self, profile_id: str, suggested_role: str) -> bool:
        """
        Update the suggested_role field for a profile

        Args:
            profile_id: Profile record ID
            suggested_role: New suggested role value

        Returns:
            bool: True if update was successful, False otherwise
        """
        await self._ensure_client()
        self.logger.info("Updating profile suggested role", profile_id=profile_id, suggested_role=suggested_role)

        try:
            table = self.client.table("linkedin_profiles")
            result = await table.update({"suggested_role": suggested_role}).eq("id", profile_id).execute()

            # Check if any rows were updated (result.data will contain updated rows)
            if result.data and len(result.data) > 0:
                self.logger.info("Profile suggested role updated", profile_id=profile_id, suggested_role=suggested_role)
                return True
            else:
                self.logger.warning("Profile not found for suggested role update", profile_id=profile_id)
                return False

        except Exception as e:
            self.logger.error(
                "Failed to update profile suggested role",
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
        location: Optional[str] = None,
        score_range: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Search profiles with optional filters
        
        Args:
            name: Partial name search (case-insensitive)
            company: Partial company name search (case-insensitive)
            location: Partial location search (case-insensitive, searches city field)
            score_range: Score range filter: 'unscored', 'high' (8-10), 'medium' (5-7), 'low' (1-4)
            limit: Maximum number of profiles to return
            offset: Number of profiles to skip
            
        Returns:
            List of matching profiles
        """
        await self._ensure_client()
        self.logger.info("Searching profiles", name=name, company=company, location=location, score_range=score_range, limit=limit, offset=offset)
        
        try:
            # For score filtering, we need to handle it differently since we need to join with profile_scores
            if score_range:
                # First, get profile IDs that match the score criteria
                scored_profile_ids = set()
                
                if score_range.lower() == "unscored":
                    # Get all profile linkedin_ids from profile_scores
                    scores_table = self.client.table("profile_scores")
                    scores_result = await scores_table.select("profile_id").execute()
                    scored_linkedin_ids = {row["profile_id"] for row in scores_result.data or []}
                    
                    # Get all profiles and filter out the scored ones
                    profiles_table = self.client.table("linkedin_profiles")
                    query = profiles_table.select("*")
                    
                    # Add other filters
                    if name:
                        query = query.ilike("name", f"%{name}%")
                    if company:
                        query = query.or_(f"current_company->>company_name.ilike.%{company}%,position.ilike.%{company}%")
                    if location:
                        query = query.ilike("city", f"%{location}%")
                    
                    query = query.order("created_at", desc=True).range(offset, offset + limit - 1)
                    result = await query.execute()
                    
                    # Filter out profiles that have scores
                    profiles = [p for p in (result.data or []) if p.get("linkedin_id") not in scored_linkedin_ids]
                    
                else:
                    # Get profiles with scores in the specified range
                    scores_table = self.client.table("profile_scores")
                    scores_query = scores_table.select("profile_id")
                    
                    if score_range.lower() == "high":
                        scores_query = scores_query.gte("overall_score", 8.0).lte("overall_score", 10.0)
                    elif score_range.lower() == "medium":
                        scores_query = scores_query.gte("overall_score", 5.0).lt("overall_score", 8.0)
                    elif score_range.lower() == "low":
                        scores_query = scores_query.gte("overall_score", 1.0).lt("overall_score", 5.0)
                    else:
                        # Handle custom ranges like "7-10"
                        if "-" in score_range:
                            try:
                                min_score, max_score = score_range.split("-")
                                min_score = float(min_score.strip())
                                max_score = float(max_score.strip())
                                scores_query = scores_query.gte("overall_score", min_score).lte("overall_score", max_score)
                            except (ValueError, IndexError):
                                self.logger.warning(f"Invalid score_range format: {score_range}")
                                # Fall back to no score filtering
                                scores_query = None
                        else:
                            scores_query = None
                    
                    if scores_query:
                        scores_result = await scores_query.execute()
                        target_linkedin_ids = [row["profile_id"] for row in scores_result.data or []]
                        
                        if target_linkedin_ids:
                            # Get profiles matching these linkedin_ids
                            profiles_table = self.client.table("linkedin_profiles")
                            query = profiles_table.select("*").in_("linkedin_id", target_linkedin_ids)
                            
                            # Add other filters
                            if name:
                                query = query.ilike("name", f"%{name}%")
                            if company:
                                query = query.or_(f"current_company->>company_name.ilike.%{company}%,position.ilike.%{company}%")
                            if location:
                                query = query.ilike("city", f"%{location}%")
                            
                            query = query.order("created_at", desc=True).range(offset, offset + limit - 1)
                            result = await query.execute()
                            profiles = result.data or []
                        else:
                            profiles = []  # No profiles match the score criteria
                    else:
                        # Fall back to regular search without score filtering
                        profiles_table = self.client.table("linkedin_profiles")
                        query = profiles_table.select("*")
                        
                        if name:
                            query = query.ilike("name", f"%{name}%")
                        if company:
                            query = query.or_(f"current_company->>company_name.ilike.%{company}%,position.ilike.%{company}%")
                        if location:
                            query = query.ilike("city", f"%{location}%")
                        
                        query = query.order("created_at", desc=True).range(offset, offset + limit - 1)
                        result = await query.execute()
                        profiles = result.data or []
                
            else:
                # Regular query without score filtering
                table = self.client.table("linkedin_profiles")
                query = table.select("*")
                
                # Add name filter if provided (case-insensitive)
                if name:
                    query = query.ilike("name", f"%{name}%")
                
                # Add company filter if provided (search in current_company and experience)
                if company:
                    # This is a simplified approach - in production you might want more sophisticated JSON searching
                    query = query.or_(f"current_company->>company_name.ilike.%{company}%,position.ilike.%{company}%")
                
                # Add location filter if provided (search in city field)
                if location:
                    query = query.ilike("city", f"%{location}%")
                
                # Add ordering, limit, and offset
                query = query.order("created_at", desc=True).range(offset, offset + limit - 1)
                
                result = await query.execute()
                profiles = result.data or []
            
            self.logger.info("Profile search completed", count=len(profiles))
            return profiles
            
        except Exception as e:
            self.logger.error("Failed to search profiles", error=str(e))
            raise
    
    async def link_profile_to_company(
        self,
        profile_id: str,
        company_id: str,
        job_title: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        duration_text: Optional[str] = None,
        is_current_role: bool = False,
        description: Optional[str] = None
    ) -> str:
        """
        Link a profile to a company with job details in the junction table
        
        Args:
            profile_id: Profile record ID
            company_id: Company record ID
            job_title: Job title/position
            start_date: Job start date
            end_date: Job end date
            duration_text: Duration as text (e.g., "2 yrs 3 mos")
            is_current_role: Whether this is a current role
            description: Job description
            
        Returns:
            str: Junction table record ID
        """
        await self._ensure_client()
        self.logger.info(
            "Linking profile to company", 
            profile_id=profile_id, 
            company_id=company_id, 
            job_title=job_title,
            is_current_role=is_current_role
        )
        
        # Generate a unique record ID
        record_id = str(uuid.uuid4())
        
        # Prepare junction table data
        junction_data = {
            "id": record_id,
            "profile_id": profile_id,
            "company_id": company_id,
            "job_title": job_title,
            "start_date": start_date,
            "end_date": end_date,
            "duration_text": duration_text,
            "is_current_role": is_current_role,
            "description": description,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        try:
            # Insert into profile_companies junction table
            table = self.client.table("profile_companies")
            result = await table.insert(junction_data).execute()
            
            self.logger.info(
                "Profile-company link created",
                record_id=record_id,
                profile_id=profile_id,
                company_id=company_id
            )
            
            return record_id
            
        except Exception as e:
            self.logger.error(
                "Failed to link profile to company",
                profile_id=profile_id,
                company_id=company_id,
                error=str(e),
                error_type=type(e).__name__
            )
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
