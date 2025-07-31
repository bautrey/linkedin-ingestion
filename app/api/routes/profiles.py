"""
Profile API endpoints
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any
import uuid
from datetime import datetime

from app.core.logging import get_logger
from app.cassidy.workflows import LinkedInWorkflow, EnrichedProfile
from app.cassidy.models import (
    ProfileIngestionRequest,
    IngestionResponse,
    IngestionStatus,
    WorkflowStatus,
    ErrorResponse,
)
from app.cassidy.exceptions import CassidyException

logger = get_logger(__name__)
router = APIRouter()

# Global workflow instance for handling requests
workflow = LinkedInWorkflow()


@router.post("/profiles/ingest", response_model=IngestionResponse)
async def ingest_profile(
    request: ProfileIngestionRequest,
    background_tasks: BackgroundTasks
) -> IngestionResponse:
    """
    Ingest a LinkedIn profile with optional company data enrichment
    
    This endpoint initiates the profile ingestion process and returns immediately
    with a request ID that can be used to track progress.
    
    Args:
        request: Profile ingestion request with LinkedIn URL and options
        background_tasks: FastAPI background tasks for async processing
        
    Returns:
        IngestionResponse with request ID and status URL
        
    Raises:
        HTTPException: For validation errors or system failures
    """
    request_id = str(uuid.uuid4())
    
    logger.info(
        "Profile ingestion requested",
        request_id=request_id,
        linkedin_url=str(request.linkedin_url),
        include_companies=request.include_companies
    )
    
    try:
        # For synchronous processing (simple case)
        if not request.include_companies:
            logger.info("Processing profile synchronously", request_id=request_id)
            request_id, enriched_profile = await workflow.process_profile(request, request_id)
            
            return IngestionResponse(
                request_id=request_id,
                status=WorkflowStatus.SUCCESS,
                message="Profile ingested successfully",
                status_url=f"/api/v1/profiles/status/{request_id}"
            )
        
        # For asynchronous processing (with companies)
        else:
            logger.info("Processing profile asynchronously", request_id=request_id)
            
            # Add to background tasks
            background_tasks.add_task(
                _process_profile_background,
                request,
                request_id
            )
            
            return IngestionResponse(
                request_id=request_id,
                status=WorkflowStatus.RUNNING,
                message="Profile ingestion started. Check status for progress.",
                estimated_completion_time=datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
                status_url=f"/api/v1/profiles/status/{request_id}"
            )
            
    except CassidyException as e:
        logger.error(
            "Cassidy error during profile ingestion",
            request_id=request_id,
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(
            status_code=422,
            detail={
                "error": "ingestion_failed",
                "message": f"Failed to ingest LinkedIn profile: {str(e)}",
                "request_id": request_id
            }
        )
        
    except Exception as e:
        logger.error(
            "Unexpected error during profile ingestion",
            request_id=request_id,
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_error", 
                "message": "An unexpected error occurred during profile ingestion",
                "request_id": request_id
            }
        )


@router.get("/profiles/status/{request_id}", response_model=IngestionStatus)
async def get_ingestion_status(request_id: str) -> IngestionStatus:
    """
    Get the status of a profile ingestion request
    
    Args:
        request_id: Unique request identifier from ingestion response
        
    Returns:
        IngestionStatus with current progress and details
        
    Raises:
        HTTPException: If request ID is not found
    """
    logger.info("Status check requested", request_id=request_id)
    
    status = workflow.get_request_status(request_id)
    
    if not status:
        logger.warning("Request ID not found", request_id=request_id)
        raise HTTPException(
            status_code=404,
            detail={
                "error": "request_not_found",
                "message": f"No ingestion request found with ID: {request_id}",
                "request_id": request_id
            }
        )
    
    logger.info(
        "Status retrieved",
        request_id=request_id,
        status=status.status.value,
        progress=status.progress
    )
    
    return status


@router.get("/profiles/requests")
async def list_active_requests() -> Dict[str, Any]:
    """
    List all currently tracked ingestion requests
    
    Returns:
        Dict with active requests summary
    """
    logger.info("Active requests list requested")
    
    requests = workflow.list_active_requests()
    
    # Group by status
    status_summary = {}
    for request in requests:
        status = request.status.value
        if status not in status_summary:
            status_summary[status] = 0
        status_summary[status] += 1
    
    return {
        "total_requests": len(requests),
        "status_summary": status_summary,
        "requests": [
            {
                "request_id": req.request_id,
                "status": req.status.value,
                "profile_url": str(req.profile_url),
                "started_at": req.started_at.isoformat(),
                "completed_at": req.completed_at.isoformat() if req.completed_at else None,
                "progress": req.progress
            }
            for req in requests
        ]
    }


@router.delete("/profiles/requests/cleanup")
async def cleanup_old_requests(max_age_hours: int = 24) -> Dict[str, Any]:
    """
    Clean up completed requests older than specified age
    
    Args:
        max_age_hours: Maximum age in hours for completed requests (default 24)
        
    Returns:
        Dict with cleanup summary
    """
    logger.info("Request cleanup initiated", max_age_hours=max_age_hours)
    
    cleaned_count = workflow.cleanup_completed_requests(max_age_hours)
    
    return {
        "message": "Cleanup completed successfully",
        "cleaned_requests": cleaned_count,
        "max_age_hours": max_age_hours
    }


async def _process_profile_background(
    request: ProfileIngestionRequest,
    request_id: str
) -> None:
    """
    Background task to process profile ingestion
    
    Args:
        request: Profile ingestion request
        request_id: Unique request identifier
    """
    try:
        logger.info("Starting background profile processing", request_id=request_id)
        
        request_id, enriched_profile = await workflow.process_profile(request, request_id)
        
        logger.info(
            "Background profile processing completed",
            request_id=request_id,
            profile_id=enriched_profile.profile.profile_id,
            companies_fetched=enriched_profile.company_count
        )
        
    except Exception as e:
        logger.error(
            "Background profile processing failed",
            request_id=request_id,
            error=str(e),
            error_type=type(e).__name__
        )
