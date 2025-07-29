"""
Models package for LinkedIn Ingestion Service

Contains Pydantic models for request/response validation and API documentation.
"""

from .errors import ErrorResponse

__all__ = ["ErrorResponse"]
