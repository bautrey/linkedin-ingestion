"""
Cassidy-to-Canonical Adapter

This module provides the CassidyAdapter class that transforms Cassidy API responses
into our internal canonical data models. This decoupling layer allows us to easily
switch data providers without modifying the core application logic.
"""

import json
import os
from typing import Dict, Any, List, Optional
from pathlib import Path

from .exceptions import IncompleteDataError
from app.models.canonical import (
    CanonicalProfile,
    CanonicalExperienceEntry, 
    CanonicalEducationEntry,
    CanonicalCompany,
    CanonicalFundingInfo,
    CanonicalCompanyLocation,
    CanonicalAffiliatedCompany
)


class CassidyAdapter:
    """
    Adapter that transforms Cassidy API responses into canonical models.
    
    This class provides a clean interface for converting external API data
    into our internal data structures, with validation to ensure data quality.
    """
    
    def __init__(self):
        """Initialize the adapter with field mappings configuration."""
        self._load_field_mappings()
        
    def _load_field_mappings(self) -> None:
        """Load field mappings from the configuration file."""
        config_path = Path(__file__).parent / "cassidy_field_mappings.json"
        
        try:
            with open(config_path, 'r') as f:
                self._mappings = json.load(f)
        except FileNotFoundError:
            raise RuntimeError(f"Field mappings configuration not found at {config_path}")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Invalid JSON in field mappings configuration: {e}")
    
    def transform(self, cassidy_data: Dict[str, Any]) -> CanonicalProfile:
        """
        Transform a Cassidy API response into a CanonicalProfile.
        
        Args:
            cassidy_data: Dictionary containing Cassidy API response data
            
        Returns:
            CanonicalProfile instance with transformed data
            
        Raises:
            IncompleteDataError: If essential fields are missing
        """
        # Validate essential fields first
        self._validate_essential_fields(cassidy_data)
        
        # Transform basic profile fields
        profile_data = self._transform_basic_profile_fields(cassidy_data)
        
        # Transform nested data structures
        profile_data['experiences'] = self._transform_experiences(
            cassidy_data.get('experiences', [])
        )
        profile_data['educations'] = self._transform_educations(
            cassidy_data.get('educations', [])
        )
        
        # Store raw data for debugging and future reference
        profile_data['raw_data'] = cassidy_data
        
        return CanonicalProfile(**profile_data)
    
    def _validate_essential_fields(self, cassidy_data: Dict[str, Any]) -> None:
        """
        Validate that essential fields are present and not empty.
        
        Args:
            cassidy_data: Dictionary to validate
            
        Raises:
            IncompleteDataError: If essential fields are missing
        """
        essential_fields = self._mappings['essential_fields']['profile']
        missing_fields = []
        
        for field in essential_fields:
            value = cassidy_data.get(field)
            if value is None or (isinstance(value, str) and not value.strip()):
                missing_fields.append(field)
        
        if missing_fields:
            raise IncompleteDataError(missing_fields)
    
    def _transform_basic_profile_fields(self, cassidy_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform basic profile fields from Cassidy format to canonical format.
        
        Args:
            cassidy_data: Source data from Cassidy API
            
        Returns:
            Dictionary with transformed basic profile fields
        """
        profile_mapping = self._mappings['profile_mapping']
        transformed = {}
        
        # Transform each category of fields
        for category, field_mappings in profile_mapping.items():
            for canonical_field, cassidy_field in field_mappings.items():
                value = cassidy_data.get(cassidy_field)
                if value is not None:
                    transformed[canonical_field] = value
        
        return transformed
    
    def _transform_experiences(self, experiences_data: List[Dict[str, Any]]) -> List[CanonicalExperienceEntry]:
        """
        Transform experience entries from Cassidy format to canonical format.
        
        Args:
            experiences_data: List of experience dictionaries from Cassidy
            
        Returns:
            List of CanonicalExperienceEntry instances
        """
        transformed_experiences = []
        
        for experience in experiences_data:
            transformed_experience = self._transform_experience(experience)
            transformed_experiences.append(transformed_experience)
        
        return transformed_experiences
    
    def _transform_experience(self, experience_data: Dict[str, Any]) -> CanonicalExperienceEntry:
        """
        Transform a single experience entry from Cassidy to canonical format.
        
        Args:
            experience_data: Single experience dictionary from Cassidy
            
        Returns:
            CanonicalExperienceEntry instance
        """
        experience_mapping = self._mappings['experience_mapping']
        transformed = {}
        
        for canonical_field, cassidy_field in experience_mapping.items():
            value = experience_data.get(cassidy_field)
            if value is not None:
                # Apply data type conversions for specific fields
                transformed[canonical_field] = self._convert_experience_field(canonical_field, value)
        
        return CanonicalExperienceEntry(**transformed)
    
    def _convert_experience_field(self, field_name: str, value: Any) -> Any:
        """
        Convert field values to appropriate types for CanonicalExperienceEntry.
        
        Args:
            field_name: Name of the canonical field
            value: Raw value from Cassidy data
            
        Returns:
            Converted value appropriate for the field type
        """
        # Handle year fields that might be strings like "Present"
        if field_name in ['start_year', 'end_year'] and isinstance(value, str):
            if value.lower() in ['present', 'current', 'now']:
                return None  # Set to None for current positions
            try:
                return int(value)
            except ValueError:
                return None  # If conversion fails, set to None
        
        # Handle month fields that might be strings
        if field_name in ['start_month', 'end_month'] and isinstance(value, str):
            try:
                return int(value)
            except ValueError:
                return None
        
        return value
    
    def _transform_educations(self, educations_data: List[Dict[str, Any]]) -> List[CanonicalEducationEntry]:
        """
        Transform education entries from Cassidy format to canonical format.
        
        Args:
            educations_data: List of education dictionaries from Cassidy
            
        Returns:
            List of CanonicalEducationEntry instances
        """
        transformed_educations = []
        
        for education in educations_data:
            transformed_education = self._transform_education(education)
            transformed_educations.append(transformed_education)
        
        return transformed_educations
    
    def _transform_education(self, education_data: Dict[str, Any]) -> CanonicalEducationEntry:
        """
        Transform a single education entry from Cassidy to canonical format.
        
        Args:
            education_data: Single education dictionary from Cassidy
            
        Returns:
            CanonicalEducationEntry instance
        """
        education_mapping = self._mappings['education_mapping']
        transformed = {}
        
        for canonical_field, cassidy_field in education_mapping.items():
            value = education_data.get(cassidy_field)
            if value is not None:
                # Apply data type conversions for specific fields
                transformed[canonical_field] = self._convert_education_field(canonical_field, value)
        
        return CanonicalEducationEntry(**transformed)
    
    def _convert_education_field(self, field_name: str, value: Any) -> Any:
        """
        Convert field values to appropriate types for CanonicalEducationEntry.
        
        Args:
            field_name: Name of the canonical field
            value: Raw value from Cassidy data
            
        Returns:
            Converted value appropriate for the field type
        """
        # Handle year fields that might be strings
        if field_name in ['start_year', 'end_year'] and isinstance(value, str):
            try:
                return int(value)
            except ValueError:
                return None  # If conversion fails, set to None
        
        return value
    
    def _transform_company(self, company_data: Dict[str, Any]) -> CanonicalCompany:
        """
        Transform a company profile from Cassidy to canonical format.
        
        Args:
            company_data: Company dictionary from Cassidy
            
        Returns:
            CanonicalCompany instance
            
        Raises:
            IncompleteDataError: If essential company fields are missing
        """
        # Validate essential company fields
        essential_fields = self._mappings['essential_fields']['company']
        missing_fields = []
        
        for field in essential_fields:
            value = company_data.get(field)
            if value is None or (isinstance(value, str) and not value.strip()):
                missing_fields.append(field)
        
        if missing_fields:
            raise IncompleteDataError(missing_fields)
        
        # Transform company fields
        company_mapping = self._mappings['company_mapping']
        transformed = {}
        
        for category, field_mappings in company_mapping.items():
            for canonical_field, cassidy_field in field_mappings.items():
                value = company_data.get(cassidy_field)
                if value is not None:
                    transformed[canonical_field] = value
        
        # Transform nested company data
        if 'funding_info' in company_data and company_data['funding_info']:
            transformed['funding_info'] = CanonicalFundingInfo(**company_data['funding_info'])
        
        if 'locations' in company_data and company_data['locations']:
            transformed['locations'] = [
                CanonicalCompanyLocation(**loc) for loc in company_data['locations']
            ]
        
        if 'affiliated_companies' in company_data and company_data['affiliated_companies']:
            transformed['affiliated_companies'] = [
                CanonicalAffiliatedCompany(**company) for company in company_data['affiliated_companies']
            ]
        
        # Store raw data
        transformed['raw_data'] = company_data
        
        return CanonicalCompany(**transformed)
