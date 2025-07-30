"""
Cassidy-to-Canonical Adapter

This module provides the CassidyAdapter class that transforms Cassidy API responses
into our internal canonical data models. This decoupling layer allows us to easily
switch data providers without modifying the core application logic.
"""

import json
import logging
import os
import time
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

# Configure logger for this module
logger = logging.getLogger(__name__)


class CassidyAdapter:
    """
    Adapter that transforms Cassidy API responses into canonical models.
    
    This class provides a clean interface for converting external API data
    into our internal data structures, with validation to ensure data quality.
    """
    
    def __init__(self):
        """Initialize the adapter with field mappings configuration."""
        logger.info("Initializing CassidyAdapter")
        self._load_field_mappings()
        logger.info("CassidyAdapter initialized successfully")
        
    def _load_field_mappings(self) -> None:
        """Load field mappings from the configuration file."""
        config_path = Path(__file__).parent / "cassidy_field_mappings.json"
        logger.debug(f"Loading field mappings from: {config_path}")
        
        try:
            with open(config_path, 'r') as f:
                self._mappings = json.load(f)
            logger.info(f"Successfully loaded field mappings configuration with {len(self._mappings)} sections")
        except FileNotFoundError:
            logger.error(f"Field mappings configuration not found at {config_path}")
            raise RuntimeError(f"Field mappings configuration not found at {config_path}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in field mappings configuration: {e}")
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
        start_time = time.time()
        linkedin_url = cassidy_data.get('linkedin_url', 'unknown')
        
        logger.info(
            "Starting profile transformation",
            extra={
                "linkedin_url": linkedin_url,
                "data_size_bytes": len(str(cassidy_data)),
                "top_level_keys": list(cassidy_data.keys()) if isinstance(cassidy_data, dict) else []
            }
        )
        
        try:
            # Validate essential fields first
            self._validate_essential_fields(cassidy_data)
            
            # Transform basic profile fields
            profile_data = self._transform_basic_profile_fields(cassidy_data)
            
            # Transform nested data structures
            experiences_raw = cassidy_data.get('experiences', [])
            educations_raw = cassidy_data.get('educations', [])
            
            logger.debug(
                "Transforming nested data structures",
                extra={
                    "linkedin_url": linkedin_url,
                    "experiences_count": len(experiences_raw) if isinstance(experiences_raw, list) else 0,
                    "educations_count": len(educations_raw) if isinstance(educations_raw, list) else 0
                }
            )
            
            profile_data['experiences'] = self._transform_experiences(experiences_raw)
            profile_data['educations'] = self._transform_educations(educations_raw)
            
            # Store raw data for debugging and future reference
            profile_data['raw_data'] = cassidy_data
            
            # Create the canonical profile
            canonical_profile = CanonicalProfile(**profile_data)
            
            # Log successful transformation with metrics
            transformation_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            logger.info(
                "Successfully transformed profile data",
                extra={
                    "linkedin_url": linkedin_url,
                    "transformation_time_ms": round(transformation_time, 2),
                    "experiences_transformed": len(canonical_profile.experiences) if canonical_profile.experiences else 0,
                    "educations_transformed": len(canonical_profile.educations) if canonical_profile.educations else 0,
                    "profile_name": getattr(canonical_profile, 'name', None)
                }
            )
            
            return canonical_profile
            
        except IncompleteDataError as e:
            transformation_time = (time.time() - start_time) * 1000
            logger.warning(
                "Profile transformation failed due to incomplete data",
                extra={
                    "linkedin_url": linkedin_url,
                    "transformation_time_ms": round(transformation_time, 2),
                    "missing_fields": e.missing_fields,
                    "error_type": "IncompleteDataError"
                }
            )
            raise
        except Exception as e:
            transformation_time = (time.time() - start_time) * 1000
            logger.error(
                "Profile transformation failed with unexpected error",
                extra={
                    "linkedin_url": linkedin_url,
                    "transformation_time_ms": round(transformation_time, 2),
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                }
            )
            raise
    
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
        
        logger.debug(
            "Validating essential profile fields",
            extra={
                "essential_fields_count": len(essential_fields),
                "essential_fields": essential_fields
            }
        )
        
        for field in essential_fields:
            value = cassidy_data.get(field)
            if value is None or (isinstance(value, str) and not value.strip()):
                missing_fields.append(field)
        
        if missing_fields:
            logger.warning(
                "Essential field validation failed",
                extra={
                    "missing_fields": missing_fields,
                    "total_missing": len(missing_fields),
                    "available_fields": list(cassidy_data.keys()) if isinstance(cassidy_data, dict) else []
                }
            )
            raise IncompleteDataError(missing_fields)
        else:
            logger.debug("All essential fields validated successfully")
    
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
        # Handle edge case where experiences_data is not a list
        if not isinstance(experiences_data, list):
            logger.warning(
                "Experiences data is not a list",
                extra={
                    "actual_type": type(experiences_data).__name__,
                    "value": str(experiences_data)[:100] if experiences_data else None
                }
            )
            return []
            
        logger.debug(
            "Starting experience transformation",
            extra={"total_experiences": len(experiences_data)}
        )
        
        transformed_experiences = []
        skipped_count = 0
        
        for i, experience in enumerate(experiences_data):
            # Skip None entries in the array
            if experience is None:
                logger.debug(f"Skipping None experience at index {i}")
                skipped_count += 1
                continue
                
            # Ensure experience is a dictionary
            if not isinstance(experience, dict):
                logger.debug(
                    f"Skipping non-dict experience at index {i}",
                    extra={"actual_type": type(experience).__name__}
                )
                skipped_count += 1
                continue
                
            try:
                transformed_experience = self._transform_experience(experience)
                transformed_experiences.append(transformed_experience)
                logger.debug(
                    f"Successfully transformed experience {i}",
                    extra={
                        "company": experience.get('company_name'),
                        "position": experience.get('position_title')
                    }
                )
            except Exception as e:
                logger.warning(
                    f"Failed to transform experience at index {i}",
                    extra={
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                        "experience_keys": list(experience.keys()) if isinstance(experience, dict) else []
                    }
                )
                skipped_count += 1
                continue
        
        logger.info(
            "Completed experience transformation",
            extra={
                "total_input": len(experiences_data),
                "successfully_transformed": len(transformed_experiences),
                "skipped_count": skipped_count
            }
        )
        
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
        original_value = value
        
        # Handle year fields that might be strings like "Present"
        if field_name in ['start_year', 'end_year'] and isinstance(value, str):
            if value.lower() in ['present', 'current', 'now']:
                logger.debug(
                    f"Converting {field_name} 'present' value to None",
                    extra={"original_value": original_value}
                )
                return None  # Set to None for current positions
            try:
                converted_value = int(value)
                logger.debug(
                    f"Successfully converted {field_name} to integer",
                    extra={"original_value": original_value, "converted_value": converted_value}
                )
                return converted_value
            except ValueError:
                logger.warning(
                    f"Failed to convert {field_name} to integer",
                    extra={"original_value": original_value, "field_name": field_name}
                )
                return None  # If conversion fails, set to None
        
        # Handle month fields that might be strings
        if field_name in ['start_month', 'end_month'] and isinstance(value, str):
            try:
                converted_value = int(value)
                logger.debug(
                    f"Successfully converted {field_name} to integer",
                    extra={"original_value": original_value, "converted_value": converted_value}
                )
                return converted_value
            except ValueError:
                logger.warning(
                    f"Failed to convert {field_name} to integer",
                    extra={"original_value": original_value, "field_name": field_name}
                )
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
        # Handle edge case where educations_data is not a list or is None
        if not isinstance(educations_data, list):
            logger.warning(
                "Education data is not a list",
                extra={
                    "actual_type": type(educations_data).__name__,
                    "value": str(educations_data)[:100] if educations_data else None
                }
            )
            return []
            
        logger.debug(
            "Starting education transformation",
            extra={"total_educations": len(educations_data)}
        )
        
        transformed_educations = []
        skipped_count = 0
        
        for i, education in enumerate(educations_data):
            # Skip None entries in the array
            if education is None:
                logger.debug(f"Skipping None education at index {i}")
                skipped_count += 1
                continue
                
            # Ensure education is a dictionary
            if not isinstance(education, dict):
                logger.debug(
                    f"Skipping non-dict education at index {i}",
                    extra={"actual_type": type(education).__name__}
                )
                skipped_count += 1
                continue
                
            try:
                transformed_education = self._transform_education(education)
                transformed_educations.append(transformed_education)
                logger.debug(
                    f"Successfully transformed education {i}",
                    extra={
                        "institution": education.get('institution_name'),
                        "degree": education.get('degree')
                    }
                )
            except Exception as e:
                logger.warning(
                    f"Failed to transform education at index {i}",
                    extra={
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                        "education_keys": list(education.keys()) if isinstance(education, dict) else []
                    }
                )
                skipped_count += 1
                continue
        
        logger.info(
            "Completed education transformation",
            extra={
                "total_input": len(educations_data),
                "successfully_transformed": len(transformed_educations),
                "skipped_count": skipped_count
            }
        )
        
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
    
    def _clean_funding_data(self, funding_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean and validate funding data to ensure it can be used with CanonicalFundingInfo.
        
        Args:
            funding_data: Raw funding data dictionary
            
        Returns:
            Cleaned funding data dictionary with valid types
        """
        logger.debug(
            "Starting funding data cleaning",
            extra={
                "input_fields": list(funding_data.keys()) if isinstance(funding_data, dict) else [],
                "input_size": len(funding_data) if isinstance(funding_data, dict) else 0
            }
        )
        
        cleaned = {}
        cleaned_count = 0
        skipped_count = 0
        
        # Copy all string fields as-is
        string_fields = ['crunchbase_url', 'last_funding_round_type', 'last_funding_round_amount', 'last_funding_round_currency']
        for field in string_fields:
            value = funding_data.get(field)
            if value is not None:
                cleaned[field] = value
                cleaned_count += 1
            else:
                skipped_count += 1
        
        # Handle integer fields with validation
        int_fields = ['last_funding_round_year', 'last_funding_round_month', 'last_funding_round_investor_count']
        for field in int_fields:
            value = funding_data.get(field)
            if value is not None:
                if isinstance(value, int):
                    cleaned[field] = value
                    cleaned_count += 1
                elif isinstance(value, str) and value.strip():
                    try:
                        cleaned_value = int(value)
                        cleaned[field] = cleaned_value
                        cleaned_count += 1
                        logger.debug(
                            f"Successfully converted funding field {field} to integer",
                            extra={"original_value": value, "converted_value": cleaned_value}
                        )
                    except ValueError:
                        logger.warning(
                            f"Failed to convert funding field {field} to integer",
                            extra={"field": field, "value": value}
                        )
                        skipped_count += 1
                else:
                    skipped_count += 1
            else:
                skipped_count += 1
        
        logger.debug(
            "Completed funding data cleaning",
            extra={
                "cleaned_fields": cleaned_count,
                "skipped_fields": skipped_count,
                "output_fields": list(cleaned.keys())
            }
        )
        
        return cleaned
    
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
        start_time = time.time()
        company_name = company_data.get('company_name', 'unknown')
        
        logger.info(
            "Starting company transformation",
            extra={
                "company_name": company_name,
                "data_size_bytes": len(str(company_data)),
                "top_level_keys": list(company_data.keys()) if isinstance(company_data, dict) else []
            }
        )
        
        # Validate essential company fields
        essential_fields = self._mappings['essential_fields']['company']
        missing_fields = []
        
        logger.debug(
            "Validating essential company fields",
            extra={
                "company_name": company_name,
                "essential_fields_count": len(essential_fields),
                "essential_fields": essential_fields
            }
        )
        
        for field in essential_fields:
            value = company_data.get(field)
            if value is None or (isinstance(value, str) and not value.strip()):
                missing_fields.append(field)
        
        if missing_fields:
            transformation_time = (time.time() - start_time) * 1000
            logger.warning(
                "Company transformation failed due to missing essential fields",
                extra={
                    "company_name": company_name,
                    "transformation_time_ms": round(transformation_time, 2),
                    "missing_fields": missing_fields,
                    "available_fields": list(company_data.keys()) if isinstance(company_data, dict) else []
                }
            )
            raise IncompleteDataError(missing_fields)
        
        # Transform company fields
        company_mapping = self._mappings['company_mapping']
        transformed = {}
        
        for category, field_mappings in company_mapping.items():
            for canonical_field, cassidy_field in field_mappings.items():
                value = company_data.get(cassidy_field)
                if value is not None:
                    transformed[canonical_field] = value
        
        # Transform nested company data with robust handling
        nested_data_stats = {"funding_processed": False, "locations_count": 0, "affiliated_count": 0}
        
        # Handle funding_info - skip if empty dict or has invalid data
        if 'funding_info' in company_data:
            funding_data = company_data['funding_info']
            if isinstance(funding_data, dict) and funding_data:  # Not empty dict
                try:
                    # Clean and validate funding data before creating object
                    cleaned_funding = self._clean_funding_data(funding_data)
                    # Only create FundingInfo if there's actual data after cleaning
                    if cleaned_funding and any(v is not None for v in cleaned_funding.values()):
                        transformed['funding_info'] = CanonicalFundingInfo(**cleaned_funding)
                        nested_data_stats["funding_processed"] = True
                        logger.debug(
                            "Successfully processed company funding info",
                            extra={"company_name": company_name, "funding_fields": list(cleaned_funding.keys())}
                        )
                except Exception as e:
                    logger.warning(
                        "Failed to process company funding info",
                        extra={
                            "company_name": company_name,
                            "error_type": type(e).__name__,
                            "error_message": str(e)
                        }
                    )
        
        # Handle locations - filter out None entries
        if 'locations' in company_data and company_data['locations']:
            locations_data = company_data['locations']
            if isinstance(locations_data, list):
                valid_locations = []
                for i, loc in enumerate(locations_data):
                    if loc is not None and isinstance(loc, dict):
                        try:
                            valid_locations.append(CanonicalCompanyLocation(**loc))
                        except Exception as e:
                            logger.warning(
                                f"Failed to process company location at index {i}",
                                extra={
                                    "company_name": company_name,
                                    "error_type": type(e).__name__,
                                    "location_keys": list(loc.keys()) if isinstance(loc, dict) else []
                                }
                            )
                            continue
                transformed['locations'] = valid_locations
                nested_data_stats["locations_count"] = len(valid_locations)
        
        # Handle affiliated_companies - filter out None entries
        if 'affiliated_companies' in company_data and company_data['affiliated_companies']:
            affiliated_data = company_data['affiliated_companies']
            if isinstance(affiliated_data, list):
                valid_companies = []
                for i, company in enumerate(affiliated_data):
                    if company is not None and isinstance(company, dict):
                        try:
                            valid_companies.append(CanonicalAffiliatedCompany(**company))
                        except Exception as e:
                            logger.warning(
                                f"Failed to process affiliated company at index {i}",
                                extra={
                                    "company_name": company_name,
                                    "error_type": type(e).__name__,
                                    "affiliated_company_keys": list(company.keys()) if isinstance(company, dict) else []
                                }
                            )
                            continue
                transformed['affiliated_companies'] = valid_companies
                nested_data_stats["affiliated_count"] = len(valid_companies)
        
        # Store raw data
        transformed['raw_data'] = company_data
        
        # Create the canonical company
        canonical_company = CanonicalCompany(**transformed)
        
        # Log successful transformation with metrics
        transformation_time = (time.time() - start_time) * 1000
        logger.info(
            "Successfully transformed company data",
            extra={
                "company_name": company_name,
                "transformation_time_ms": round(transformation_time, 2),
                "funding_processed": nested_data_stats["funding_processed"],
                "locations_count": nested_data_stats["locations_count"],
                "affiliated_companies_count": nested_data_stats["affiliated_count"]
            }
        )
        
        return canonical_company
