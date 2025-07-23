"""
Services package for LinkedIn data ingestion

Provides high-level orchestration and pipeline services
"""

from .linkedin_pipeline import LinkedInDataPipeline

__all__ = [
    "LinkedInDataPipeline",
]
