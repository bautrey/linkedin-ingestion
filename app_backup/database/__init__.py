"""
Database integration package for LinkedIn profile and company storage

Provides Supabase client, vector embeddings, and data persistence
"""

from .supabase_client import SupabaseClient
from .embeddings import EmbeddingService

__all__ = [
    "SupabaseClient",
    "EmbeddingService",
]

# Database module
