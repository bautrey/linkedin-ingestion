"""
LinkedIn Ingestion Service

A FastAPI microservice for ingesting LinkedIn profiles and company data
using Cassidy AI workflows and storing in Supabase with pgvector.
"""

import asyncio
import os
import uuid
from fastapi import FastAPI, HTTPException, Header, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl, Field
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.cassidy.client import CassidyClient
from app.cassidy.workflows import LinkedInWorkflow
from app.cassidy.models import ProfileIngestionRequest
from app.database.supabase_client import SupabaseClient
from app.core.config import settings


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
        raise HTTPException(
            status_code=403, 
            detail={
                "error": "Unauthorized",
                "message": "Invalid or missing API key"
            }
        )
    return x_api_key

# Request/Response models for REST API
class ProfileCreateRequest(BaseModel):
    linkedin_url: HttpUrl
    name: Optional[str] = None
    include_companies: bool = Field(default=True, description="Include company profiles for all experience entries")

class PaginationMetadata(BaseModel):
    limit: int
    offset: int
    total: Optional[int] = None
    has_more: bool = False

class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None

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
    current_company: Optional[Dict[str, Any]] = None
    experience: List[Dict[str, Any]] = []
    education: List[Dict[str, Any]] = []
    certifications: List[Dict[str, Any]] = []
    created_at: str
    timestamp: Optional[str] = None

class ProfileListResponse(BaseModel):
    data: List[ProfileResponse]
    pagination: PaginationMetadata

# ProfileController class for REST endpoints
class ProfileController:
    """Controller for profile-related REST operations"""
    
    def __init__(self, db_client, cassidy_client, linkedin_workflow):
        self.db_client = db_client
        self.cassidy_client = cassidy_client
        self.linkedin_workflow = linkedin_workflow
    
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
            current_company=db_profile.get("current_company"),
            experience=db_profile.get("experience", []),
            education=db_profile.get("education", []),
            certifications=db_profile.get("certifications", []),
            created_at=db_profile["created_at"],
            timestamp=db_profile.get("timestamp")
        )
    
    async def list_profiles(
        self,
        linkedin_url: Optional[str] = None,
        name: Optional[str] = None,
        company: Optional[str] = None,
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
            raise HTTPException(status_code=404, detail={
                "error": "Not Found",
                "message": f"Profile with ID {profile_id} not found"
            })
        
        return self._convert_db_profile_to_response(profile)
    
    async def create_profile(self, request: ProfileCreateRequest) -> ProfileResponse:
        """Create or update profile with smart duplicate handling"""
        # Normalize LinkedIn URL to consistent format
        linkedin_url = normalize_linkedin_url(str(request.linkedin_url))
        
        # Check for existing profile with normalized URL
        existing = await self.db_client.get_profile_by_url(linkedin_url)
        
        if existing:
            # Smart profile management: Update existing profile with latest data
            # Delete the existing profile and create fresh one with latest LinkedIn data
            await self.db_client.delete_profile(existing["id"])
        
        # Create workflow request with user's company inclusion preference
        workflow_request = ProfileIngestionRequest(
            linkedin_url=request.linkedin_url,
            include_companies=request.include_companies
        )
        
        # Process profile through workflow for complete data
        request_id, enriched_profile = await self.linkedin_workflow.process_profile(workflow_request)
        
        # Store in database using the enriched profile data
        record_id = await self.db_client.store_profile(enriched_profile.profile)
        
        # Retrieve the stored profile to return consistent data
        stored_profile = await self.db_client.get_profile_by_id(record_id)
        return self._convert_db_profile_to_response(stored_profile)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "LinkedIn Ingestion Service",
        "version": settings.VERSION,
        "status": "running",
        "docs_url": "/docs" if settings.ENVIRONMENT != "production" else None,
        "deployment_timestamp": datetime.utcnow().isoformat()
    }


@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check database connectivity
        db_health = await get_db_client().health_check()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": settings.VERSION,
            "database": db_health,
            "environment": settings.ENVIRONMENT
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail={
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        })


# Initialize ProfileController
def get_profile_controller():
    return ProfileController(get_db_client(), get_cassidy_client(), get_linkedin_workflow())

# New REST API endpoints
@app.get("/api/v1/profiles", response_model=ProfileListResponse)
async def list_profiles(
    linkedin_url: Optional[str] = Query(None, description="Exact LinkedIn URL search"),
    name: Optional[str] = Query(None, description="Partial name search (case-insensitive)"),
    company: Optional[str] = Query(None, description="Partial company name search (case-insensitive)"),
    limit: int = Query(50, ge=1, le=100, description="Number of profiles to return"),
    offset: int = Query(0, ge=0, description="Number of profiles to skip"),
    api_key: str = Depends(verify_api_key)
):
    """List profiles with optional filtering and pagination"""
    controller = get_profile_controller()
    return await controller.list_profiles(
        linkedin_url=linkedin_url,
        name=name,
        company=company,
        limit=limit,
        offset=offset
    )

@app.get("/api/v1/profiles/{profile_id}", response_model=ProfileResponse)
async def get_profile(
    profile_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Get individual profile by ID"""
    controller = get_profile_controller()
    return await controller.get_profile(profile_id)

@app.post("/api/v1/profiles", response_model=ProfileResponse, status_code=201)
async def create_profile(
    request: ProfileCreateRequest,
    api_key: str = Depends(verify_api_key)
):
    """Create a new profile by ingesting from LinkedIn"""
    controller = get_profile_controller()
    return await controller.create_profile(request)


@app.delete("/api/v1/profiles/{profile_id}", status_code=204)
async def delete_profile(
    profile_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Delete an individual profile by ID"""
    try:
        controller = get_profile_controller()
        deleted = await controller.db_client.delete_profile(profile_id)
        
        if not deleted:
            raise HTTPException(
                status_code=404, 
                detail={
                    "error": "Not Found",
                    "message": f"Profile with ID {profile_id} not found"
                }
            )
        
        # Return empty response for 204 No Content
        return None
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 404)
        raise
    except Exception as e:
        # Handle database and other errors
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal Server Error",
                "message": f"Failed to delete profile: {str(e)}"
            }
        )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=False,
    )
