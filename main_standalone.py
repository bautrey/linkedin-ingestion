"""
LinkedIn Ingestion Service - Standalone Version for Railway Deployment

A FastAPI microservice for ingesting LinkedIn profiles and company data
using Cassidy AI workflows and storing in Supabase with pgvector.
"""

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import Dict, Any, Optional
from datetime import datetime
import httpx
from supabase import create_client, Client

# Configuration
class Settings:
    VERSION = "1.0.0"
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    
    # Supabase
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
    SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
    
    # CORS
    ALLOWED_ORIGINS = ["*"]  # Configure appropriately for production

settings = Settings()

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

# Initialize Supabase client
supabase_client: Optional[Client] = None

def get_supabase_client():
    global supabase_client
    if supabase_client is None and settings.SUPABASE_URL and settings.SUPABASE_ANON_KEY:
        supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
    return supabase_client

# Request/Response models
class ProfileIngestRequest(BaseModel):
    linkedin_url: HttpUrl
    
class ProfileIngestResponse(BaseModel):
    success: bool
    message: str
    profile_id: Optional[str] = None
    record_id: Optional[str] = None

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
        # Basic health check
        db_status = "not_configured"
        if settings.SUPABASE_URL and settings.SUPABASE_ANON_KEY:
            try:
                client = get_supabase_client()
                if client:
                    # Simple test query
                    result = client.from_("profiles").select("id").limit(1).execute()
                    db_status = "connected"
            except Exception as db_error:
                db_status = f"error: {str(db_error)}"
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": settings.VERSION,
            "database": {"status": db_status, "provider": "supabase"},
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
        # For now, return a mock response since we need to configure Cassidy and database
        return ProfileIngestResponse(
            success=True,
            message=f"Profile ingestion endpoint is working. LinkedIn URL: {request.linkedin_url}",
            profile_id="mock_profile_id",
            record_id="mock_record_id"
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
        # Mock response for now
        return {
            "profiles": [
                {
                    "id": "mock_profile_1",
                    "name": "Test Profile",
                    "linkedin_url": "https://linkedin.com/in/test",
                    "created_at": datetime.utcnow().isoformat()
                }
            ],
            "count": 1,
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
        "main_standalone:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=False,
    )
