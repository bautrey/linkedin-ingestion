"""
LinkedIn Ingestion Service

A FastAPI microservice for ingesting LinkedIn profiles and company data
using Cassidy AI workflows and storing in Supabase with pgvector.

Updated: Test Nixpacks build after removing Docker files - build verification
"""

import asyncio
import os
import uuid
from fastapi import FastAPI, HTTPException, Header, Depends, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, HttpUrl, Field, ValidationError, field_validator
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import traceback
import logging

# Configure logging for error tracking
logger = logging.getLogger(__name__)

from app.cassidy.client import CassidyClient
from app.cassidy.workflows import LinkedInWorkflow
from app.cassidy.models import ProfileIngestionRequest
from app.database.supabase_client import SupabaseClient
from app.core.config import settings
from app.models.errors import ErrorResponse, ValidationErrorResponse
from app.exceptions import (
    LinkedInIngestionError,
    InvalidLinkedInURLError,
    ProfileAlreadyExistsError
)
from app.cassidy.exceptions import CassidyWorkflowError
from app.models.canonical import CanonicalProfile
from app.models.canonical.profile import RoleType
from app.models.scoring import ScoringRequest, ScoringResponse, JobRetryRequest
from app.controllers.scoring_controllers import ProfileScoringController, ScoringJobController
from app.services.template_service import TemplateService
from app.services.template_versioning_service import TemplateVersioningService
from app.models.template_models import (
    PromptTemplate,
    CreateTemplateRequest,
    UpdateTemplateRequest,
    TemplateSummary,
    TemplateListResponse,
    TemplateListSummaryResponse,
    DeleteTemplateResponse,
    EnhancedScoringRequest,
    ScoringJobResponse
)


def normalize_linkedin_url(url: str) -> str:
    """
    Normalize LinkedIn profile URLs to consistent format:
    https://www.linkedin.com/in/username/
    
    Handles variations like:
    - linkedin.com/in/user -> https://www.linkedin.com/in/user/
    - https://linkedin.com/in/user -> https://www.linkedin.com/in/user/
    - https://www.linkedin.com/in/user -> https://www.linkedin.com/in/user/
    """
    # Remove trailing whitespace
    url = url.strip()
    
    # Ensure https protocol
    if not url.startswith('http'):
        url = 'https://' + url
    
    # Ensure www subdomain for linkedin.com
    if '://linkedin.com' in url:
        url = url.replace('://linkedin.com', '://www.linkedin.com')
    
    # Ensure trailing slash
    if not url.endswith('/'):
        url += '/'
    
    return url

# Create FastAPI application
app = FastAPI(
    title="LinkedIn Ingestion Service",
    description="Microservice for LinkedIn profile and company data ingestion",
    version=settings.VERSION,
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Global exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors with standardized error response"""
    validation_errors = []
    for error in exc.errors():
        validation_errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "invalid_value": error.get("input"),
            "error_type": error["type"]
        })
    
    error_response = ValidationErrorResponse(
        error_code="VALIDATION_ERROR",
        message="Request validation failed",
        details={
            "endpoint": str(request.url),
            "method": request.method,
            "total_errors": len(validation_errors)
        },
        validation_errors=validation_errors
    )
    
    return JSONResponse(
        status_code=422,
        content=error_response.model_dump()
    )

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle ValueError exceptions with standardized error response"""
    error_response = ErrorResponse(
        error_code="INVALID_VALUE",
        message=str(exc),
        details={
            "endpoint": str(request.url),
            "method": request.method,
            "exception_type": "ValueError"
        }
    )
    
    return JSONResponse(
        status_code=400,
        content=error_response.model_dump()
    )

# Custom LinkedIn Ingestion Exception Handlers
@app.exception_handler(InvalidLinkedInURLError)
async def invalid_linkedin_url_handler(request: Request, exc: InvalidLinkedInURLError):
    """Handle InvalidLinkedInURLError with 400 status code and suggestions"""
    # Log the error for tracking
    logger.warning(
        f"Invalid LinkedIn URL error: {exc.message}",
        extra={
            "url": exc.url,
            "endpoint": str(request.url),
            "method": request.method,
            "error_code": exc.error_code
        }
    )
    
    error_response = ErrorResponse(
        error_code=exc.error_code,
        message=exc.message,
        details={
            "endpoint": str(request.url),
            "method": request.method,
            "invalid_url": exc.url,
            **exc.details
        },
        suggestions=exc.details.get("suggestions", [])
    )
    
    return JSONResponse(
        status_code=exc.status_code or 400,
        content=error_response.model_dump()
    )

@app.exception_handler(ProfileAlreadyExistsError)
async def profile_already_exists_handler(request: Request, exc: ProfileAlreadyExistsError):
    """Handle ProfileAlreadyExistsError with 409 status code and suggestions"""
    # Log the error for tracking
    logger.info(
        f"Profile already exists: {exc.message}",
        extra={
            "profile_id": exc.profile_id,
            "endpoint": str(request.url),
            "method": request.method,
            "error_code": exc.error_code
        }
    )
    
    error_response = ErrorResponse(
        error_code=exc.error_code,
        message=exc.message,
        details={
            "endpoint": str(request.url),
            "method": request.method,
            "profile_id": exc.profile_id,
            **exc.details
        },
        suggestions=exc.details.get("suggestions", [])
    )
    
    return JSONResponse(
        status_code=exc.status_code or 409,
        content=error_response.model_dump()
    )

@app.exception_handler(CassidyWorkflowError)
async def cassidy_workflow_error_handler(request: Request, exc: CassidyWorkflowError):
    """Handle CassidyWorkflowError with 400 status code for invalid URLs"""
    # Log the error for tracking
    logger.warning(
        f"Cassidy workflow error: {exc.message}",
        extra={
            "endpoint": str(request.url),
            "method": request.method,
            "error_message": str(exc)
        }
    )
    
    # Check if this is a LinkedIn URL format error
    error_message = str(exc)
    if "not a valid LinkedIn profile URL" in error_message:
        # Extract the URL from the error message if possible
        url_start = error_message.find("*https://")
        url_end = error_message.find("*", url_start + 1)
        invalid_url = error_message[url_start+1:url_end] if url_start != -1 and url_end != -1 else "unknown"
        
        error_response = ErrorResponse(
            error_code="INVALID_LINKEDIN_URL",
            message="Invalid LinkedIn profile URL format",
            details={
                "endpoint": str(request.url),
                "method": request.method,
                "invalid_url": invalid_url,
                "cassidy_error": str(exc)
            },
            suggestions=[
                "Use the modern LinkedIn URL format: https://www.linkedin.com/in/username",
                "Avoid old LinkedIn URL formats like /pub/ which are no longer supported",
                "Ensure the LinkedIn URL is publicly accessible"
            ]
        )
        return JSONResponse(
            status_code=400,
            content=error_response.model_dump()
        )
    else:
        # Handle other Cassidy workflow errors
        error_response = ErrorResponse(
            error_code="WORKFLOW_ERROR",
            message="LinkedIn profile processing failed",
            details={
                "endpoint": str(request.url),
                "method": request.method,
                "workflow_error": str(exc)
            },
            suggestions=[
                "Verify the LinkedIn URL is correct and accessible",
                "Try again in a few minutes if this was a temporary issue"
            ]
        )
        return JSONResponse(
            status_code=400,
            content=error_response.model_dump()
        )

@app.exception_handler(LinkedInIngestionError)
async def linkedin_ingestion_error_handler(request: Request, exc: LinkedInIngestionError):
    """Handle base LinkedInIngestionError with dynamic status code and suggestions"""
    # Log the error for tracking  
    logger.error(
        f"LinkedIn ingestion error: {exc.message}",
        extra={
            "endpoint": str(request.url),
            "method": request.method,
            "error_code": exc.error_code,
            "status_code": exc.status_code
        }
    )
    
    error_response = ErrorResponse(
        error_code=exc.error_code,
        message=exc.message,
        details={
            "endpoint": str(request.url),
            "method": request.method,
            **exc.details
        },
        suggestions=exc.details.get("suggestions", [])
    )
    
    return JSONResponse(
        status_code=exc.status_code or 500,
        content=error_response.model_dump()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions with standardized error response"""
    # Don't catch HTTPExceptions - let FastAPI handle them
    if isinstance(exc, HTTPException):
        raise exc
    
    # Log unexpected errors for debugging
    logger.error(
        f"Unexpected error: {str(exc)}",
        extra={
            "endpoint": str(request.url),
            "method": request.method,
            "exception_type": type(exc).__name__,
            "traceback": traceback.format_exc() if settings.ENVIRONMENT != "production" else None
        }
    )
    
    error_response = ErrorResponse(
        error_code="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred",
        details={
            "endpoint": str(request.url),
            "method": request.method,
            "exception_type": type(exc).__name__,
            "exception_message": str(exc) if settings.ENVIRONMENT != "production" else None
        }
    )
    
    return JSONResponse(
        status_code=500,
        content=error_response.model_dump()
    )

# Client instances (initialized lazily)
cassidy_client = None
db_client = None
linkedin_workflow = None

def get_cassidy_client():
    global cassidy_client
    if cassidy_client is None:
        cassidy_client = CassidyClient()
    return cassidy_client

def get_db_client():
    global db_client
    if db_client is None:
        db_client = SupabaseClient()
    return db_client

def get_linkedin_workflow():
    global linkedin_workflow
    if linkedin_workflow is None:
        linkedin_workflow = LinkedInWorkflow()
    return linkedin_workflow

# Security dependency
def verify_api_key(x_api_key: Optional[str] = Header(None)):
    """Verify API key from header"""
    if x_api_key != settings.API_KEY:
        error_response = ErrorResponse(
            error_code="UNAUTHORIZED",
            message="Invalid or missing API key",
            details={
                "provided_key_length": len(x_api_key) if x_api_key else 0,
                "expected_key_present": bool(settings.API_KEY)
            }
        )
        raise HTTPException(
            status_code=403, 
            detail=error_response.model_dump()
        )
    return x_api_key

# Request/Response models for REST API
class ProfileCreateRequest(BaseModel):
    linkedin_url: HttpUrl
    name: Optional[str] = None
    include_companies: bool = Field(default=True, description="Include company profiles for all experience entries")
    suggested_role: RoleType = Field(..., description="The suggested role for this profile: CIO, CTO, or CISO for role-specific scoring")

class BatchProfileCreateRequest(BaseModel):
    profiles: List[ProfileCreateRequest] = Field(..., min_items=1, max_items=10, description="List of profiles to ingest (max 10 per batch)")
    max_concurrent: int = Field(default=3, ge=1, le=5, description="Maximum concurrent processing (1-5)")

class PaginationMetadata(BaseModel):
    limit: int
    offset: int
    total: Optional[int] = None
    has_more: bool = False

# ErrorResponse models now imported from app.models.errors

class ProfileResponse(BaseModel):
    id: str
    linkedin_id: Optional[str] = None
    name: Optional[str] = None
    url: str
    position: Optional[str] = None
    about: Optional[str] = None
    city: Optional[str] = None
    country_code: Optional[str] = None
    followers: Optional[int] = None
    connections: Optional[int] = None
    profile_image_url: Optional[str] = None
    current_company: Optional[Dict[str, Any]] = None
    experience: List[Dict[str, Any]] = []
    education: List[Dict[str, Any]] = []
    certifications: List[Dict[str, Any]] = []
    suggested_role: Optional[RoleType] = None
    created_at: str
    timestamp: Optional[str] = None
    
    # Company processing response fields (only present when using company ingestion)
    companies_processed: Optional[List[Dict[str, Any]]] = None
    pipeline_metadata: Optional[Dict[str, Any]] = None

class ProfileListResponse(BaseModel):
    data: List[ProfileResponse]
    pagination: PaginationMetadata

class BatchProfileResponse(BaseModel):
    batch_id: str = Field(..., description="Unique identifier for this batch operation")
    total_requested: int = Field(..., description="Total number of profiles requested")
    successful: int = Field(..., description="Number of profiles successfully processed")
    failed: int = Field(..., description="Number of profiles that failed processing")
    results: List[ProfileResponse] = Field(..., description="Individual profile results")
    started_at: str = Field(..., description="Batch processing start time")
    completed_at: str = Field(..., description="Batch processing completion time")
    processing_time_seconds: float = Field(..., description="Total processing time in seconds")

# ProfileController class for REST endpoints
class ProfileController:
    """Controller for profile-related REST operations"""
    
    def __init__(self, db_client, cassidy_client, linkedin_workflow):
        self.db_client = db_client
        self.cassidy_client = cassidy_client
        self.linkedin_workflow = linkedin_workflow
        
        # Initialize LinkedIn pipeline for company processing
        from app.services.linkedin_pipeline import LinkedInDataPipeline
        self.linkedin_pipeline = LinkedInDataPipeline()
    
    def _convert_db_profile_to_response(self, db_profile: Dict[str, Any]) -> ProfileResponse:
        """Convert database profile to ProfileResponse model"""
        return ProfileResponse(
            id=db_profile["id"],
            linkedin_id=db_profile.get("linkedin_id"),
            name=db_profile.get("name"),
            url=db_profile["url"],
            position=db_profile.get("position"),
            about=db_profile.get("about"),
            city=db_profile.get("city"),
            country_code=db_profile.get("country_code"),
            followers=db_profile.get("followers"),
            connections=db_profile.get("connections"),
            profile_image_url=db_profile.get("profile_image_url"),
            current_company=db_profile.get("current_company"),
            experience=db_profile.get("experience", []),
            education=db_profile.get("education", []),
            certifications=db_profile.get("certifications", []),
            suggested_role=db_profile.get("suggested_role"),
            created_at=db_profile["created_at"],
            timestamp=db_profile.get("timestamp")
        )
    
    async def list_profiles(
        self,
        linkedin_url: Optional[str] = None,
        name: Optional[str] = None,
        company: Optional[str] = None,
        location: Optional[str] = None,
        score_range: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> ProfileListResponse:
        """List profiles with optional filtering and pagination"""
        
        # If linkedin_url is provided, do exact search with normalized URL
        if linkedin_url:
            normalized_url = normalize_linkedin_url(linkedin_url)
            profile = await self.db_client.get_profile_by_url(normalized_url)
            if profile:
                return ProfileListResponse(
                    data=[self._convert_db_profile_to_response(profile)],
                    pagination=PaginationMetadata(limit=limit, offset=offset, total=1, has_more=False)
                )
            else:
                return ProfileListResponse(
                    data=[],
                    pagination=PaginationMetadata(limit=limit, offset=offset, total=0, has_more=False)
                )
        
        # Otherwise do general search with filters
        profiles = await self.db_client.search_profiles(
            name=name,
            company=company,
            location=location,
            score_range=score_range,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            offset=offset
        )
        
        profile_responses = [self._convert_db_profile_to_response(p) for p in profiles]
        
        return ProfileListResponse(
            data=profile_responses,
            pagination=PaginationMetadata(
                limit=limit,
                offset=offset,
                total=len(profile_responses),
                has_more=len(profile_responses) >= limit
            )
        )
    
    async def get_profile(self, profile_id: str) -> ProfileResponse:
        """Get individual profile by ID"""
        profile = await self.db_client.get_profile_by_id(profile_id)
        if not profile:
            error_response = ErrorResponse(
                error_code="PROFILE_NOT_FOUND",
                message=f"Profile with ID {profile_id} not found",
                details={
                    "profile_id": profile_id,
                    "operation": "get_profile"
                }
            )
            raise HTTPException(status_code=404, detail=error_response.model_dump())
        
        return self._convert_db_profile_to_response(profile)
    
    async def create_profile(self, request: ProfileCreateRequest) -> ProfileResponse:
        """Create a new LinkedIn profile with complete company processing
        
        Uses the consolidated LinkedInDataPipeline for all processing.
        """
        
        # Normalize LinkedIn URL to consistent format
        linkedin_url = normalize_linkedin_url(str(request.linkedin_url))
        
        # Check for existing profile with normalized URL
        existing_by_url = await self.db_client.get_profile_by_url(linkedin_url)
        if existing_by_url:
            # Smart update behavior: delete existing profile and create fresh one
            await self.db_client.delete_profile(existing_by_url["id"])
        
        # Use LinkedInDataPipeline for unified processing (now includes storage and suggested role)
        # Note: Company processing is controlled by ENABLE_COMPANY_INGESTION setting
        pipeline_result = await self.linkedin_pipeline.ingest_profile(
            linkedin_url, 
            store_in_db=True,  # Pipeline now handles all storage
            suggested_role=request.suggested_role.value if request.suggested_role else None
        )
        
        # Get the stored profile ID from pipeline result
        profile_id = pipeline_result.get("storage_ids", {}).get("profile")
        if not profile_id:
            raise Exception("No profile ID returned from pipeline storage")
        
        # Retrieve the final profile data to return
        stored_profile = await self.db_client.get_profile_by_id(profile_id)
        response = self._convert_db_profile_to_response(stored_profile)
        
        # Add company processing metadata to response from pipeline result
        if pipeline_result.get("companies"):
            response.companies_processed = pipeline_result["companies"]
            response.pipeline_metadata = {
                "companies_found": len(pipeline_result["companies"]),
                "companies_fetched_from_cassidy": True,
                "pipeline_status": pipeline_result.get("status"),
                "pipeline_id": pipeline_result.get("pipeline_id")
            }
        
        return response
    
    
    async def batch_create_profiles(self, request: BatchProfileCreateRequest) -> BatchProfileResponse:
        """Batch create profiles using the unified ingestion flow with company processing"""
        import time
        import asyncio
        from uuid import uuid4
        
        batch_id = str(uuid4())
        start_time = time.time()
        started_at = datetime.now(timezone.utc)
        
        # Process profiles with concurrency control
        semaphore = asyncio.Semaphore(request.max_concurrent)
        
        async def process_single_profile(profile_request):
            async with semaphore:
                try:
                    return await self.create_profile(profile_request), None
                except Exception as e:
                    return None, str(e)
        
        # Execute all profile creation tasks
        tasks = [process_single_profile(profile_req) for profile_req in request.profiles]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        profile_responses = []
        successful_count = 0
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # Handle exceptions from gather
                error_response = ProfileResponse(
                    id="",
                    name=f"Failed: {request.profiles[i].linkedin_url}",
                    url=str(request.profiles[i].linkedin_url),
                    position="Processing Failed",
                    about=f"Error: {str(result)}",
                    created_at=started_at.isoformat(),
                    experience=[],
                    education=[],
                    certifications=[],
                    companies_processed=[],
                    pipeline_metadata={
                        "status": "failed",
                        "error": str(result)
                    }
                )
                profile_responses.append(error_response)
            else:
                profile_response, error = result
                if profile_response:
                    profile_responses.append(profile_response)
                    successful_count += 1
                else:
                    # Handle errors from individual profile processing
                    error_response = ProfileResponse(
                        id="",
                        name=f"Failed: {request.profiles[i].linkedin_url}",
                        url=str(request.profiles[i].linkedin_url),
                        position="Processing Failed",
                        about=f"Error: {error}",
                        created_at=started_at.isoformat(),
                        experience=[],
                        education=[],
                        certifications=[],
                        companies_processed=[],
                        pipeline_metadata={
                            "status": "failed",
                            "error": error
                        }
                    )
                    profile_responses.append(error_response)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        return BatchProfileResponse(
            batch_id=batch_id,
            total_requested=len(request.profiles),
            successful=successful_count,
            failed=len(request.profiles) - successful_count,
            results=profile_responses,
            started_at=started_at.isoformat(),
            completed_at=datetime.now(timezone.utc).isoformat(),
            processing_time_seconds=processing_time
        )


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "LinkedIn Ingestion Service",
        "version": settings.VERSION,
        "status": "running",
        "docs_url": "/docs" if settings.ENVIRONMENT != "production" else None,
        "deployment_timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.get("/api/v1/health")
async def health_check():
    """Basic health check endpoint"""
    try:
        # Check database connectivity
        db_health = await get_db_client().health_check()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": settings.VERSION,
            "database": db_health,
            "environment": settings.ENVIRONMENT
        }
    except Exception as e:
        error_response = ErrorResponse(
            error_code="HEALTH_CHECK_FAILED",
            message=f"Health check failed: {str(e)}",
            details={
                "service": "linkedin-ingestion",
                "component": "health_check",
                "exception_type": type(e).__name__
            }
        )
        raise HTTPException(status_code=503, detail=error_response.model_dump())


@app.get("/api/v1/health/detailed")
async def detailed_health_check(
    api_key: str = Depends(verify_api_key)
):
    """Detailed health check including all services"""
    start_time = datetime.now(timezone.utc)
    health_checks = {}
    overall_status = "healthy"
    errors = []
    
    try:
        # Database health check
        db_start = datetime.now()
        try:
            db_health = await get_db_client().health_check()
            db_time = (datetime.now() - db_start).total_seconds() * 1000
            health_checks["database"] = {
                "status": "healthy" if db_health["status"] == "healthy" else "degraded",
                "response_time_ms": db_time,
                "details": db_health
            }
        except Exception as e:
            health_checks["database"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            overall_status = "degraded"
            errors.append(f"Database: {str(e)}")
        
        # OpenAI/LLM service health check
        llm_start = datetime.now()
        try:
            from app.services.llm_scoring_service import LLMScoringService
            llm_service = LLMScoringService()
            
            has_api_key = bool(llm_service.api_key and llm_service.api_key != "your-openai-key-here-or-set-in-railway")
            has_client = llm_service.client is not None
            
            # Test token counting (lightweight test)
            test_tokens = llm_service.count_tokens("Health check test")
            llm_time = (datetime.now() - llm_start).total_seconds() * 1000
            
            llm_status = "healthy" if (has_api_key and has_client and test_tokens > 0) else "degraded"
            if not has_api_key:
                llm_status = "degraded"
                errors.append("LLM: No API key configured")
            
            health_checks["llm_service"] = {
                "status": llm_status,
                "response_time_ms": llm_time,
                "has_api_key": has_api_key,
                "has_client": has_client,
                "token_test_result": test_tokens
            }
            
            if llm_status != "healthy":
                overall_status = "degraded"
                
        except Exception as e:
            health_checks["llm_service"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            overall_status = "degraded"
            errors.append(f"LLM Service: {str(e)}")
        
        # Template service health check
        template_start = datetime.now()
        try:
            from app.services.template_service import TemplateService
            
            template_service = TemplateService(get_db_client())
            
            # Test template listing (lightweight operation)
            templates = await template_service.list_templates()
            template_time = (datetime.now() - template_start).total_seconds() * 1000
            
            health_checks["template_service"] = {
                "status": "healthy",
                "response_time_ms": template_time,
                "template_count": len(templates),
                "has_default_templates": any("CTO" in t.name for t in templates)
            }
        except Exception as e:
            health_checks["template_service"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            overall_status = "degraded"
            errors.append(f"Template Service: {str(e)}")
        
        # Scoring job service health check
        scoring_start = datetime.now()
        try:
            from app.services.scoring_job_service import ScoringJobService
            scoring_service = ScoringJobService()
            
            # Test basic service functionality (no actual database query)
            scoring_time = (datetime.now() - scoring_start).total_seconds() * 1000
            
            health_checks["scoring_service"] = {
                "status": "healthy",
                "response_time_ms": scoring_time,
                "service_initialized": True
            }
        except Exception as e:
            health_checks["scoring_service"] = {
                "status": "unhealthy", 
                "error": str(e)
            }
            overall_status = "degraded"
            errors.append(f"Scoring Service: {str(e)}")
        
        total_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        
        return {
            "status": overall_status,
            "timestamp": start_time.isoformat(),
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
            "total_check_time_ms": total_time,
            "services": health_checks,
            "errors": errors if errors else None
        }
        
    except Exception as e:
        error_response = ErrorResponse(
            error_code="DETAILED_HEALTH_CHECK_FAILED",
            message=f"Detailed health check failed: {str(e)}",
            details={
                "service": "linkedin-ingestion",
                "component": "detailed_health_check",
                "exception_type": type(e).__name__
            }
        )
        raise HTTPException(status_code=503, detail=error_response.model_dump())


@app.get("/api/v1/openai-test")
async def openai_test(
    api_key: str = Depends(verify_api_key)
):
    """Test OpenAI configuration and connectivity"""
    try:
        from app.services.llm_scoring_service import LLMScoringService
        
        # Initialize the service
        llm_service = LLMScoringService()
        
        # Check configuration
        has_api_key = bool(llm_service.api_key and llm_service.api_key != "your-openai-key-here-or-set-in-railway")
        has_client = llm_service.client is not None
        
        # Try a simple token counting test
        test_text = "This is a simple test for OpenAI integration"
        token_count = llm_service.count_tokens(test_text)
        
        return {
            "status": "openai_configuration_check",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "has_api_key": has_api_key,
            "api_key_preview": llm_service.api_key[:10] + "..." if llm_service.api_key else None,
            "has_client": has_client,
            "default_model": llm_service.default_model,
            "max_tokens": llm_service.max_tokens,
            "temperature": llm_service.temperature,
            "token_counting_test": {
                "text": test_text,
                "token_count": token_count
            }
        }
    except Exception as e:
        error_response = ErrorResponse(
            error_code="OPENAI_TEST_FAILED",
            message=f"OpenAI test failed: {str(e)}",
            details={
                "service": "linkedin-ingestion",
                "component": "openai_test",
                "exception_type": type(e).__name__
            }
        )
        raise HTTPException(status_code=500, detail=error_response.model_dump())


# Kubernetes probe endpoints
@app.get("/ready")
async def readiness_probe():
    """Kubernetes readiness probe - checks if service can serve requests"""
    try:
        # Basic database connectivity check
        db_health = await get_db_client().health_check()
        
        if db_health["status"] != "healthy":
            raise HTTPException(status_code=503, detail={"status": "not_ready", "reason": "database_unhealthy"})
        
        # Check template service initialization
        try:
            from app.services.template_service import TemplateService
            template_service = TemplateService(get_db_client())
            # Light test - just instantiate service
        except Exception:
            raise HTTPException(status_code=503, detail={"status": "not_ready", "reason": "template_service_initialization_failed"})
        
        return {"status": "ready", "timestamp": datetime.now(timezone.utc).isoformat()}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail={
            "status": "not_ready", 
            "reason": "unexpected_error",
            "error": str(e)
        })


@app.get("/live")
async def liveness_probe():
    """Kubernetes liveness probe - checks if service is alive"""
    # Simple check that the application is responsive
    # This should be very lightweight and not depend on external services
    return {
        "status": "alive",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": settings.VERSION
    }


@app.get("/api/version")
async def get_version():
    """Get comprehensive version and deployment information"""
    return {
        "version": settings.VERSION,
        "service": "LinkedIn Ingestion Service",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **settings.version_info
    }


# Initialize ProfileController
def get_profile_controller():
    return ProfileController(get_db_client(), get_cassidy_client(), get_linkedin_workflow())

# New REST API endpoints
@app.get(
    "/api/v1/profiles", 
    response_model=ProfileListResponse,
    responses={
        403: {"model": ErrorResponse, "description": "Unauthorized - Invalid API key"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def list_profiles(
    linkedin_url: Optional[str] = Query(None, description="Exact LinkedIn URL search"),
    name: Optional[str] = Query(None, description="Partial name search (case-insensitive)"),
    company: Optional[str] = Query(None, description="Partial company name search (case-insensitive)"),
    location: Optional[str] = Query(None, description="Partial location search (case-insensitive)"),
    score_range: Optional[str] = Query(None, description="Score range filter: 'unscored', 'high' (8-10), 'medium' (5-7), 'low' (1-4)"),
    sort_by: Optional[str] = Query(None, description="Field to sort by: name, position, city, location, company, current_company, created_at, timestamp, followers, connections, country_code, url, about, profile_image_url, suggested_role, linkedin_id"),
    sort_order: Optional[str] = Query("desc", description="Sort order: 'asc' or 'desc' (default: desc)"),
    limit: int = Query(50, ge=1, le=100, description="Number of profiles to return"),
    offset: int = Query(0, ge=0, description="Number of profiles to skip"),
    api_key: str = Depends(verify_api_key)
):
    """List profiles with optional filtering, sorting, and pagination"""
    controller = get_profile_controller()
    return await controller.list_profiles(
        linkedin_url=linkedin_url,
        name=name,
        company=company,
        location=location,
        score_range=score_range,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        offset=offset
    )

@app.get(
    "/api/v1/profiles/{profile_id}", 
    response_model=ProfileResponse,
    responses={
        403: {"model": ErrorResponse, "description": "Unauthorized - Invalid API key"},
        404: {"model": ErrorResponse, "description": "Profile not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def get_profile(
    profile_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Get individual profile by ID"""
    controller = get_profile_controller()
    return await controller.get_profile(profile_id)

@app.post(
    "/api/v1/profiles", 
    response_model=ProfileResponse, 
    status_code=201,
    responses={
        403: {"model": ErrorResponse, "description": "Unauthorized - Invalid API key"},
        409: {"model": ErrorResponse, "description": "Profile already exists - Conflict"},
        422: {"model": ValidationErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def create_profile(
    request: ProfileCreateRequest,
    api_key: str = Depends(verify_api_key)
):
    """Create a new profile by ingesting from LinkedIn"""
    controller = get_profile_controller()
    return await controller.create_profile(request)


@app.post(
    "/api/v1/profiles/batch", 
    response_model=BatchProfileResponse, 
    status_code=201,
    responses={
        403: {"model": ErrorResponse, "description": "Unauthorized - Invalid API key"},
        422: {"model": ValidationErrorResponse, "description": "Validation error"},
        429: {"model": ErrorResponse, "description": "Too many profiles in batch or rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def batch_create_profiles(
    request: BatchProfileCreateRequest,
    api_key: str = Depends(verify_api_key)
):
    """Batch create profiles using the unified ingestion flow with company processing (max 10 profiles per batch)"""
    controller = get_profile_controller()
    return await controller.batch_create_profiles(request)


@app.delete(
    "/api/v1/profiles/{profile_id}", 
    status_code=204,
    responses={
        403: {"model": ErrorResponse, "description": "Unauthorized - Invalid API key"},
        404: {"model": ErrorResponse, "description": "Profile not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def delete_profile(
    profile_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Delete an individual profile by ID"""
    try:
        controller = get_profile_controller()
        deleted = await controller.db_client.delete_profile(profile_id)
        
        if not deleted:
            error_response = ErrorResponse(
                error_code="PROFILE_NOT_FOUND",
                message=f"Profile with ID {profile_id} not found",
                details={
                    "profile_id": profile_id,
                    "operation": "delete_profile"
                }
            )
            raise HTTPException(
                status_code=404, 
                detail=error_response.model_dump()
            )
        
        # Return empty response for 204 No Content
        return None
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 404)
        raise
    except Exception as e:
        # Handle database and other errors
        error_response = ErrorResponse(
            error_code="DATABASE_ERROR",
            message=f"Failed to delete profile: {str(e)}",
            details={
                "profile_id": profile_id,
                "operation": "delete_profile",
                "exception_type": type(e).__name__
            }
        )
        raise HTTPException(
            status_code=500,
            detail=error_response.model_dump()
        )

# =============================================================================
# COMPANY API MODELS AND ENDPOINTS
# =============================================================================

# Company API Request/Response Models
class CompanyCreateRequest(BaseModel):
    company_name: str = Field(..., description="Company name (required)")
    linkedin_url: Optional[HttpUrl] = Field(None, description="LinkedIn company page URL")
    description: Optional[str] = Field(None, description="Company description")
    website: Optional[HttpUrl] = Field(None, description="Company website")
    employee_count: Optional[int] = Field(None, ge=0, description="Number of employees")
    year_founded: Optional[int] = Field(None, ge=1600, le=2030, description="Year founded")
    industries: List[str] = Field(default_factory=list, description="List of industries")
    hq_city: Optional[str] = Field(None, description="Headquarters city")
    hq_region: Optional[str] = Field(None, description="Headquarters region/state")
    hq_country: Optional[str] = Field(None, description="Headquarters country")
    tagline: Optional[str] = Field(None, description="Company tagline")
    specialties: Optional[str] = Field(None, description="Comma-separated specialties")

class CompanyUpdateRequest(BaseModel):
    company_name: Optional[str] = Field(None, description="Company name")
    linkedin_url: Optional[HttpUrl] = Field(None, description="LinkedIn company page URL")
    description: Optional[str] = Field(None, description="Company description")
    website: Optional[HttpUrl] = Field(None, description="Company website")
    employee_count: Optional[int] = Field(None, ge=0, description="Number of employees")
    year_founded: Optional[int] = Field(None, ge=1600, le=2030, description="Year founded")
    industries: Optional[List[str]] = Field(None, description="List of industries")
    hq_city: Optional[str] = Field(None, description="Headquarters city")
    hq_region: Optional[str] = Field(None, description="Headquarters region/state")
    hq_country: Optional[str] = Field(None, description="Headquarters country")
    tagline: Optional[str] = Field(None, description="Company tagline")
    specialties: Optional[str] = Field(None, description="Comma-separated specialties")

class CompanyResponse(BaseModel):
    id: str
    company_id: Optional[str] = None
    company_name: str
    linkedin_url: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    domain: Optional[str] = None
    employee_count: Optional[int] = None
    employee_range: Optional[str] = None
    year_founded: Optional[int] = None
    company_age: Optional[int] = None
    size_category: str
    industries: List[str] = []
    tagline: Optional[str] = None
    specialties: Optional[str] = None
    follower_count: Optional[int] = None
    hq_city: Optional[str] = None
    hq_region: Optional[str] = None
    hq_country: Optional[str] = None
    hq_full_address: Optional[str] = None
    logo_url: Optional[str] = None
    funding_info: Optional[Dict[str, Any]] = None
    locations: List[Dict[str, Any]] = []
    affiliated_companies: List[Dict[str, Any]] = []
    is_startup: bool = False
    profile_count: Optional[int] = None
    created_at: str
    updated_at: Optional[str] = None

class CompanyListResponse(BaseModel):
    data: List[CompanyResponse]
    pagination: PaginationMetadata

class CompanySummaryResponse(BaseModel):
    id: str
    company_name: str
    domain: Optional[str] = None
    employee_count: Optional[int] = None
    size_category: str
    industries: List[str] = []
    hq_city: Optional[str] = None
    hq_country: Optional[str] = None
    is_startup: bool = False

# Profile-Company Relationship Models
class ProfileCompanyLinkRequest(BaseModel):
    position_title: str = Field(..., description="Job title/position")
    start_date: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")
    is_current: bool = Field(False, description="Is this a current position")
    description: Optional[str] = Field(None, description="Job description")

class ProfileCompanyRelationship(BaseModel):
    id: str
    profile_id: str
    company_id: str
    position_title: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_current: bool = False
    description: Optional[str] = None
    created_at: str

# Company Controller
class CompanyController:
    """Controller for company-related REST operations"""
    
    def __init__(self, db_client):
        self.db_client = db_client
        
        # Initialize company service and repository
        from app.repositories.company_repository import CompanyRepository
        from app.services.company_service import CompanyService
        
        self.company_repo = CompanyRepository(db_client)
        self.company_service = CompanyService(self.company_repo)
    
    def _convert_canonical_to_response(self, company, profile_count=None) -> CompanyResponse:
        """Convert CanonicalCompany to CompanyResponse model"""
        from app.models.canonical.company import CanonicalCompany
        
        if isinstance(company, dict):
            # Handle database row format
            return CompanyResponse(
                id=company.get("id", ""),
                company_id=company.get("linkedin_company_id"),
                company_name=company.get("company_name", ""),
                linkedin_url=company.get("linkedin_url"),
                description=company.get("description"),
                website=company.get("website"),
                domain=company.get("domain"),
                employee_count=company.get("employee_count"),
                employee_range=company.get("employee_range"),
                year_founded=company.get("year_founded"),
                company_age=None,  # Will be computed
                size_category=self._get_size_category(company.get("employee_count")),
                industries=company.get("industries", []),
                tagline=company.get("tagline"),
                specialties=company.get("specialties"),
                follower_count=company.get("follower_count"),
                hq_city=company.get("hq_city"),
                hq_region=company.get("hq_region"),
                hq_country=company.get("hq_country"),
                hq_full_address=company.get("hq_full_address"),
                logo_url=company.get("logo_url"),
                funding_info=company.get("funding_info"),
                locations=company.get("locations", []),
                affiliated_companies=company.get("affiliated_companies", []),
                is_startup=False,  # Will be computed
                profile_count=profile_count or company.get("profile_count"),
                created_at=company.get("created_at", company.get("timestamp", "")),
                updated_at=company.get("updated_at")
            )
        else:
            # Handle CanonicalCompany instance
            return CompanyResponse(
                id=getattr(company, 'id', ''),  # Database ID not in model
                company_id=company.company_id,
                company_name=company.company_name,
                linkedin_url=str(company.linkedin_url) if company.linkedin_url else None,
                description=company.description,
                website=str(company.website) if company.website else None,
                domain=company.domain,
                employee_count=company.employee_count,
                employee_range=company.employee_range,
                year_founded=company.year_founded,
                company_age=company.company_age,
                size_category=company.size_category,
                industries=company.industries,
                tagline=company.tagline,
                specialties=company.specialties,
                follower_count=company.follower_count,
                hq_city=company.hq_city,
                hq_region=company.hq_region,
                hq_country=company.hq_country,
                hq_full_address=company.hq_full_address,
                logo_url=str(company.logo_url) if company.logo_url else None,
                funding_info=company.funding_info.model_dump() if company.funding_info else None,
                locations=[loc.model_dump() for loc in company.locations] if company.locations else [],
                affiliated_companies=[ac.model_dump() for ac in company.affiliated_companies] if company.affiliated_companies else [],
                is_startup=company.is_startup(),
                profile_count=profile_count,  # Use the profile_count parameter
                created_at=company.timestamp.isoformat() if company.timestamp else "",
                updated_at=None  # Not tracked in canonical model
            )
    
    def _get_size_category(self, employee_count: Optional[int]) -> str:
        """Calculate size category from employee count"""
        if employee_count is None:
            return "Unknown"
        elif employee_count < 10:
            return "Startup"
        elif employee_count < 50:
            return "Small"
        elif employee_count < 200:
            return "Medium"
        elif employee_count < 1000:
            return "Large"
        else:
            return "Enterprise"
    
    async def list_companies(
        self,
        name: Optional[str] = None,
        domain: Optional[str] = None,
        industry: Optional[str] = None,
        city: Optional[str] = None,
        country: Optional[str] = None,
        size_category: Optional[str] = None,
        is_startup: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0
    ) -> CompanyListResponse:
        """List companies with filtering and pagination"""
        try:
            companies = []
            
            # Apply filters based on parameters
            if name:
                companies = await self.company_repo.search_by_name(name, limit)
            elif domain:
                companies = self.company_repo.search_by_domain(domain, exact_match=False)
            elif industry:
                companies = self.company_repo.get_companies_by_industry(industry, limit)
            elif city or country:
                companies = self.company_repo.get_companies_by_location(city, country, limit)
            elif is_startup:
                startup_companies = self.company_repo.get_startup_companies(limit)
                # Convert dict results to response format and get profile counts
                if startup_companies:
                    company_ids = [c.get("id") for c in startup_companies if c.get("id")]
                    profile_counts = await self.company_repo.batch_get_profile_counts(company_ids)
                    
                    company_responses = []
                    for company_dict in startup_companies:
                        company_id = company_dict.get("id")
                        profile_count = profile_counts.get(company_id, 0)
                        company_responses.append(self._convert_canonical_to_response(company_dict, profile_count))
                    
                    return CompanyListResponse(
                        data=company_responses,
                        pagination=PaginationMetadata(
                            limit=limit,
                            offset=offset,
                            total=len(company_responses),
                            has_more=len(company_responses) >= limit
                        )
                    )
                else:
                    return CompanyListResponse(
                        data=[],
                        pagination=PaginationMetadata(
                            limit=limit,
                            offset=offset,
                            total=0,
                            has_more=False
                        )
                    )
            elif size_category:
                size_companies = self.company_repo.get_companies_by_size_category(size_category, limit)
                # Convert dict results to response format and get profile counts
                if size_companies:
                    company_ids = [c.get("id") for c in size_companies if c.get("id")]
                    profile_counts = await self.company_repo.batch_get_profile_counts(company_ids)
                    
                    company_responses = []
                    for company_dict in size_companies:
                        company_id = company_dict.get("id")
                        profile_count = profile_counts.get(company_id, 0)
                        company_responses.append(self._convert_canonical_to_response(company_dict, profile_count))
                    
                    return CompanyListResponse(
                        data=company_responses,
                        pagination=PaginationMetadata(
                            limit=limit,
                            offset=offset,
                            total=len(company_responses),
                            has_more=len(company_responses) >= limit
                        )
                    )
                else:
                    return CompanyListResponse(
                        data=[],
                        pagination=PaginationMetadata(
                            limit=limit,
                            offset=offset,
                            total=0,
                            has_more=False
                        )
                    )
            else:
                # Get all companies using the proper get_all method
                companies = await self.company_repo.get_all(limit=limit, offset=offset)
            
            # For standard company results (CanonicalCompany objects), get profile counts
            if companies:
                # Extract company IDs from the company objects
                company_ids = []
                for company in companies:
                    if hasattr(company, 'id'):
                        company_ids.append(getattr(company, 'id'))
                    elif isinstance(company, dict) and company.get('id'):
                        company_ids.append(company['id'])
                
                # Get profile counts in batch
                profile_counts = await self.company_repo.batch_get_profile_counts(company_ids) if company_ids else {}
                
                # Convert to response format with profile counts
                company_responses = []
                for company in companies:
                    company_id = None
                    if hasattr(company, 'id'):
                        company_id = getattr(company, 'id')
                    elif isinstance(company, dict) and company.get('id'):
                        company_id = company['id']
                    
                    profile_count = profile_counts.get(company_id, 0) if company_id else 0
                    company_responses.append(self._convert_canonical_to_response(company, profile_count))
            else:
                company_responses = []
            
            return CompanyListResponse(
                data=company_responses,
                pagination=PaginationMetadata(
                    limit=limit,
                    offset=offset,
                    total=len(company_responses),
                    has_more=len(company_responses) >= limit
                )
            )
            
        except Exception as e:
            logger.error(f"Failed to list companies: {str(e)}")
            return CompanyListResponse(
                data=[],
                pagination=PaginationMetadata(
                    limit=limit,
                    offset=offset,
                    total=0,
                    has_more=False
                )
            )
    
    async def get_company(self, company_id: str) -> CompanyResponse:
        """Get individual company by ID"""
        company = await self.company_repo.get_by_id(company_id)
        if not company:
            error_response = ErrorResponse(
                error_code="COMPANY_NOT_FOUND",
                message=f"Company with ID {company_id} not found",
                details={
                    "company_id": company_id,
                    "operation": "get_company"
                }
            )
            raise HTTPException(status_code=404, detail=error_response.model_dump())
        
        # Get profile count for this company
        profile_count = self.company_repo.get_profile_count_for_company(company_id)
        
        return self._convert_canonical_to_response(company, profile_count)
    
    async def create_company(self, request: CompanyCreateRequest) -> CompanyResponse:
        """Create a new company"""
        try:
            # Convert request to CanonicalCompany
            from app.models.canonical.company import CanonicalCompany
            
            company_data = {
                "company_name": request.company_name,
                "linkedin_url": request.linkedin_url,
                "description": request.description,
                "website": request.website,
                "employee_count": request.employee_count,
                "year_founded": request.year_founded,
                "industries": request.industries,
                "hq_city": request.hq_city,
                "hq_region": request.hq_region,
                "hq_country": request.hq_country,
                "tagline": request.tagline,
                "specialties": request.specialties
            }
            
            # Remove None values
            company_data = {k: v for k, v in company_data.items() if v is not None}
            
            # Create CanonicalCompany instance
            company = CanonicalCompany(**company_data)
            
            # Use service to create with deduplication
            result = self.company_service.create_or_update_company(company)
            
            # Get the created company
            created_company = await self.company_repo.get_by_id(result["id"])
            return self._convert_canonical_to_response(created_company)
            
        except Exception as e:
            logger.error(f"Failed to create company: {str(e)}")
            error_response = ErrorResponse(
                error_code="COMPANY_CREATION_FAILED",
                message=f"Failed to create company: {str(e)}",
                details={
                    "company_name": request.company_name,
                    "operation": "create_company",
                    "exception_type": type(e).__name__
                }
            )
            raise HTTPException(status_code=500, detail=error_response.model_dump())
    
    async def update_company(self, company_id: str, request: CompanyUpdateRequest) -> CompanyResponse:
        """Update an existing company"""
        try:
            # Get existing company
            existing_company = await self.company_repo.get_by_id(company_id)
            if not existing_company:
                error_response = ErrorResponse(
                    error_code="COMPANY_NOT_FOUND",
                    message=f"Company with ID {company_id} not found",
                    details={
                        "company_id": company_id,
                        "operation": "update_company"
                    }
                )
                raise HTTPException(status_code=404, detail=error_response.model_dump())
            
            # Update fields that were provided
            update_data = existing_company.model_dump()
            request_data = request.model_dump(exclude_none=True)
            
            for field, value in request_data.items():
                update_data[field] = value
            
            # Create updated CanonicalCompany
            from app.models.canonical.company import CanonicalCompany
            updated_company = CanonicalCompany(**update_data)
            
            # Update in database
            result = self.company_repo.update(company_id, updated_company)
            
            # Get the updated company
            updated_company = await self.company_repo.get_by_id(company_id)
            return self._convert_canonical_to_response(updated_company)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to update company {company_id}: {str(e)}")
            error_response = ErrorResponse(
                error_code="COMPANY_UPDATE_FAILED",
                message=f"Failed to update company: {str(e)}",
                details={
                    "company_id": company_id,
                    "operation": "update_company",
                    "exception_type": type(e).__name__
                }
            )
            raise HTTPException(status_code=500, detail=error_response.model_dump())
    
    async def delete_company(self, company_id: str) -> None:
        """Delete a company"""
        try:
            deleted = self.company_repo.delete(company_id)
            if not deleted:
                error_response = ErrorResponse(
                    error_code="COMPANY_NOT_FOUND",
                    message=f"Company with ID {company_id} not found",
                    details={
                        "company_id": company_id,
                        "operation": "delete_company"
                    }
                )
                raise HTTPException(status_code=404, detail=error_response.model_dump())
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to delete company {company_id}: {str(e)}")
            error_response = ErrorResponse(
                error_code="COMPANY_DELETE_FAILED",
                message=f"Failed to delete company: {str(e)}",
                details={
                    "company_id": company_id,
                    "operation": "delete_company",
                    "exception_type": type(e).__name__
                }
            )
            raise HTTPException(status_code=500, detail=error_response.model_dump())
    
    async def link_profile_to_company(self, profile_id: str, company_id: str, request: ProfileCompanyLinkRequest) -> ProfileCompanyRelationship:
        """Link a profile to a company with work experience"""
        try:
            work_experience = {
                "position_title": request.position_title,
                "start_date": request.start_date,
                "end_date": request.end_date,
                "is_current": request.is_current,
                "description": request.description
            }
            
            result = self.company_service.link_profile_to_company(profile_id, company_id, work_experience)
            
            return ProfileCompanyRelationship(
                id=result["id"],
                profile_id=result["profile_id"],
                company_id=result["company_id"],
                position_title=result["position_title"],
                start_date=result.get("start_date"),
                end_date=result.get("end_date"),
                is_current=result.get("is_current", False),
                description=result.get("description"),
                created_at=result["created_at"]
            )
            
        except Exception as e:
            logger.error(f"Failed to link profile {profile_id} to company {company_id}: {str(e)}")
            error_response = ErrorResponse(
                error_code="PROFILE_COMPANY_LINK_FAILED",
                message=f"Failed to link profile to company: {str(e)}",
                details={
                    "profile_id": profile_id,
                    "company_id": company_id,
                    "operation": "link_profile_to_company",
                    "exception_type": type(e).__name__
                }
            )
            raise HTTPException(status_code=500, detail=error_response.model_dump())


# Initialize CompanyController
def get_company_controller():
    return CompanyController(get_db_client())

# ============================================================================
# COMPANY REST API ENDPOINTS
# ============================================================================

@app.get(
    "/api/v1/companies", 
    response_model=CompanyListResponse,
    responses={
        403: {"model": ErrorResponse, "description": "Unauthorized - Invalid API key"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def list_companies(
    name: Optional[str] = Query(None, description="Company name search"),
    domain: Optional[str] = Query(None, description="Domain search"),
    industry: Optional[str] = Query(None, description="Industry filter"),
    city: Optional[str] = Query(None, description="City filter"),
    country: Optional[str] = Query(None, description="Country filter"),
    size_category: Optional[str] = Query(None, description="Size category (startup, small, medium, large, enterprise)"),
    is_startup: Optional[bool] = Query(None, description="Filter for startup companies"),
    limit: int = Query(50, ge=1, le=100, description="Number of companies to return"),
    offset: int = Query(0, ge=0, description="Number of companies to skip"),
    api_key: str = Depends(verify_api_key)
):
    """List companies with optional filtering and pagination"""
    controller = get_company_controller()
    return await controller.list_companies(
        name=name,
        domain=domain,
        industry=industry,
        city=city,
        country=country,
        size_category=size_category,
        is_startup=is_startup,
        limit=limit,
        offset=offset
    )


@app.get(
    "/api/v1/companies/{company_id}", 
    response_model=CompanyResponse,
    responses={
        403: {"model": ErrorResponse, "description": "Unauthorized - Invalid API key"},
        404: {"model": ErrorResponse, "description": "Company not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def get_company(
    company_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Get individual company by ID"""
    controller = get_company_controller()
    return await controller.get_company(company_id)


@app.post(
    "/api/v1/companies", 
    response_model=CompanyResponse, 
    status_code=201,
    responses={
        403: {"model": ErrorResponse, "description": "Unauthorized - Invalid API key"},
        422: {"model": ValidationErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def create_company(
    request: CompanyCreateRequest,
    api_key: str = Depends(verify_api_key)
):
    """Create a new company"""
    controller = get_company_controller()
    return await controller.create_company(request)


@app.put(
    "/api/v1/companies/{company_id}", 
    response_model=CompanyResponse,
    responses={
        403: {"model": ErrorResponse, "description": "Unauthorized - Invalid API key"},
        404: {"model": ErrorResponse, "description": "Company not found"},
        422: {"model": ValidationErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def update_company(
    company_id: str,
    request: CompanyUpdateRequest,
    api_key: str = Depends(verify_api_key)
):
    """Update an existing company"""
    controller = get_company_controller()
    return await controller.update_company(company_id, request)


@app.delete(
    "/api/v1/companies/{company_id}", 
    status_code=204,
    responses={
        403: {"model": ErrorResponse, "description": "Unauthorized - Invalid API key"},
        404: {"model": ErrorResponse, "description": "Company not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def delete_company(
    company_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Delete a company"""
    controller = get_company_controller()
    await controller.delete_company(company_id)
    return None


# ============================================================================
# PROFILE-COMPANY RELATIONSHIP ENDPOINTS
# ============================================================================

@app.post(
    "/api/v1/profiles/{profile_id}/companies/{company_id}/link", 
    response_model=ProfileCompanyRelationship, 
    status_code=201,
    responses={
        403: {"model": ErrorResponse, "description": "Unauthorized - Invalid API key"},
        404: {"model": ErrorResponse, "description": "Profile or company not found"},
        422: {"model": ValidationErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def link_profile_to_company(
    profile_id: str,
    company_id: str,
    request: ProfileCompanyLinkRequest,
    api_key: str = Depends(verify_api_key)
):
    """Link a profile to a company with work experience details"""
    controller = get_company_controller()
    return await controller.link_profile_to_company(profile_id, company_id, request)


@app.delete(
    "/api/v1/profiles/{profile_id}/companies/{company_id}/link", 
    status_code=204,
    responses={
        403: {"model": ErrorResponse, "description": "Unauthorized - Invalid API key"},
        404: {"model": ErrorResponse, "description": "Profile, company, or relationship not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def unlink_profile_from_company(
    profile_id: str,
    company_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Unlink a profile from a company"""
    try:
        controller = get_company_controller()
        controller.company_service.unlink_profile_from_company(profile_id, company_id)
        return None
    except Exception as e:
        logger.error(f"Failed to unlink profile {profile_id} from company {company_id}: {str(e)}")
        error_response = ErrorResponse(
            error_code="PROFILE_COMPANY_UNLINK_FAILED",
            message=f"Failed to unlink profile from company: {str(e)}",
            details={
                "profile_id": profile_id,
                "company_id": company_id,
                "operation": "unlink_profile_from_company",
                "exception_type": type(e).__name__
            }
        )
        raise HTTPException(status_code=500, detail=error_response.model_dump())


@app.get(
    "/api/v1/profiles/{profile_id}/companies", 
    response_model=CompanyListResponse,
    responses={
        403: {"model": ErrorResponse, "description": "Unauthorized - Invalid API key"},
        404: {"model": ErrorResponse, "description": "Profile not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def get_companies_for_profile(
    profile_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Get all companies associated with a profile"""
    try:
        controller = get_company_controller()
        companies = controller.company_service.get_companies_for_profile(profile_id)
        
        # Convert to response format
        company_responses = [controller._convert_canonical_to_response(company) for company in companies]
        
        return CompanyListResponse(
            data=company_responses,
            pagination=PaginationMetadata(
                limit=len(company_responses),
                offset=0,
                total=len(company_responses),
                has_more=False
            )
        )
        
    except Exception as e:
        logger.error(f"Failed to get companies for profile {profile_id}: {str(e)}")
        error_response = ErrorResponse(
            error_code="PROFILE_COMPANIES_FAILED",
            message=f"Failed to get companies for profile: {str(e)}",
            details={
                "profile_id": profile_id,
                "operation": "get_companies_for_profile",
                "exception_type": type(e).__name__
            }
        )
        raise HTTPException(status_code=500, detail=error_response.model_dump())


@app.get(
    "/api/v1/companies/{company_id}/profiles", 
    responses={
        403: {"model": ErrorResponse, "description": "Unauthorized - Invalid API key"},
        404: {"model": ErrorResponse, "description": "Company not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def get_profiles_for_company(
    company_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Get all profiles associated with a company"""
    try:
        controller = get_company_controller()
        profiles = controller.company_repo.get_profiles_for_company(company_id)
        
        return {
            "data": profiles,
            "pagination": {
                "limit": len(profiles),
                "offset": 0,
                "total": len(profiles),
                "has_more": False
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get profiles for company {company_id}: {str(e)}")
        error_response = ErrorResponse(
            error_code="COMPANY_PROFILES_FAILED",
            message=f"Failed to get profiles for company: {str(e)}",
            details={
                "company_id": company_id,
                "operation": "get_profiles_for_company",
                "exception_type": type(e).__name__
            }
        )
        raise HTTPException(status_code=500, detail=error_response.model_dump())


# Initialize Scoring Controllers
def get_profile_scoring_controller():
    return ProfileScoringController()

def get_scoring_job_controller():
    return ScoringJobController()

# Initialize Template Service
def get_template_service():
    return TemplateService(supabase_client=get_db_client())

# Initialize Template Versioning Service
def get_template_versioning_service():
    return TemplateVersioningService(supabase_client=get_db_client())


# V1.85 LLM Profile Scoring Endpoints
@app.post(
    "/api/v1/profiles/{profile_id}/score",
    response_model=ScoringResponse,
    status_code=201,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid profile ID or malformed request"},
        403: {"model": ErrorResponse, "description": "Unauthorized - Invalid API key"},
        404: {"model": ErrorResponse, "description": "Profile not found"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def create_scoring_job(
    profile_id: str,
    request: ScoringRequest,
    api_key: str = Depends(verify_api_key)
):
    """Initiate LLM-based scoring evaluation for a LinkedIn profile"""
    controller = get_profile_scoring_controller()
    return await controller.create_scoring_job(profile_id, request)


@app.get(
    "/api/v1/scoring-jobs/{job_id}",
    response_model=ScoringResponse,
    responses={
        403: {"model": ErrorResponse, "description": "Unauthorized - Invalid API key"},
        404: {"model": ErrorResponse, "description": "Job not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def get_scoring_job_status(
    job_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Check the status and retrieve results of a scoring job"""
    controller = get_scoring_job_controller()
    response = await controller.get_job_status(job_id)
    return JSONResponse(
        status_code=200,
        content=jsonable_encoder(response, exclude_none=True)
    )


@app.get(
    "/api/v1/scoring-jobs",
    responses={
        403: {"model": ErrorResponse, "description": "Unauthorized - Invalid API key"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def list_scoring_jobs(
    limit: int = Query(50, ge=1, le=100, description="Number of jobs to return"),
    offset: int = Query(0, ge=0, description="Number of jobs to skip"),
    status: Optional[str] = Query(None, description="Filter by job status"),
    api_key: str = Depends(verify_api_key)
):
    """List scoring jobs for dashboard"""
    controller = get_scoring_job_controller()
    return await controller.list_jobs(limit=limit, offset=offset, status_filter=status)


@app.post(
    "/api/v1/scoring-jobs/{job_id}/retry",
    response_model=ScoringResponse,
    status_code=200,
    responses={
        400: {"model": ErrorResponse, "description": "Job not in failed state or retry limit exceeded"},
        403: {"model": ErrorResponse, "description": "Unauthorized - Invalid API key"},
        404: {"model": ErrorResponse, "description": "Job not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def retry_scoring_job(
    job_id: str,
    retry_request: Optional[JobRetryRequest] = None,
    api_key: str = Depends(verify_api_key)
):
    """Retry a failed scoring job"""
    controller = get_scoring_job_controller()
    return await controller.retry_job(job_id, retry_request)


# V1.88 Template-based Scoring Endpoint
@app.post(
    "/api/v1/profiles/{profile_id}/score-template",
    response_model=ScoringResponse,
    status_code=201,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid profile ID, template ID, or malformed request"},
        403: {"model": ErrorResponse, "description": "Unauthorized - Invalid API key"},
        404: {"model": ErrorResponse, "description": "Profile or template not found"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def create_template_scoring_job(
    profile_id: str,
    request: EnhancedScoringRequest,
    api_key: str = Depends(verify_api_key)
):
    """Create LLM scoring job with template-based OR prompt-based evaluation (V1.88)"""
    controller = get_profile_scoring_controller()
    return await controller.create_template_scoring_job(profile_id, request)


# ============================================================================
# V1.88 TEMPLATE MANAGEMENT API ENDPOINTS
# ============================================================================

@app.get(
    "/api/v1/templates",
    response_model=TemplateListResponse,
    responses={
        403: {"model": ErrorResponse, "description": "Unauthorized - Invalid API key"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def list_templates(
    category: Optional[str] = Query(None, description="Filter by template category (CTO, CIO, CISO, etc.)"),
    include_inactive: bool = Query(False, description="Include inactive templates in results"),
    limit: Optional[int] = Query(None, ge=1, le=100, description="Maximum number of templates to return"),
    api_key: str = Depends(verify_api_key)
):
    """List prompt templates with optional filtering"""
    try:
        service = get_template_service()
        templates = await service.list_templates(
            category=category,
            include_inactive=include_inactive,
            limit=limit
        )
        
        return TemplateListResponse(
            templates=templates,
            count=len(templates)
        )
        
    except Exception as e:
        logger.error(
            f"Failed to list templates: {str(e)}",
            extra={
                "category": category,
                "include_inactive": include_inactive,
                "limit": limit,
                "exception_type": type(e).__name__
            }
        )
        error_response = ErrorResponse(
            error_code="TEMPLATE_LIST_FAILED",
            message=f"Failed to retrieve templates: {str(e)}",
            details={
                "operation": "list_templates",
                "category": category,
                "exception_type": type(e).__name__
            }
        )
        raise HTTPException(status_code=500, detail=error_response.model_dump())


@app.get(
    "/api/v1/templates/summaries",
    response_model=TemplateListSummaryResponse,
    responses={
        403: {"model": ErrorResponse, "description": "Unauthorized - Invalid API key"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def list_template_summaries(
    category: Optional[str] = Query(None, description="Filter by template category"),
    include_inactive: bool = Query(False, description="Include inactive templates"),
    limit: Optional[int] = Query(None, ge=1, le=100, description="Maximum number of summaries to return"),
    api_key: str = Depends(verify_api_key)
):
    """List template summaries (without full prompt text) for performance"""
    try:
        service = get_template_service()
        summaries = await service.list_template_summaries(
            category=category,
            include_inactive=include_inactive,
            limit=limit
        )
        
        return TemplateListSummaryResponse(
            templates=summaries,
            count=len(summaries)
        )
        
    except Exception as e:
        logger.error(
            f"Failed to list template summaries: {str(e)}",
            extra={
                "category": category,
                "include_inactive": include_inactive,
                "limit": limit,
                "exception_type": type(e).__name__
            }
        )
        error_response = ErrorResponse(
            error_code="TEMPLATE_SUMMARIES_FAILED",
            message=f"Failed to retrieve template summaries: {str(e)}",
            details={
                "operation": "list_template_summaries",
                "category": category,
                "exception_type": type(e).__name__
            }
        )
        raise HTTPException(status_code=500, detail=error_response.model_dump())


@app.get(
    "/api/v1/templates/{template_id}",
    response_model=PromptTemplate,
    responses={
        403: {"model": ErrorResponse, "description": "Unauthorized - Invalid API key"},
        404: {"model": ErrorResponse, "description": "Template not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def get_template(
    template_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Get a specific template by ID"""
    try:
        service = get_template_service()
        template = await service.get_template_by_id(template_id)
        
        if not template:
            error_response = ErrorResponse(
                error_code="TEMPLATE_NOT_FOUND",
                message=f"Template with ID {template_id} not found",
                details={
                    "template_id": template_id,
                    "operation": "get_template"
                }
            )
            raise HTTPException(status_code=404, detail=error_response.model_dump())
        
        return template
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 404)
        raise
    except Exception as e:
        logger.error(
            f"Failed to get template {template_id}: {str(e)}",
            extra={
                "template_id": template_id,
                "exception_type": type(e).__name__
            }
        )
        error_response = ErrorResponse(
            error_code="TEMPLATE_RETRIEVAL_FAILED",
            message=f"Failed to retrieve template: {str(e)}",
            details={
                "template_id": template_id,
                "operation": "get_template",
                "exception_type": type(e).__name__
            }
        )
        raise HTTPException(status_code=500, detail=error_response.model_dump())


@app.post(
    "/api/v1/templates",
    response_model=PromptTemplate,
    status_code=201,
    responses={
        403: {"model": ErrorResponse, "description": "Unauthorized - Invalid API key"},
        422: {"model": ValidationErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def create_template(
    request: CreateTemplateRequest,
    api_key: str = Depends(verify_api_key)
):
    """Create a new prompt template"""
    try:
        service = get_template_service()
        template = await service.create_template(request)
        
        logger.info(
            f"Template created successfully",
            extra={
                "template_id": str(template.id),
                "template_name": template.name,
                "category": template.category
            }
        )
        
        return template
        
    except Exception as e:
        logger.error(
            f"Failed to create template: {str(e)}",
            extra={
                "template_name": request.name,
                "category": request.category,
                "exception_type": type(e).__name__
            }
        )
        error_response = ErrorResponse(
            error_code="TEMPLATE_CREATION_FAILED",
            message=f"Failed to create template: {str(e)}",
            details={
                "template_name": request.name,
                "category": request.category,
                "operation": "create_template",
                "exception_type": type(e).__name__
            }
        )
        raise HTTPException(status_code=500, detail=error_response.model_dump())


@app.put(
    "/api/v1/templates/{template_id}",
    response_model=PromptTemplate,
    responses={
        403: {"model": ErrorResponse, "description": "Unauthorized - Invalid API key"},
        404: {"model": ErrorResponse, "description": "Template not found"},
        422: {"model": ValidationErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def update_template(
    template_id: str,
    request: UpdateTemplateRequest,
    api_key: str = Depends(verify_api_key)
):
    """Update an existing template"""
    try:
        service = get_template_service()
        template = await service.update_template(template_id, request)
        
        if not template:
            error_response = ErrorResponse(
                error_code="TEMPLATE_NOT_FOUND",
                message=f"Template with ID {template_id} not found",
                details={
                    "template_id": template_id,
                    "operation": "update_template"
                }
            )
            raise HTTPException(status_code=404, detail=error_response.model_dump())
        
        logger.info(
            f"Template updated successfully",
            extra={
                "template_id": template_id,
                "template_name": template.name
            }
        )
        
        return template
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 404)
        raise
    except Exception as e:
        logger.error(
            f"Failed to update template {template_id}: {str(e)}",
            extra={
                "template_id": template_id,
                "exception_type": type(e).__name__
            }
        )
        error_response = ErrorResponse(
            error_code="TEMPLATE_UPDATE_FAILED",
            message=f"Failed to update template: {str(e)}",
            details={
                "template_id": template_id,
                "operation": "update_template",
                "exception_type": type(e).__name__
            }
        )
        raise HTTPException(status_code=500, detail=error_response.model_dump())


@app.delete(
    "/api/v1/templates/{template_id}",
    response_model=DeleteTemplateResponse,
    responses={
        403: {"model": ErrorResponse, "description": "Unauthorized - Invalid API key"},
        404: {"model": ErrorResponse, "description": "Template not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def delete_template(
    template_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Soft delete a template (sets is_active to False)"""
    try:
        service = get_template_service()
        deleted = await service.delete_template(template_id)
        
        if not deleted:
            error_response = ErrorResponse(
                error_code="TEMPLATE_NOT_FOUND",
                message=f"Template with ID {template_id} not found",
                details={
                    "template_id": template_id,
                    "operation": "delete_template"
                }
            )
            raise HTTPException(status_code=404, detail=error_response.model_dump())
        
        logger.info(
            f"Template soft deleted successfully",
            extra={"template_id": template_id}
        )
        
        return DeleteTemplateResponse(
            message="Template successfully deactivated",
            template_id=template_id
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 404)
        raise
    except Exception as e:
        logger.error(
            f"Failed to delete template {template_id}: {str(e)}",
            extra={
                "template_id": template_id,
                "exception_type": type(e).__name__
            }
        )
        error_response = ErrorResponse(
            error_code="TEMPLATE_DELETE_FAILED",
            message=f"Failed to delete template: {str(e)}",
            details={
                "template_id": template_id,
                "operation": "delete_template",
                "exception_type": type(e).__name__
            }
        )
        raise HTTPException(status_code=500, detail=error_response.model_dump())


# ============================================================================
# V1.90 ROLE-BASED TEMPLATE RECOMMENDATION ENDPOINTS
# ============================================================================

@app.get(
    "/api/v1/profiles/{profile_id}/recommended-templates",
    response_model=TemplateListResponse,
    responses={
        403: {"model": ErrorResponse, "description": "Unauthorized - Invalid API key"},
        404: {"model": ErrorResponse, "description": "Profile not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def get_recommended_templates_for_profile(
    profile_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Get template recommendations based on profile's suggested role"""
    try:
        # Get the profile to determine the suggested role
        db_client = get_db_client()
        profile = await db_client.get_profile_by_id(profile_id)
        
        if not profile:
            error_response = ErrorResponse(
                error_code="PROFILE_NOT_FOUND",
                message=f"Profile with ID {profile_id} not found",
                details={
                    "profile_id": profile_id,
                    "operation": "get_recommended_templates"
                }
            )
            raise HTTPException(status_code=404, detail=error_response.model_dump())
        
        # Get the suggested role from profile
        suggested_role = profile.get("suggested_role")
        if not suggested_role:
            # If no suggested role, return all templates
            service = get_template_service()
            templates = await service.list_templates(include_inactive=False, limit=10)
            
            logger.info(
                f"No suggested role for profile, returning general templates",
                extra={
                    "profile_id": profile_id,
                    "template_count": len(templates)
                }
            )
        else:
            # Get role-specific templates
            service = get_template_service()
            templates = await service.get_templates_for_role(suggested_role)
            
            logger.info(
                f"Retrieved role-based template recommendations",
                extra={
                    "profile_id": profile_id,
                    "suggested_role": suggested_role,
                    "template_count": len(templates)
                }
            )
        
        return TemplateListResponse(
            templates=templates,
            count=len(templates)
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 404)
        raise
    except Exception as e:
        logger.error(
            f"Failed to get template recommendations for profile {profile_id}: {str(e)}",
            extra={
                "profile_id": profile_id,
                "exception_type": type(e).__name__
            }
        )
        error_response = ErrorResponse(
            error_code="TEMPLATE_RECOMMENDATION_FAILED",
            message=f"Failed to get template recommendations: {str(e)}",
            details={
                "profile_id": profile_id,
                "operation": "get_recommended_templates",
                "exception_type": type(e).__name__
            }
        )
        raise HTTPException(status_code=500, detail=error_response.model_dump())


@app.get(
    "/api/v1/profiles/{profile_id}/default-template",
    response_model=PromptTemplate,
    responses={
        403: {"model": ErrorResponse, "description": "Unauthorized - Invalid API key"},
        404: {"model": ErrorResponse, "description": "Profile or default template not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def get_default_template_for_profile(
    profile_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Get the default template recommendation for a profile's role"""
    try:
        # Get the profile to determine the suggested role
        db_client = get_db_client()
        profile = await db_client.get_profile_by_id(profile_id)
        
        if not profile:
            error_response = ErrorResponse(
                error_code="PROFILE_NOT_FOUND",
                message=f"Profile with ID {profile_id} not found",
                details={
                    "profile_id": profile_id,
                    "operation": "get_default_template"
                }
            )
            raise HTTPException(status_code=404, detail=error_response.model_dump())
        
        # Get the suggested role from profile
        suggested_role = profile.get("suggested_role")
        if not suggested_role:
            error_response = ErrorResponse(
                error_code="NO_SUGGESTED_ROLE",
                message="Profile has no suggested role for template recommendation",
                details={
                    "profile_id": profile_id,
                    "suggestion": "Use the general templates endpoint or specify a role"
                }
            )
            raise HTTPException(status_code=404, detail=error_response.model_dump())
        
        # Get the default template for the role
        service = get_template_service()
        default_template = await service.get_default_template_for_role(suggested_role)
        
        if not default_template:
            error_response = ErrorResponse(
                error_code="NO_DEFAULT_TEMPLATE",
                message=f"No default template found for role {suggested_role}",
                details={
                    "profile_id": profile_id,
                    "suggested_role": suggested_role,
                    "suggestion": f"Create templates for the {suggested_role} category"
                }
            )
            raise HTTPException(status_code=404, detail=error_response.model_dump())
        
        logger.info(
            f"Default template retrieved for profile role",
            extra={
                "profile_id": profile_id,
                "suggested_role": suggested_role,
                "template_id": str(default_template.id),
                "template_name": default_template.name
            }
        )
        
        return default_template
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 404)
        raise
    except Exception as e:
        logger.error(
            f"Failed to get default template for profile {profile_id}: {str(e)}",
            extra={
                "profile_id": profile_id,
                "exception_type": type(e).__name__
            }
        )
        error_response = ErrorResponse(
            error_code="DEFAULT_TEMPLATE_RETRIEVAL_FAILED",
            message=f"Failed to get default template: {str(e)}",
            details={
                "profile_id": profile_id,
                "operation": "get_default_template",
                "exception_type": type(e).__name__
            }
        )
        raise HTTPException(status_code=500, detail=error_response.model_dump())


# ============================================================================
# V1.9 TEMPLATE VERSIONING API ENDPOINTS
# ============================================================================

@app.get(
    "/api/v1/templates/{template_id}/versions",
    response_model=List[PromptTemplate],
    responses={
        403: {"model": ErrorResponse, "description": "Unauthorized - Invalid API key"},
        404: {"model": ErrorResponse, "description": "Template not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def get_template_versions(
    template_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Get version history for a template"""
    try:
        versioning_service = get_template_versioning_service()
        versions = await versioning_service.get_version_history(template_id)
        
        if not versions:
            error_response = ErrorResponse(
                error_code="TEMPLATE_NOT_FOUND",
                message=f"Template with ID {template_id} not found",
                details={
                    "template_id": template_id,
                    "operation": "get_template_versions"
                }
            )
            raise HTTPException(status_code=404, detail=error_response.model_dump())
        
        logger.info(
            f"Retrieved version history for template",
            extra={
                "template_id": template_id,
                "version_count": len(versions)
            }
        )
        
        return versions
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 404)
        raise
    except Exception as e:
        logger.error(
            f"Failed to get template versions {template_id}: {str(e)}",
            extra={
                "template_id": template_id,
                "exception_type": type(e).__name__
            }
        )
        error_response = ErrorResponse(
            error_code="TEMPLATE_VERSIONS_FAILED",
            message=f"Failed to retrieve template versions: {str(e)}",
            details={
                "template_id": template_id,
                "operation": "get_template_versions",
                "exception_type": type(e).__name__
            }
        )
        raise HTTPException(status_code=500, detail=error_response.model_dump())


@app.post(
    "/api/v1/templates/{template_id}/versions",
    response_model=PromptTemplate,
    status_code=201,
    responses={
        403: {"model": ErrorResponse, "description": "Unauthorized - Invalid API key"},
        404: {"model": ErrorResponse, "description": "Template not found"},
        422: {"model": ValidationErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def create_template_version(
    template_id: str,
    request: UpdateTemplateRequest,
    api_key: str = Depends(verify_api_key)
):
    """Create a new version of an existing template"""
    try:
        versioning_service = get_template_versioning_service()
        new_version = await versioning_service.create_new_version(template_id, request)
        
        if not new_version:
            error_response = ErrorResponse(
                error_code="TEMPLATE_NOT_FOUND",
                message=f"Template with ID {template_id} not found",
                details={
                    "template_id": template_id,
                    "operation": "create_template_version"
                }
            )
            raise HTTPException(status_code=404, detail=error_response.model_dump())
        
        logger.info(
            f"New template version created successfully",
            extra={
                "template_id": template_id,
                "new_version": new_version.version,
                "template_name": new_version.name
            }
        )
        
        return new_version
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 404)
        raise
    except Exception as e:
        logger.error(
            f"Failed to create new version for template {template_id}: {str(e)}",
            extra={
                "template_id": template_id,
                "exception_type": type(e).__name__
            }
        )
        error_response = ErrorResponse(
            error_code="TEMPLATE_VERSION_CREATION_FAILED",
            message=f"Failed to create template version: {str(e)}",
            details={
                "template_id": template_id,
                "operation": "create_template_version",
                "exception_type": type(e).__name__
            }
        )
        raise HTTPException(status_code=500, detail=error_response.model_dump())


@app.get(
    "/api/v1/templates/{template_id}/versions/{version}/diff/{compare_version}",
    responses={
        403: {"model": ErrorResponse, "description": "Unauthorized - Invalid API key"},
        404: {"model": ErrorResponse, "description": "Template or version not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def compare_template_versions(
    template_id: str,
    version: int,
    compare_version: int,
    api_key: str = Depends(verify_api_key)
):
    """Compare two versions of a template"""
    try:
        versioning_service = get_template_versioning_service()
        diff_result = await versioning_service.compare_versions(
            template_id, version, compare_version
        )
        
        if not diff_result:
            error_response = ErrorResponse(
                error_code="VERSION_NOT_FOUND",
                message=f"One or both versions not found for template {template_id}",
                details={
                    "template_id": template_id,
                    "version": version,
                    "compare_version": compare_version,
                    "operation": "compare_template_versions"
                }
            )
            raise HTTPException(status_code=404, detail=error_response.model_dump())
        
        logger.info(
            f"Template versions compared successfully",
            extra={
                "template_id": template_id,
                "version": version,
                "compare_version": compare_version
            }
        )
        
        return diff_result
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 404)
        raise
    except Exception as e:
        logger.error(
            f"Failed to compare template versions {template_id} v{version} vs v{compare_version}: {str(e)}",
            extra={
                "template_id": template_id,
                "version": version,
                "compare_version": compare_version,
                "exception_type": type(e).__name__
            }
        )
        error_response = ErrorResponse(
            error_code="TEMPLATE_COMPARISON_FAILED",
            message=f"Failed to compare template versions: {str(e)}",
            details={
                "template_id": template_id,
                "version": version,
                "compare_version": compare_version,
                "operation": "compare_template_versions",
                "exception_type": type(e).__name__
            }
        )
        raise HTTPException(status_code=500, detail=error_response.model_dump())


@app.post(
    "/api/v1/templates/{template_id}/versions/{version}/restore",
    response_model=PromptTemplate,
    status_code=200,
    responses={
        403: {"model": ErrorResponse, "description": "Unauthorized - Invalid API key"},
        404: {"model": ErrorResponse, "description": "Template or version not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def restore_template_version(
    template_id: str,
    version: int,
    api_key: str = Depends(verify_api_key)
):
    """Restore a previous version of a template as the current active version"""
    try:
        versioning_service = get_template_versioning_service()
        restored_template = await versioning_service.restore_version(template_id, version)
        
        if not restored_template:
            error_response = ErrorResponse(
                error_code="VERSION_NOT_FOUND",
                message=f"Version {version} not found for template {template_id}",
                details={
                    "template_id": template_id,
                    "version": version,
                    "operation": "restore_template_version"
                }
            )
            raise HTTPException(status_code=404, detail=error_response.model_dump())
        
        logger.info(
            f"Template version restored successfully",
            extra={
                "template_id": template_id,
                "restored_from_version": version,
                "new_version": restored_template.version
            }
        )
        
        return restored_template
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 404)
        raise
    except Exception as e:
        logger.error(
            f"Failed to restore template version {template_id} v{version}: {str(e)}",
            extra={
                "template_id": template_id,
                "version": version,
                "exception_type": type(e).__name__
            }
        )
        error_response = ErrorResponse(
            error_code="TEMPLATE_RESTORE_FAILED",
            message=f"Failed to restore template version: {str(e)}",
            details={
                "template_id": template_id,
                "version": version,
                "operation": "restore_template_version",
                "exception_type": type(e).__name__
            }
        )
        raise HTTPException(status_code=500, detail=error_response.model_dump())


@app.post(
    "/api/v1/templates/{template_id}/versions/{version}/activate",
    response_model=PromptTemplate,
    status_code=200,
    responses={
        403: {"model": ErrorResponse, "description": "Unauthorized - Invalid API key"},
        404: {"model": ErrorResponse, "description": "Template or version not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def set_active_template_version(
    template_id: str,
    version: int,
    api_key: str = Depends(verify_api_key)
):
    """Set a specific version as the active version for a template"""
    try:
        versioning_service = get_template_versioning_service()
        active_template = await versioning_service.set_active_version(template_id, version)
        
        if not active_template:
            error_response = ErrorResponse(
                error_code="VERSION_NOT_FOUND",
                message=f"Version {version} not found for template {template_id}",
                details={
                    "template_id": template_id,
                    "version": version,
                    "operation": "set_active_template_version"
                }
            )
            raise HTTPException(status_code=404, detail=error_response.model_dump())
        
        logger.info(
            f"Template active version set successfully",
            extra={
                "template_id": template_id,
                "active_version": version
            }
        )
        
        return active_template
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 404)
        raise
    except Exception as e:
        logger.error(
            f"Failed to set active version for template {template_id} v{version}: {str(e)}",
            extra={
                "template_id": template_id,
                "version": version,
                "exception_type": type(e).__name__
            }
        )
        error_response = ErrorResponse(
            error_code="TEMPLATE_ACTIVATE_FAILED",
            message=f"Failed to set active template version: {str(e)}",
            details={
                "template_id": template_id,
                "version": version,
                "operation": "set_active_template_version",
                "exception_type": type(e).__name__
            }
        )
        raise HTTPException(status_code=500, detail=error_response.model_dump())


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=False,
    )
