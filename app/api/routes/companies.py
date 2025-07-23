"""
Company API endpoints - Placeholder for implementation
"""

from fastapi import APIRouter
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/companies")
async def list_companies():
    """List all companies - TODO: Implement"""
    return {"message": "Company listing endpoint - Coming soon"}


@router.post("/companies/ingest")
async def ingest_company():
    """Ingest company profile - TODO: Implement"""
    return {"message": "Company ingestion endpoint - Coming soon"}
