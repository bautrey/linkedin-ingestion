"""
Workflow orchestrator for LinkedIn profile and company data ingestion

Handles the complete ingestion process including profile fetching,
company data enrichment, and data validation.
"""

import asyncio
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta, timezone
import uuid

from app.core.config import settings
from app.core.logging import LoggerMixin
from .client import CassidyClient
from .models import (
    LinkedInProfile,
    CompanyProfile,
    ProfileIngestionRequest,
    IngestionResponse,
    IngestionStatus,
    WorkflowStatus,
)
from .exceptions import CassidyException
from app.adapters.cassidy_adapter import CassidyAdapter
from app.adapters.exceptions import IncompleteDataError
from app.models.canonical import CanonicalProfile


class EnrichedProfile:
    """Container for profile with associated company data"""
    
    def __init__(self, profile: CanonicalProfile, companies: List[Optional[CompanyProfile]] = None):
        self.profile = profile
        self.companies = companies or []
        self.created_at = datetime.now(timezone.utc)
    
    @property
    def company_count(self) -> int:
        """Number of successfully fetched companies"""
        return sum(1 for c in self.companies if c is not None)
    
    @property
    def total_company_requests(self) -> int:
        """Total number of company requests made"""
        return len(self.companies)


class LinkedInWorkflow(LoggerMixin):
    """
    Orchestrates the complete LinkedIn ingestion workflow
    
    Handles profile fetching, company data enrichment, and provides
    status tracking for long-running operations.
    """
    
    def __init__(self):
        self.cassidy_client = CassidyClient()
        self.adapter = CassidyAdapter()
        self._active_requests: Dict[str, IngestionStatus] = {}
    
    async def process_profile(
        self, 
        request: ProfileIngestionRequest,
        request_id: Optional[str] = None
    ) -> Tuple[str, EnrichedProfile]:
        """
        Process a complete LinkedIn profile ingestion
        
        Args:
            request: Profile ingestion request
            request_id: Optional request ID for tracking
            
        Returns:
            Tuple of (request_id, enriched_profile)
            
        Raises:
            CassidyException: Various ingestion errors
        """
        if not request_id:
            request_id = str(uuid.uuid4())
        
        self.logger.info(
            "Starting profile processing workflow",
            request_id=request_id,
            linkedin_url=str(request.linkedin_url),
            include_companies=request.include_companies
        )
        
        # Initialize status tracking
        status = IngestionStatus(
            request_id=request_id,
            status=WorkflowStatus.RUNNING,
            profile_url=request.linkedin_url,
            started_at=datetime.now(timezone.utc),
            progress={"stage": "profile_fetch", "step": 1, "total_steps": 2}
        )
        self._active_requests[request_id] = status
        
        try:
            # Step 1: Fetch profile data from Cassidy API
            self.logger.info("Fetching profile data", request_id=request_id)
            linkedin_profile_model = await self.cassidy_client.fetch_profile(str(request.linkedin_url))
            
            # Convert Pydantic model to dict for the adapter
            cassidy_data = linkedin_profile_model.model_dump()
            
            # Use CassidyAdapter to transform the data
            try:
                canonical_profile = self.adapter.transform(cassidy_data)
            except IncompleteDataError as e:
                self.logger.error(
                    "Transformation failed due to incomplete data",
                    missing_fields=e.missing_fields,
                    request_id=request_id
                )
                raise
            
            # Update progress
            status.progress = {"stage": "company_fetch", "step": 2, "total_steps": 2}
            
            companies = []
            if request.include_companies and settings.ENABLE_COMPANY_INGESTION:
                # Step 2: Fetch company data for experiences
                self.logger.info(
                    "Fetching company data for experiences",
                    request_id=request_id,
                    experience_count=len(canonical_profile.experiences)
                )
                companies = await self._fetch_companies_for_profile(canonical_profile, request_id)
            
            # Complete the workflow
            enriched_profile = EnrichedProfile(canonical_profile, companies)
            
            # Update final status
            status.status = WorkflowStatus.SUCCESS
            status.completed_at = datetime.now(timezone.utc)
            status.progress = {
                "stage": "completed",
                "step": 2,
                "total_steps": 2,
                "profile_fetched": True,
                "companies_fetched": len(companies),
                "companies_successful": enriched_profile.company_count
            }
            
            self.logger.info(
                "Profile processing workflow completed successfully",
                request_id=request_id,
                profile_id=canonical_profile.profile_id,
                companies_fetched=enriched_profile.company_count,
                execution_time_seconds=(
                    status.completed_at - status.started_at
                ).total_seconds()
            )
            
            return request_id, enriched_profile
            
        except Exception as e:
            # Update error status
            status.status = WorkflowStatus.FAILED
            status.completed_at = datetime.now(timezone.utc)
            status.error_message = str(e)
            
            self.logger.error(
                "Profile processing workflow failed",
                request_id=request_id,
                error=str(e),
                error_type=type(e).__name__
            )
            raise
    
    async def _fetch_companies_for_profile(
        self, 
        profile: CanonicalProfile, 
        request_id: str
    ) -> List[Optional[CompanyProfile]]:
        """
        Fetch company data for all experiences in a profile
        
        Args:
            profile: Canonical profile with experience entries
            request_id: Request ID for logging
            
        Returns:
            List of CompanyProfile objects (may contain None for failed fetches)
        """
        # Extract unique company URLs from experience entries
        company_urls = []
        for experience in profile.experiences:
            company_url = experience.company_linkedin_url
            if company_url and str(company_url) not in company_urls:
                company_urls.append(str(company_url))
        
        if not company_urls:
            self.logger.info(
                "No company URLs found in profile experiences",
                request_id=request_id,
                profile_id=profile.profile_id
            )
            return []
        
        self.logger.info(
            "Fetching companies for profile",
            request_id=request_id,
            profile_id=profile.profile_id,
            unique_companies=len(company_urls)
        )
        
        # Use batch fetch with delay (from blueprint: 10 seconds between requests)
        companies = await self.cassidy_client.batch_fetch_companies(
            company_urls=company_urls,
            delay_seconds=10.0
        )
        
        successful_count = sum(1 for c in companies if c is not None)
        self.logger.info(
            "Company fetch completed for profile",
            request_id=request_id,
            profile_id=profile.profile_id,
            total_requested=len(company_urls),
            successful=successful_count,
            failed=len(company_urls) - successful_count
        )
        
        return companies
    
    async def process_company(
        self, 
        company_url: str,
        request_id: Optional[str] = None
    ) -> Tuple[str, CompanyProfile]:
        """
        Process a single company profile ingestion
        
        Args:
            company_url: LinkedIn company URL to process
            request_id: Optional request ID for tracking
            
        Returns:
            Tuple of (request_id, company_profile)
            
        Raises:
            CassidyException: Various ingestion errors
        """
        if not request_id:
            request_id = str(uuid.uuid4())
        
        self.logger.info(
            "Starting company processing workflow",
            request_id=request_id,
            company_url=company_url
        )
        
        # Initialize status tracking
        status = IngestionStatus(
            request_id=request_id,
            status=WorkflowStatus.RUNNING,
            profile_url=company_url,  # Using profile_url field for company URL
            started_at=datetime.now(timezone.utc),
            progress={"stage": "company_fetch", "step": 1, "total_steps": 1}
        )
        self._active_requests[request_id] = status
        
        try:
            # Fetch company data
            company = await self.cassidy_client.fetch_company(company_url)
            
            # Update final status
            status.status = WorkflowStatus.SUCCESS
            status.completed_at = datetime.now(timezone.utc)
            status.progress = {"stage": "completed", "step": 1, "total_steps": 1}
            
            self.logger.info(
                "Company processing workflow completed successfully",
                request_id=request_id,
                company_name=company.company_name,
                execution_time_seconds=(
                    status.completed_at - status.started_at
                ).total_seconds()
            )
            
            return request_id, company
            
        except Exception as e:
            # Update error status
            status.status = WorkflowStatus.FAILED
            status.completed_at = datetime.now(timezone.utc)
            status.error_message = str(e)
            
            self.logger.error(
                "Company processing workflow failed",
                request_id=request_id,
                error=str(e),
                error_type=type(e).__name__
            )
            raise
    
    def get_request_status(self, request_id: str) -> Optional[IngestionStatus]:
        """
        Get status of a running or completed request
        
        Args:
            request_id: Request ID to check
            
        Returns:
            IngestionStatus if found, None otherwise
        """
        return self._active_requests.get(request_id)
    
    def list_active_requests(self) -> List[IngestionStatus]:
        """
        List all currently tracked requests
        
        Returns:
            List of IngestionStatus objects
        """
        return list(self._active_requests.values())
    
    def cleanup_completed_requests(self, max_age_hours: int = 24) -> int:
        """
        Clean up completed requests older than specified age
        
        Args:
            max_age_hours: Maximum age in hours for completed requests
            
        Returns:
            Number of requests cleaned up
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
        cleaned_count = 0
        
        # Find requests to clean up
        requests_to_remove = []
        for request_id, status in self._active_requests.items():
            if (status.status in [WorkflowStatus.SUCCESS, WorkflowStatus.FAILED] 
                and status.completed_at 
                and status.completed_at < cutoff_time):
                requests_to_remove.append(request_id)
        
        # Remove old requests
        for request_id in requests_to_remove:
            del self._active_requests[request_id]
            cleaned_count += 1
        
        if cleaned_count > 0:
            self.logger.info(
                "Cleaned up completed requests",
                cleaned_count=cleaned_count,
                max_age_hours=max_age_hours
            )
        
        return cleaned_count
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check health of the workflow system
        
        Returns:
            Dict with health check results
        """
        cassidy_health = await self.cassidy_client.health_check()
        
        active_requests = len([
            s for s in self._active_requests.values() 
            if s.status == WorkflowStatus.RUNNING
        ])
        
        return {
            "status": "healthy" if cassidy_health["status"] == "healthy" else "degraded",
            "cassidy_api": cassidy_health,
            "active_requests": active_requests,
            "total_tracked_requests": len(self._active_requests),
            "feature_flags": {
                "company_ingestion_enabled": settings.ENABLE_COMPANY_INGESTION,
                "async_processing_enabled": settings.ENABLE_ASYNC_PROCESSING,
            }
        }
