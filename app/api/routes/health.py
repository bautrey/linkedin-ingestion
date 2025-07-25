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
    
    Checks external service connectivity, database status, and LinkedIn integration
    """
    logger.info("Detailed health check requested")
    
    checks = {}
    overall_status = "healthy"
    
    # Check Cassidy API connectivity (legacy check)
    cassidy_check = await _check_cassidy_connectivity()
    checks["cassidy"] = cassidy_check
    if cassidy_check.status != "healthy":
        overall_status = "degraded"
    
    # Check database connectivity
    database_check = await _check_database_connectivity()
    checks["database"] = database_check
    if database_check.status != "healthy":
        overall_status = "unhealthy"
    
    # Enhanced LinkedIn integration check
    from app.cassidy.health_checker import health_checker
    linkedin_check = await health_checker.quick_health_check()
    checks["linkedin_integration"] = {
        "status": linkedin_check["status"],
        "response_time_ms": linkedin_check["response_time_ms"],
        "error": linkedin_check.get("error")
    }
    
    if linkedin_check["status"] == "unhealthy":
        overall_status = "unhealthy"
    elif linkedin_check["status"] == "degraded" and overall_status == "healthy":
        overall_status = "degraded"
    
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


@router.get("/health/linkedin")
async def linkedin_integration_health_check():
    """
    Comprehensive LinkedIn integration health check
    
    Tests actual LinkedIn data ingestion using public test profiles
    WITHOUT saving data to the database. Detects API format changes,
    authentication issues, and service availability.
    
    Returns detailed metrics about:
    - API connectivity
    - Profile ingestion capability  
    - Company ingestion capability
    - Data quality metrics
    - Performance metrics
    """
    logger.info("Comprehensive LinkedIn integration health check requested")
    
    try:
        from app.cassidy.health_checker import health_checker
        
        # Run comprehensive health check
        result = await health_checker.comprehensive_health_check()
        
        # Log the result for monitoring
        logger.info(
            "LinkedIn integration health check completed",
            status=result["overall_status"],
            execution_time=result.get("execution_time_seconds", 0),
            errors_count=len(result.get("errors", [])),
            warnings_count=len(result.get("warnings", []))
        )
        
        return result
        
    except Exception as e:
        logger.error(f"LinkedIn integration health check failed: {e}")
        return {
            "overall_status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
            "service": "linkedin_integration_health_check"
        }
