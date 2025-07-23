"""
Profile API endpoints - Placeholder for implementation
"""

from fastapi import APIRouter
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/profiles")
async def list_profiles():
    """List all profiles - TODO: Implement"""
    return {"message": "Profile listing endpoint - Coming soon"}


@router.post("/profiles/ingest")
async def ingest_profile():
    """Ingest LinkedIn profile - TODO: Implement"""
    return {"message": "Profile ingestion endpoint - Coming soon"}
