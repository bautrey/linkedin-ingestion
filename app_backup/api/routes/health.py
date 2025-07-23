"""
Health check API endpoints
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Dict, Any
import asyncio
from datetime import datetime

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    version: str
    timestamp: datetime
    environment: str
    checks: Dict[str, Any] = {}


class ServiceCheck(BaseModel):
    """Individual service check result"""
    status: str
    response_time_ms: float
    error: str = None


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Basic health check endpoint
    
    Returns service status and version information
    """
    logger.info("Health check requested")
    
    return HealthResponse(
        status="healthy",
        version=settings.VERSION,
        timestamp=datetime.utcnow(),
        environment=settings.ENVIRONMENT,
    )


@router.get("/health/detailed", response_model=HealthResponse)
async def detailed_health_check():
    """
    Detailed health check with dependency verification
    
    Checks external service connectivity and database status
    """
    logger.info("Detailed health check requested")
    
    checks = {}
    overall_status = "healthy"
    
    # Check Cassidy API connectivity
    cassidy_check = await _check_cassidy_connectivity()
    checks["cassidy"] = cassidy_check
    if cassidy_check.status != "healthy":
        overall_status = "degraded"
    
    # Check database connectivity
    database_check = await _check_database_connectivity()
    checks["database"] = database_check
    if database_check.status != "healthy":
        overall_status = "unhealthy"
    
    return HealthResponse(
        status=overall_status,
        version=settings.VERSION,
        timestamp=datetime.utcnow(),
        environment=settings.ENVIRONMENT,
        checks=checks,
    )


async def _check_cassidy_connectivity() -> ServiceCheck:
    """Check Cassidy API connectivity"""
    from time import time
    from app.cassidy.workflows import LinkedInWorkflow
    
    start_time = time()
    
    try:
        # Use the workflow health check method
        workflow = LinkedInWorkflow()
        health_result = await workflow.health_check()
        
        response_time = (time() - start_time) * 1000
        
        cassidy_status = health_result.get("cassidy_api", {}).get("status")
        
        if cassidy_status == "healthy":
            return ServiceCheck(
                status="healthy",
                response_time_ms=response_time
            )
        else:
            return ServiceCheck(
                status="unhealthy",
                response_time_ms=response_time,
                error=health_result.get("cassidy_api", {}).get("error", "Unknown error")
            )
            
    except Exception as e:
        response_time = (time() - start_time) * 1000
        return ServiceCheck(
            status="unhealthy",
            response_time_ms=response_time,
            error=str(e)
        )


async def _check_database_connectivity() -> ServiceCheck:
    """Check database connectivity"""
    from time import time
    
    start_time = time()
    
    try:
        # TODO: Implement actual database connectivity check
        # For now, simulate a successful check
        await asyncio.sleep(0.01)  # Simulate database query
        
        response_time = (time() - start_time) * 1000
        
        return ServiceCheck(
            status="healthy",
            response_time_ms=response_time
        )
        
    except Exception as e:
        response_time = (time() - start_time) * 1000
        return ServiceCheck(
            status="unhealthy", 
            response_time_ms=response_time,
            error=str(e)
        )


@router.get("/ready")
async def readiness_check():
    """
    Kubernetes readiness probe endpoint
    
    Returns 200 if service is ready to accept traffic
    """
    return {"status": "ready"}


@router.get("/live") 
async def liveness_check():
    """
    Kubernetes liveness probe endpoint
    
    Returns 200 if service is alive
    """
    return {"status": "alive"}
