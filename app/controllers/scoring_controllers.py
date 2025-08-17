"""
V1.85 LLM Profile Scoring Controllers

Controllers for scoring API endpoints including profile scoring requests
and job status/retry management.
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional

from fastapi import HTTPException

from app.core.logging import LoggerMixin
from app.core.config import settings
from app.database.supabase_client import SupabaseClient
from app.services.scoring_job_service import ScoringJobService
from app.services.llm_scoring_service import LLMScoringService
from app.models.scoring import (
    ScoringRequest, ScoringResponse, JobRetryRequest,
    JobStatus, ScoringResultData, ScoringErrorData
)
from app.models.template_models import EnhancedScoringRequest
from app.services.template_service import TemplateService
from app.models.errors import ErrorResponse


class ProfileScoringController(LoggerMixin):
    """Controller for profile scoring request endpoints"""
    
    def __init__(self):
        self.db_client = SupabaseClient()
        self.job_service = ScoringJobService()
        self.llm_service = LLMScoringService()
        self.template_service = TemplateService(supabase_client=self.db_client)
        self._rate_limits = {}  # Simple in-memory rate limiting
    
    def _check_rate_limit(self, profile_id: str) -> bool:
        """
        Check if profile has exceeded rate limits
        
        Returns:
            bool: True if within limits, False if exceeded
        """
        now = datetime.now(timezone.utc)
        hour_ago = now - timedelta(hours=1)
        
        # Clean old entries
        self._rate_limits = {
            pid: requests for pid, requests in self._rate_limits.items()
            if any(req_time > hour_ago for req_time in requests)
        }
        
        # Check current profile
        if profile_id not in self._rate_limits:
            self._rate_limits[profile_id] = []
        
        # Filter to last hour
        self._rate_limits[profile_id] = [
            req_time for req_time in self._rate_limits[profile_id]
            if req_time > hour_ago
        ]
        
        # Check limit (10 per hour per profile)
        if len(self._rate_limits[profile_id]) >= 10:
            return False
        
        # Record this request
        self._rate_limits[profile_id].append(now)
        return True
    
    async def create_scoring_job(
        self, 
        profile_id: str, 
        request: ScoringRequest
    ) -> ScoringResponse:
        """
        Create a new scoring job for a profile
        
        Args:
            profile_id: UUID of profile to score
            request: Scoring request parameters
            
        Returns:
            ScoringResponse: Job creation response
            
        Raises:
            HTTPException: If validation fails or limits exceeded
        """
        self.logger.info(
            "Creating scoring job",
            profile_id=profile_id,
            model=request.model,
            prompt_length=len(request.prompt)
        )
        
        # Check rate limits
        if not self._check_rate_limit(profile_id):
            error_response = ErrorResponse(
                error_code="RATE_LIMIT_EXCEEDED",
                message="Rate limit exceeded for profile scoring",
                details={
                    "profile_id": profile_id,
                    "limit": "10 requests per hour per profile"
                }
            )
            raise HTTPException(
                status_code=429,
                detail=error_response.model_dump(),
                headers={"Retry-After": "3600"}
            )
        
        # Verify profile exists
        try:
            profile = await self.db_client.get_profile_by_id(profile_id)
            if not profile:
                error_response = ErrorResponse(
                    error_code="PROFILE_NOT_FOUND",
                    message=f"Profile with ID {profile_id} not found",
                    details={"profile_id": profile_id}
                )
                raise HTTPException(
                    status_code=404,
                    detail=error_response.model_dump()
                )
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(
                "Profile validation failed",
                profile_id=profile_id,
                error=str(e),
                error_type=type(e).__name__
            )
            error_response = ErrorResponse(
                error_code="PROFILE_ACCESS_ERROR",
                message="Unable to verify profile access",
                details={
                    "profile_id": profile_id,
                    "error": str(e)
                }
            )
            raise HTTPException(
                status_code=500,
                detail=error_response.model_dump()
            )
        
        # Create scoring job
        try:
            job_id = await self.job_service.create_job(
                profile_id=profile_id,
                prompt=request.prompt,
                model_name=request.model
            )
            
            # Start background processing (don't await)
            asyncio.create_task(self._process_scoring_job(job_id, request))
            
            # Return immediate response
            estimated_completion = datetime.now(timezone.utc) + timedelta(minutes=2)
            
            response = ScoringResponse(
                job_id=job_id,
                status=JobStatus.PENDING,
                profile_id=profile_id,
                created_at=datetime.now(timezone.utc)
            )
            
            self.logger.info(
                "Scoring job created successfully",
                job_id=job_id,
                profile_id=profile_id
            )
            
            return response
            
        except Exception as e:
            self.logger.error(
                "Failed to create scoring job",
                profile_id=profile_id,
                error=str(e),
                error_type=type(e).__name__
            )
            error_response = ErrorResponse(
                error_code="JOB_CREATION_FAILED",
                message="Failed to create scoring job",
                details={
                    "profile_id": profile_id,
                    "error": str(e)
                }
            )
            raise HTTPException(
                status_code=500,
                detail=error_response.model_dump()
            )
    
    async def _process_scoring_job(self, job_id: str, request: ScoringRequest):
        """
        Background task to process scoring job with LLM
        
        Args:
            job_id: Job identifier
            request: Original scoring request
        """
        try:
            self.logger.info("Starting background scoring job processing", job_id=job_id)
            
            # Process with LLM service (it will handle status updates)
            await self.llm_service.process_scoring_job(
                job_id=job_id,
                max_tokens=request.max_tokens,
                temperature=request.temperature
            )
            
            self.logger.info("Scoring job completed successfully", job_id=job_id)
            
        except Exception as e:
            self.logger.error(
                "Background scoring job failed",
                job_id=job_id,
                error=str(e),
                error_type=type(e).__name__
            )
            # LLMScoringService will handle marking job as failed
    
    async def create_enhanced_scoring_job(
        self,
        profile_id: str,
        request: EnhancedScoringRequest
    ) -> ScoringResponse:
        """
        Create a new scoring job supporting both template-based and prompt-based scoring
        
        Args:
            profile_id: UUID of profile to score
            request: Enhanced scoring request with template_id OR prompt
            
        Returns:
            ScoringResponse: Job creation response
            
        Raises:
            HTTPException: If validation fails or limits exceeded
        """
        # Determine if this is template-based or prompt-based scoring
        template_id = None
        prompt = None
        
        if request.template_id:
            self.logger.info(
                "Creating template-based scoring job",
                profile_id=profile_id,
                template_id=str(request.template_id)
            )
            
            # Resolve template to get prompt text
            try:
                template = await self.template_service.get_template_by_id(str(request.template_id))
                if not template:
                    error_response = ErrorResponse(
                        error_code="TEMPLATE_NOT_FOUND",
                        message=f"Template with ID {request.template_id} not found",
                        details={"template_id": str(request.template_id)}
                    )
                    raise HTTPException(
                        status_code=404,
                        detail=error_response.model_dump()
                    )
                
                if not template.is_active:
                    error_response = ErrorResponse(
                        error_code="TEMPLATE_INACTIVE",
                        message=f"Template {request.template_id} is not active",
                        details={"template_id": str(request.template_id)}
                    )
                    raise HTTPException(
                        status_code=400,
                        detail=error_response.model_dump()
                    )
                
                template_id = str(request.template_id)
                prompt = template.prompt_text
                
                self.logger.info(
                    "Template resolved successfully",
                    template_id=template_id,
                    template_name=template.name,
                    template_category=template.category,
                    prompt_length=len(prompt)
                )
                
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(
                    "Failed to resolve template",
                    template_id=str(request.template_id),
                    error=str(e),
                    error_type=type(e).__name__
                )
                error_response = ErrorResponse(
                    error_code="TEMPLATE_RESOLUTION_ERROR",
                    message="Failed to resolve template",
                    details={
                        "template_id": str(request.template_id),
                        "error": str(e)
                    }
                )
                raise HTTPException(
                    status_code=500,
                    detail=error_response.model_dump()
                )
        
        else:
            # Prompt-based scoring (backward compatibility)
            prompt = request.prompt
            self.logger.info(
                "Creating prompt-based scoring job",
                profile_id=profile_id,
                prompt_length=len(prompt)
            )
        
        # Check rate limits
        if not self._check_rate_limit(profile_id):
            error_response = ErrorResponse(
                error_code="RATE_LIMIT_EXCEEDED",
                message="Rate limit exceeded for profile scoring",
                details={
                    "profile_id": profile_id,
                    "limit": "10 requests per hour per profile"
                }
            )
            raise HTTPException(
                status_code=429,
                detail=error_response.model_dump(),
                headers={"Retry-After": "3600"}
            )
        
        # Verify profile exists
        try:
            profile = await self.db_client.get_profile_by_id(profile_id)
            if not profile:
                error_response = ErrorResponse(
                    error_code="PROFILE_NOT_FOUND",
                    message=f"Profile with ID {profile_id} not found",
                    details={"profile_id": profile_id}
                )
                raise HTTPException(
                    status_code=404,
                    detail=error_response.model_dump()
                )
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(
                "Profile validation failed",
                profile_id=profile_id,
                error=str(e),
                error_type=type(e).__name__
            )
            error_response = ErrorResponse(
                error_code="PROFILE_ACCESS_ERROR",
                message="Unable to verify profile access",
                details={
                    "profile_id": profile_id,
                    "error": str(e)
                }
            )
            raise HTTPException(
                status_code=500,
                detail=error_response.model_dump()
            )
        
        # Create scoring job with template_id tracking
        try:
            job_id = await self.job_service.create_job(
                profile_id=profile_id,
                prompt=prompt,
                model_name=getattr(request, 'model', 'gpt-3.5-turbo'),
                template_id=template_id
            )
            
            # Convert enhanced request to legacy format for background processing
            legacy_request = ScoringRequest(
                prompt=prompt,
                model=getattr(request, 'model', 'gpt-3.5-turbo'),
                max_tokens=getattr(request, 'max_tokens', 2000),
                temperature=getattr(request, 'temperature', 0.1)
            )
            
            # Start background processing (don't await)
            asyncio.create_task(self._process_scoring_job(job_id, legacy_request))
            
            # Return immediate response
            response = ScoringResponse(
                job_id=job_id,
                status=JobStatus.PENDING,
                profile_id=profile_id,
                created_at=datetime.now(timezone.utc)
            )
            
            self.logger.info(
                "Enhanced scoring job created successfully",
                job_id=job_id,
                profile_id=profile_id,
                template_id=template_id,
                scoring_type="template-based" if template_id else "prompt-based"
            )
            
            return response
            
        except Exception as e:
            self.logger.error(
                "Failed to create enhanced scoring job",
                profile_id=profile_id,
                template_id=template_id,
                error=str(e),
                error_type=type(e).__name__
            )
            error_response = ErrorResponse(
                error_code="JOB_CREATION_FAILED",
                message="Failed to create scoring job",
                details={
                    "profile_id": profile_id,
                    "template_id": template_id,
                    "error": str(e)
                }
            )
            raise HTTPException(
                status_code=500,
                detail=error_response.model_dump()
            )


class ScoringJobController(LoggerMixin):
    """Controller for scoring job status and retry endpoints"""
    
    def __init__(self):
        self.job_service = ScoringJobService()
        self.llm_service = LLMScoringService()
    
    async def get_job_status(self, job_id: str) -> ScoringResponse:
        """
        Get scoring job status and results
        
        Args:
            job_id: Job identifier
            
        Returns:
            ScoringResponse: Job status and results
            
        Raises:
            HTTPException: If job not found
        """
        self.logger.debug("Retrieving job status", job_id=job_id)
        
        try:
            job = await self.job_service.get_job(job_id)
            if not job:
                error_response = ErrorResponse(
                    error_code="JOB_NOT_FOUND",
                    message=f"Scoring job with ID {job_id} not found",
                    details={"job_id": job_id}
                )
                raise HTTPException(
                    status_code=404,
                    detail=error_response.model_dump()
                )
            
            # Build response based on job status
            response_data = {
                "job_id": job.id,
                "status": job.status,
                "profile_id": job.profile_id,
                "created_at": job.created_at,
                "updated_at": job.updated_at
            }
            
            if job.status == JobStatus.COMPLETED:
                if job.llm_response and job.parsed_score:
                    response_data["result"] = ScoringResultData(
                        llm_response=job.llm_response,
                        parsed_score=job.parsed_score,
                        model_used=job.model_name,
                        tokens_used=job.llm_response.get("usage", {}).get("total_tokens", 0)
                    )
                response_data["completed_at"] = job.completed_at
            
            elif job.status == JobStatus.FAILED:
                response_data["error"] = ScoringErrorData(
                    code="LLM_PROCESSING_ERROR",
                    message=job.error_message or "Job processing failed",
                    retryable=job.retry_count < 3
                )
                response_data["failed_at"] = job.updated_at
            
            elif job.status == JobStatus.PROCESSING:
                response_data["started_at"] = job.started_at
            
            response = ScoringResponse(**response_data)
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(
                "Failed to retrieve job status",
                job_id=job_id,
                error=str(e),
                error_type=type(e).__name__
            )
            error_response = ErrorResponse(
                error_code="JOB_RETRIEVAL_ERROR",
                message="Failed to retrieve job status",
                details={
                    "job_id": job_id,
                    "error": str(e)
                }
            )
            raise HTTPException(
                status_code=500,
                detail=error_response.model_dump()
            )
    
    async def retry_job(self, job_id: str, retry_request: Optional[JobRetryRequest] = None) -> ScoringResponse:
        """
        Retry a failed scoring job
        
        Args:
            job_id: Job identifier
            retry_request: Optional retry parameters
            
        Returns:
            ScoringResponse: Retry response
            
        Raises:
            HTTPException: If job not found or not retryable
        """
        self.logger.info("Retrying scoring job", job_id=job_id)
        
        try:
            job = await self.job_service.get_job(job_id)
            if not job:
                error_response = ErrorResponse(
                    error_code="JOB_NOT_FOUND",
                    message=f"Scoring job with ID {job_id} not found",
                    details={"job_id": job_id}
                )
                raise HTTPException(
                    status_code=404,
                    detail=error_response.model_dump()
                )
            
            # Validate job can be retried
            if job.status != JobStatus.FAILED:
                error_response = ErrorResponse(
                    error_code="JOB_NOT_RETRYABLE",
                    message=f"Job status '{job.status}' cannot be retried",
                    details={
                        "job_id": job_id,
                        "current_status": job.status,
                        "required_status": "failed"
                    }
                )
                raise HTTPException(
                    status_code=400,
                    detail=error_response.model_dump()
                )
            
            if job.retry_count >= 3:
                error_response = ErrorResponse(
                    error_code="RETRY_LIMIT_EXCEEDED",
                    message="Maximum retry limit exceeded",
                    details={
                        "job_id": job_id,
                        "retry_count": job.retry_count,
                        "max_retries": 3
                    }
                )
                raise HTTPException(
                    status_code=400,
                    detail=error_response.model_dump()
                )
            
            # Reset job to pending and increment retry count
            await self.job_service.retry_job(job_id)
            
            # Start background processing with new parameters if provided
            request_params = {
                "max_tokens": retry_request.max_tokens if retry_request and retry_request.max_tokens else 2000,
                "temperature": 0.1
            }
            
            # Update model if specified in retry
            if retry_request and retry_request.model:
                await self.job_service.update_job_model(job_id, retry_request.model)
            
            asyncio.create_task(self._process_retry_job(job_id, request_params))
            
            return ScoringResponse(
                job_id=job_id,
                status=JobStatus.PENDING,
                profile_id=job.profile_id,
                created_at=job.created_at
            )
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(
                "Failed to retry job",
                job_id=job_id,
                error=str(e),
                error_type=type(e).__name__
            )
            error_response = ErrorResponse(
                error_code="JOB_RETRY_ERROR",
                message="Failed to retry job",
                details={
                    "job_id": job_id,
                    "error": str(e)
                }
            )
            raise HTTPException(
                status_code=500,
                detail=error_response.model_dump()
            )
    
    async def _process_retry_job(self, job_id: str, request_params: Dict[str, Any]):
        """
        Background task to process retried scoring job
        
        Args:
            job_id: Job identifier
            request_params: Request parameters for retry
        """
        try:
            self.logger.info("Starting retry job processing", job_id=job_id)
            
            # Update status to processing
            await self.job_service.update_job_status(
                job_id=job_id,
                status=JobStatus.PROCESSING,
                started_at=datetime.now(timezone.utc)
            )
            
            # Process with LLM service
            await self.llm_service.process_scoring_job(
                job_id=job_id,
                max_tokens=request_params["max_tokens"],
                temperature=request_params["temperature"]
            )
            
            self.logger.info("Retry job completed successfully", job_id=job_id)
            
        except Exception as e:
            self.logger.error(
                "Retry job processing failed",
                job_id=job_id,
                error=str(e),
                error_type=type(e).__name__
            )
