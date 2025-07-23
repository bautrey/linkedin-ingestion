"""
LinkedIn Ingestion Service

A FastAPI microservice for ingesting LinkedIn profiles and company data
using Cassidy AI workflows and storing in Supabase with pgvector.
"""

import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import Dict, Any
from datetime import datetime

from app.cassidy.client import CassidyClient
from app.database.supabase_client import SupabaseClient
from app.core.config import settings

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

# Request/Response models
class ProfileIngestRequest(BaseModel):
    linkedin_url: HttpUrl
    
class ProfileIngestResponse(BaseModel):
    success: bool
    message: str
    profile_id: str = None
    record_id: str = None


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "LinkedIn Ingestion Service",
        "version": settings.VERSION,
        "status": "running",
        "docs_url": "/docs" if settings.ENVIRONMENT != "production" else None,
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


@app.post("/api/v1/profiles/ingest", response_model=ProfileIngestResponse)
async def ingest_profile(request: ProfileIngestRequest):
    """Ingest a LinkedIn profile"""
    try:
        # Fetch profile from Cassidy
        profile = await get_cassidy_client().fetch_profile(str(request.linkedin_url))
        
        # Store in database
        record_id = await get_db_client().store_profile(profile)
        
        return ProfileIngestResponse(
            success=True,
            message="Profile ingested successfully",
            profile_id=profile.id,
            record_id=record_id
        )
        
    except Exception as e:
        raise HTTPException(status_code=422, detail={
            "success": False,
            "message": f"Failed to ingest profile: {str(e)}",
            "error_type": type(e).__name__
        })


@app.get("/api/v1/profiles/recent")
async def get_recent_profiles(limit: int = 10):
    """Get recently ingested profiles"""
    try:
        profiles = await get_db_client().list_recent_profiles(limit=limit)
        
        return {
            "profiles": profiles,
            "count": len(profiles),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "error": str(e),
            "message": "Failed to retrieve recent profiles"
        })


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Disabled for testing
        log_config=None,  # Use structlog instead
    )
