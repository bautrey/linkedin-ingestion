"""
Exception classes for adapter infrastructure.

This module defines custom exceptions that can be raised during
data transformation processes when essential fields are missing
or data quality issues are detected.
"""

from typing import List


class IncompleteDataError(Exception):
    """
    Raised when essential fields are missing from external API responses.
    
    This exception is used to indicate that the external data source
    (e.g., Cassidy API) has not provided all the required fields needed
    to create a complete canonical model instance.
    
    Attributes:
        missing_fields: List of field names that are missing or empty
    """
    
    def __init__(self, missing_fields: List[str]):
        """
        Initialize the IncompleteDataError.
        
        Args:
            missing_fields: List of field names that are missing or empty
        """
        self.missing_fields = missing_fields
        
        if not missing_fields:
            message = "Missing essential profile fields: No missing fields specified"
        else:
            field_list = ", ".join(missing_fields)
            message = f"Missing essential profile fields: {field_list}"
            
        super().__init__(message)
    
    def __str__(self) -> str:
        """Return a string representation of the error."""
        if not self.missing_fields:
            return "Missing essential profile fields: No missing fields specified"
        
        field_list = ", ".join(self.missing_fields)
        return f"Missing essential profile fields: {field_list}"
