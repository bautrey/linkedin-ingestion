"""
Adapters package for external data source integration.

This package contains adapters that transform external API responses
into our internal canonical data models, providing a decoupling layer
that allows us to easily switch data providers.
"""

from .exceptions import IncompleteDataError
from .cassidy_adapter import CassidyAdapter

__all__ = [
    "IncompleteDataError",
    "CassidyAdapter",
]
