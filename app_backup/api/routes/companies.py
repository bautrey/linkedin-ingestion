"""
Company API endpoints
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import uuid

from app.core.logging import get_logger
from app.cassidy.workflows import LinkedInWorkflow
from app.cassidy.models import (
    CompanyIngestionRequest,
    IngestionResponse,
    IngestionStatus,
    WorkflowStatus,
)
from app.cassidy.exceptions import CassidyException

logger = get_logger(__name__)
router = APIRouter()

# Global workflow instance for handling requests
workflow = LinkedInWorkflow()


@router.post("/companies/ingest", response_model=IngestionResponse)
async def ingest_company(
    request: CompanyIngestionRequest
) -> IngestionResponse:
    """
    Ingest a LinkedIn company profile
    
    Args:
        request: Company ingestion request with LinkedIn URL
        
    Returns:
        IngestionResponse with request ID and status
        
    Raises:
        HTTPException: For validation errors or system failures
    """
    request_id = str(uuid.uuid4())
    
    logger.info(
        "Company ingestion requested",
        request_id=request_id,
        linkedin_url=str(request.linkedin_url)
    )
    
    try:
        # Process company synchronously (simpler than profiles)
        request_id, company = await workflow.process_company(
            str(request.linkedin_url), 
            request_id
        )
        
        logger.info(
            "Company ingestion completed",
            request_id=request_id,
            company_name=company.company_name
        )
        
        return IngestionResponse(
            request_id=request_id,
            status=WorkflowStatus.SUCCESS,
            message=f"Company '{company.company_name}' ingested successfully",
            status_url=f"/api/v1/companies/status/{request_id}"
        )
        
    except CassidyException as e:
        logger.error(
            "Cassidy error during company ingestion",
            request_id=request_id,
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(
            status_code=422,
            detail={
                "error": "ingestion_failed",
                "message": f"Failed to ingest LinkedIn company: {str(e)}",
                "request_id": request_id
            }
        )
        
    except Exception as e:
        logger.error(
            "Unexpected error during company ingestion",
            request_id=request_id,
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_error",
                "message": "An unexpected error occurred during company ingestion",
                "request_id": request_id
            }
        )


@router.get("/companies/status/{request_id}", response_model=IngestionStatus)
async def get_company_status(request_id: str) -> IngestionStatus:
    """
    Get the status of a company ingestion request
    
    Args:
        request_id: Unique request identifier from ingestion response
        
    Returns:
        IngestionStatus with current progress and details
        
    Raises:
        HTTPException: If request ID is not found
    """
    logger.info("Company status check requested", request_id=request_id)
    
    status = workflow.get_request_status(request_id)
    
    if not status:
        logger.warning("Company request ID not found", request_id=request_id)
        raise HTTPException(
            status_code=404,
            detail={
                "error": "request_not_found",
                "message": f"No company ingestion request found with ID: {request_id}",
                "request_id": request_id
            }
        )
    
    return status


@router.get("/companies/health")
async def company_workflow_health() -> Dict[str, Any]:
    """
    Check health of company ingestion workflow
    
    Returns:
        Dict with workflow health status
    """
    logger.info("Company workflow health check requested")
    
    try:
        health_result = await workflow.health_check()
        return {
            "status": "healthy",
            "message": "Company workflow is operational",
            "details": health_result
        }
        
    except Exception as e:
        logger.error(
            "Company workflow health check failed",
            error=str(e),
            error_type=type(e).__name__
        )
        return {
            "status": "unhealthy",
            "message": "Company workflow has issues",
            "error": str(e)
        }
