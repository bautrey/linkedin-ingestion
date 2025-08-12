"""
V1.85 LLM Scoring Job Service

Database service for managing scoring jobs with Supabase backend.
Provides CRUD operations and job status management.
"""

import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta

from app.core.logging import LoggerMixin
from app.core.config import settings
from app.database.supabase_client import SupabaseClient
from app.models.scoring import ScoringJob, JobStatus


class ScoringJobService(LoggerMixin):
    """
    Service for managing scoring jobs in the database
    
    Provides async CRUD operations for scoring jobs using Supabase client patterns.
    """
    
    def __init__(self):
        self.supabase_client = SupabaseClient()
        # For testing purposes, allow client override
        self.client = None
        self._client_initialized = False
    
    async def _ensure_client(self):
        """Ensure Supabase client is initialized"""
        if not self._client_initialized:
            if self.client is None:  # Use real client if not overridden for testing
                await self.supabase_client._ensure_client()
                self.client = self.supabase_client.client
            self._client_initialized = True
    
    async def create_job(
        self,
        profile_id: str,
        prompt: str,
        model_name: str = "gpt-3.5-turbo"
    ) -> str:
        """
        Create a new scoring job
        
        Args:
            profile_id: UUID of the profile to score
            prompt: LLM evaluation prompt
            model_name: OpenAI model to use
            
        Returns:
            str: Created job ID
            
        Raises:
            Exception: If profile_id doesn't exist or database error occurs
        """
        await self._ensure_client()
        
        job_id = str(uuid.uuid4())
        job_data = {
            "id": job_id,
            "profile_id": profile_id,
            "status": JobStatus.PENDING,
            "prompt": prompt.strip(),
            "model_name": model_name,
            "retry_count": 0,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        self.logger.info(
            "Creating scoring job",
            job_id=job_id,
            profile_id=profile_id,
            model_name=model_name,
            prompt_length=len(prompt)
        )
        
        try:
            table = self.client.table("scoring_jobs")
            result = await table.insert(job_data).execute()
            
            if not result.data:
                raise Exception("Failed to create scoring job - no data returned")
            
            self.logger.info(
                "Scoring job created successfully",
                job_id=job_id,
                profile_id=profile_id
            )
            
            return job_id
            
        except Exception as e:
            self.logger.error(
                "Failed to create scoring job",
                job_id=job_id,
                profile_id=profile_id,
                error=str(e),
                error_type=type(e).__name__
            )
            raise
    
    async def get_job(self, job_id: str) -> Optional[ScoringJob]:
        """
        Retrieve a scoring job by ID
        
        Args:
            job_id: Job identifier
            
        Returns:
            ScoringJob: Job data or None if not found
        """
        await self._ensure_client()
        
        try:
            table = self.client.table("scoring_jobs")
            result = await table.select("*").eq("id", job_id).execute()
            
            if not result.data:
                self.logger.warning("Scoring job not found", job_id=job_id)
                return None
            
            job_data = result.data[0]
            
            # Convert timestamps from ISO strings back to datetime objects
            for timestamp_field in ['created_at', 'updated_at', 'started_at', 'completed_at']:
                if job_data.get(timestamp_field):
                    try:
                        job_data[timestamp_field] = datetime.fromisoformat(
                            job_data[timestamp_field].replace('Z', '+00:00')
                        )
                    except (ValueError, AttributeError):
                        # Handle cases where timestamp is already datetime or malformed
                        pass
            
            job = ScoringJob(**job_data)
            
            self.logger.debug(
                "Retrieved scoring job",
                job_id=job_id,
                status=job.status,
                profile_id=job.profile_id
            )
            
            return job
            
        except Exception as e:
            self.logger.error(
                "Failed to retrieve scoring job",
                job_id=job_id,
                error=str(e),
                error_type=type(e).__name__
            )
            raise
    
    async def update_job_status(
        self,
        job_id: str,
        status: JobStatus,
        started_at: Optional[datetime] = None
    ) -> bool:
        """
        Update job status and optionally set started_at timestamp
        
        Args:
            job_id: Job identifier
            status: New job status
            started_at: Optional processing start time
            
        Returns:
            bool: True if update succeeded, False if job not found
        """
        await self._ensure_client()
        
        update_data = {
            "status": status.value,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        if started_at:
            update_data["started_at"] = started_at.isoformat()
        
        try:
            table = self.client.table("scoring_jobs")
            result = await table.update(update_data).eq("id", job_id).execute()
            
            if not result.data:
                self.logger.warning(
                    "Job not found for status update",
                    job_id=job_id,
                    status=status
                )
                return False
            
            self.logger.info(
                "Updated job status",
                job_id=job_id,
                status=status,
                has_start_time=started_at is not None
            )
            
            return True
            
        except Exception as e:
            self.logger.error(
                "Failed to update job status",
                job_id=job_id,
                status=status,
                error=str(e)
            )
            raise
    
    async def complete_job(
        self,
        job_id: str,
        llm_response: Dict[str, Any],
        parsed_score: Dict[str, Any]
    ) -> bool:
        """
        Mark job as completed with LLM response data
        
        Args:
            job_id: Job identifier
            llm_response: Raw LLM response
            parsed_score: Structured scoring results
            
        Returns:
            bool: True if update succeeded, False if job not found
        """
        await self._ensure_client()
        
        completion_time = datetime.now(timezone.utc).isoformat()
        update_data = {
            "status": JobStatus.COMPLETED.value,
            "llm_response": llm_response,
            "parsed_score": parsed_score,
            "completed_at": completion_time,
            "updated_at": completion_time
        }
        
        try:
            table = self.client.table("scoring_jobs")
            result = await table.update(update_data).eq("id", job_id).execute()
            
            if not result.data:
                self.logger.warning("Job not found for completion", job_id=job_id)
                return False
            
            self.logger.info(
                "Job completed successfully",
                job_id=job_id,
                has_llm_response=bool(llm_response),
                has_parsed_score=bool(parsed_score)
            )
            
            return True
            
        except Exception as e:
            self.logger.error(
                "Failed to complete job",
                job_id=job_id,
                error=str(e)
            )
            raise
    
    async def fail_job(
        self,
        job_id: str,
        error_message: str
    ) -> bool:
        """
        Mark job as failed with error message
        
        Args:
            job_id: Job identifier
            error_message: Error description
            
        Returns:
            bool: True if update succeeded, False if job not found
        """
        await self._ensure_client()
        
        update_data = {
            "status": JobStatus.FAILED.value,
            "error_message": error_message,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        try:
            table = self.client.table("scoring_jobs")
            result = await table.update(update_data).eq("id", job_id).execute()
            
            if not result.data:
                self.logger.warning("Job not found for failure", job_id=job_id)
                return False
            
            self.logger.warning(
                "Job failed",
                job_id=job_id,
                error_message=error_message
            )
            
            return True
            
        except Exception as e:
            self.logger.error(
                "Failed to update job failure",
                job_id=job_id,
                error=str(e)
            )
            raise
    
    async def increment_retry_count(self, job_id: str) -> bool:
        """
        Increment retry count and reset job to pending status
        
        Args:
            job_id: Job identifier
            
        Returns:
            bool: True if update succeeded, False if job not found
        """
        await self._ensure_client()
        
        # Use raw SQL to increment retry_count atomically
        update_data = {
            "retry_count": "retry_count + 1",  # This will be handled as raw SQL
            "status": JobStatus.PENDING.value,
            "error_message": None,  # Clear previous error
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        try:
            table = self.client.table("scoring_jobs")
            # Note: Supabase client might require special handling for raw SQL increments
            # For now, we'll use a simpler approach by fetching and updating
            
            # First, get current retry count
            current_result = await table.select("retry_count").eq("id", job_id).execute()
            if not current_result.data:
                self.logger.warning("Job not found for retry", job_id=job_id)
                return False
            
            current_retry_count = current_result.data[0]["retry_count"] or 0
            new_retry_count = current_retry_count + 1
            
            # Update with incremented count
            update_data["retry_count"] = new_retry_count
            result = await table.update(update_data).eq("id", job_id).execute()
            
            if not result.data:
                self.logger.warning("Job not found for retry update", job_id=job_id)
                return False
            
            self.logger.info(
                "Job retry count incremented",
                job_id=job_id,
                retry_count=new_retry_count
            )
            
            return True
            
        except Exception as e:
            self.logger.error(
                "Failed to increment retry count",
                job_id=job_id,
                error=str(e)
            )
            raise
    
    async def get_jobs_by_profile(
        self,
        profile_id: str,
        limit: int = 50
    ) -> List[ScoringJob]:
        """
        Get all scoring jobs for a specific profile
        
        Args:
            profile_id: Profile UUID
            limit: Maximum number of jobs to return
            
        Returns:
            List[ScoringJob]: List of jobs for the profile
        """
        await self._ensure_client()
        
        try:
            table = self.client.table("scoring_jobs")
            result = await table.select("*").eq("profile_id", profile_id).order("created_at", desc=True).limit(limit).execute()
            
            if not result.data:
                self.logger.debug("No jobs found for profile", profile_id=profile_id)
                return []
            
            jobs = []
            for job_data in result.data:
                # Convert timestamps
                for timestamp_field in ['created_at', 'updated_at', 'started_at', 'completed_at']:
                    if job_data.get(timestamp_field):
                        try:
                            job_data[timestamp_field] = datetime.fromisoformat(
                                job_data[timestamp_field].replace('Z', '+00:00')
                            )
                        except (ValueError, AttributeError):
                            pass
                
                jobs.append(ScoringJob(**job_data))
            
            self.logger.debug(
                "Retrieved profile jobs",
                profile_id=profile_id,
                job_count=len(jobs)
            )
            
            return jobs
            
        except Exception as e:
            self.logger.error(
                "Failed to retrieve profile jobs",
                profile_id=profile_id,
                error=str(e)
            )
            raise
    
    async def get_pending_jobs(self, limit: int = 100) -> List[ScoringJob]:
        """
        Get pending jobs for background processing
        
        Args:
            limit: Maximum number of jobs to return
            
        Returns:
            List[ScoringJob]: List of pending jobs
        """
        await self._ensure_client()
        
        try:
            table = self.client.table("scoring_jobs")
            result = await table.select("*").eq("status", JobStatus.PENDING.value).order("created_at", desc=False).limit(limit).execute()
            
            if not result.data:
                return []
            
            jobs = []
            for job_data in result.data:
                # Convert timestamps
                for timestamp_field in ['created_at', 'updated_at', 'started_at', 'completed_at']:
                    if job_data.get(timestamp_field):
                        try:
                            job_data[timestamp_field] = datetime.fromisoformat(
                                job_data[timestamp_field].replace('Z', '+00:00')
                            )
                        except (ValueError, AttributeError):
                            pass
                
                jobs.append(ScoringJob(**job_data))
            
            self.logger.debug("Retrieved pending jobs", job_count=len(jobs))
            return jobs
            
        except Exception as e:
            self.logger.error(
                "Failed to retrieve pending jobs",
                error=str(e)
            )
            raise
    
    async def cleanup_old_jobs(self, days_old: int = 7) -> int:
        """
        Clean up completed and failed jobs older than specified days
        
        Args:
            days_old: Number of days after which to delete jobs
            
        Returns:
            int: Number of jobs deleted
        """
        await self._ensure_client()
        
        cutoff_date = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        ) - timedelta(days=days_old)
        
        try:
            table = self.client.table("scoring_jobs")
            
            # Delete old completed and failed jobs
            result = await table.delete().in_(
                "status", [JobStatus.COMPLETED.value, JobStatus.FAILED.value]
            ).lt("created_at", cutoff_date.isoformat()).execute()
            
            deleted_count = len(result.data) if result.data else 0
            
            self.logger.info(
                "Cleaned up old scoring jobs",
                deleted_count=deleted_count,
                cutoff_date=cutoff_date.isoformat()
            )
            
            return deleted_count
            
        except Exception as e:
            self.logger.error(
                "Failed to cleanup old jobs",
                error=str(e)
            )
            raise
    
    async def retry_job(self, job_id: str) -> bool:
        """
        Reset job to pending and increment retry count
        
        Args:
            job_id: Job identifier
            
        Returns:
            bool: True if update succeeded, False if job not found
        """
        return await self.increment_retry_count(job_id)
    
    async def update_job_model(self, job_id: str, model_name: str) -> bool:
        """
        Update the model name for a job
        
        Args:
            job_id: Job identifier
            model_name: New model name
            
        Returns:
            bool: True if update succeeded, False if job not found
        """
        await self._ensure_client()
        
        update_data = {
            "model_name": model_name,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        try:
            table = self.client.table("scoring_jobs")
            result = await table.update(update_data).eq("id", job_id).execute()
            
            if not result.data:
                self.logger.warning("Job not found for model update", job_id=job_id)
                return False
            
            self.logger.info(
                "Job model updated",
                job_id=job_id,
                model_name=model_name
            )
            
            return True
            
        except Exception as e:
            self.logger.error(
                "Failed to update job model",
                job_id=job_id,
                error=str(e)
            )
            raise
