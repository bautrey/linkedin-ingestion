"""
URL Sanitization and Validation Service

This service provides comprehensive URL validation and sanitization for LinkedIn profiles
as part of the Quality Gates & Validation Pipeline system.

Features:
- URL sanitization (remove marketing parameters, normalize format)
- Support for modern vs legacy LinkedIn URL formats
- Fast validation that fails quickly for invalid URLs
"""

import re
from typing import Optional, Dict, Any, List, Tuple
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from pydantic import BaseModel
import logging
from datetime import datetime

from app.core.logging import get_logger

logger = get_logger(__name__)


class URLValidationResult(BaseModel):
    """Result of URL validation process"""
    is_valid: bool
    sanitized_url: Optional[str] = None
    validation_errors: List[str] = []
    warnings: List[str] = []
    url_format: Optional[str] = None  # "modern", "legacy", "company", "unknown"
    processing_time_ms: Optional[float] = None


class URLSanitizationConfig(BaseModel):
    """Configuration for URL sanitization"""
    remove_tracking_params: bool = True
    normalize_protocol: bool = True
    ensure_trailing_slash: bool = True
    
    # Common tracking parameters to remove
    tracking_params: List[str] = [
        'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
        'ref', 'referer', 'referrer', 'fbclid', 'gclid', 'msclkid',
        'mc_cid', 'mc_eid', '_ga', '_gl', 'source', 'campaign'
    ]


class LinkedInURLValidator:
    """
    LinkedIn URL validator with sanitization and format detection
    """
    
    # Modern LinkedIn URL patterns
    MODERN_PROFILE_PATTERNS = [
        r'^https?://(?:www\.)?linkedin\.com/in/([a-zA-Z0-9\-_]+)/?$',
        r'^https?://(?:www\.)?linkedin\.com/in/([a-zA-Z0-9\-_]+)/.*$'
    ]
    
    # Legacy LinkedIn URL patterns (should be rejected)
    LEGACY_PROFILE_PATTERNS = [
        r'^https?://(?:www\.)?linkedin\.com/pub/([^/]+)/([^/]+)/([^/]+)/([^/]+)/?.*$',
        r'^https?://(?:www\.)?linkedin\.com/profile/view\?id=([0-9]+).*$',
        r'^https?://(?:www\.)?linkedin\.com/people/([^/]+)/([^/]+)/?.*$'
    ]
    
    # Company URL patterns (for validation but different processing)
    COMPANY_PATTERNS = [
        r'^https?://(?:www\.)?linkedin\.com/company/([a-zA-Z0-9\-_]+)/?$',
        r'^https?://(?:www\.)?linkedin\.com/company/([0-9]+)/?$'
    ]
    
    def __init__(self, config: Optional[URLSanitizationConfig] = None):
        self.config = config or URLSanitizationConfig()
        self.logger = get_logger(__name__)
    
    def sanitize_url(self, url: str) -> Tuple[str, List[str]]:
        """
        Sanitize a LinkedIn URL by removing tracking parameters and normalizing format
        
        Returns:
            Tuple of (sanitized_url, warnings)
        """
        warnings = []
        original_url = url.strip()
        
        if not original_url:
            raise ValueError("URL cannot be empty")
        
        try:
            # Parse the URL
            parsed = urlparse(original_url)
            
            # Normalize protocol
            if self.config.normalize_protocol:
                if not parsed.scheme:
                    # Add https if no protocol specified
                    original_url = f"https://{original_url}"
                    parsed = urlparse(original_url)
                    warnings.append("Added https:// protocol to URL")
                elif parsed.scheme == 'http':
                    # Convert http to https for LinkedIn
                    parsed = parsed._replace(scheme='https')
                    warnings.append("Converted http:// to https:// for security")
            
            # Normalize hostname (ensure www subdomain for linkedin.com)
            if parsed.netloc:
                if parsed.netloc == 'linkedin.com':
                    parsed = parsed._replace(netloc='www.linkedin.com')
                    warnings.append("Added www subdomain to LinkedIn URL")
                elif parsed.netloc not in ['www.linkedin.com', 'm.linkedin.com']:
                    raise ValueError(f"Invalid LinkedIn domain: {parsed.netloc}")
            
            # Remove tracking parameters
            if self.config.remove_tracking_params and parsed.query:
                query_params = parse_qs(parsed.query, keep_blank_values=True)
                cleaned_params = {}
                
                removed_params = []
                for param, values in query_params.items():
                    if param.lower() not in [p.lower() for p in self.config.tracking_params]:
                        cleaned_params[param] = values
                    else:
                        removed_params.append(param)
                
                if removed_params:
                    warnings.append(f"Removed tracking parameters: {', '.join(removed_params)}")
                
                # Rebuild query string
                if cleaned_params:
                    new_query = urlencode(cleaned_params, doseq=True)
                    parsed = parsed._replace(query=new_query)
                else:
                    parsed = parsed._replace(query='')
            
            # Normalize path
            path = parsed.path
            if self.config.ensure_trailing_slash and path and not path.endswith('/'):
                # Only add trailing slash for profile URLs, not for URLs with file extensions
                if '/in/' in path and not '.' in path.split('/')[-1]:
                    path += '/'
                    parsed = parsed._replace(path=path)
                    warnings.append("Added trailing slash to profile URL")
            
            # Reconstruct URL
            sanitized_url = urlunparse(parsed)
            
            return sanitized_url, warnings
            
        except Exception as e:
            raise ValueError(f"Failed to parse URL: {str(e)}")
    
    def detect_url_format(self, url: str) -> str:
        """
        Detect the format of a LinkedIn URL
        
        Returns:
            "modern", "legacy", "company", or "unknown"
        """
        # Check modern profile patterns
        for pattern in self.MODERN_PROFILE_PATTERNS:
            if re.match(pattern, url, re.IGNORECASE):
                return "modern"
        
        # Check legacy profile patterns
        for pattern in self.LEGACY_PROFILE_PATTERNS:
            if re.match(pattern, url, re.IGNORECASE):
                return "legacy"
        
        # Check company patterns
        for pattern in self.COMPANY_PATTERNS:
            if re.match(pattern, url, re.IGNORECASE):
                return "company"
        
        return "unknown"
    
    def validate_linkedin_url(self, url: str) -> URLValidationResult:
        """
        Comprehensive LinkedIn URL validation with sanitization
        
        This is the main validation method for Stage 1 of quality gates.
        """
        start_time = datetime.now()
        validation_errors = []
        warnings = []
        sanitized_url = None
        
        try:
            # Step 1: Basic URL validation
            if not url or not isinstance(url, str):
                validation_errors.append("URL must be a non-empty string")
                return URLValidationResult(
                    is_valid=False,
                    validation_errors=validation_errors,
                    processing_time_ms=self._get_processing_time(start_time)
                )
            
            url = url.strip()
            if not url:
                validation_errors.append("URL cannot be empty or only whitespace")
                return URLValidationResult(
                    is_valid=False,
                    validation_errors=validation_errors,
                    processing_time_ms=self._get_processing_time(start_time)
                )
            
            # Step 2: Detect URL format
            url_format = self.detect_url_format(url)
            
            # Step 3: Handle different URL formats
            if url_format == "legacy":
                validation_errors.append(
                    "Legacy LinkedIn URL format is not supported. "
                    "Please use modern format: https://www.linkedin.com/in/username"
                )
                return URLValidationResult(
                    is_valid=False,
                    validation_errors=validation_errors,
                    url_format=url_format,
                    processing_time_ms=self._get_processing_time(start_time)
                )
            elif url_format == "unknown":
                validation_errors.append("URL does not match LinkedIn profile URL format")
                return URLValidationResult(
                    is_valid=False,
                    validation_errors=validation_errors,
                    url_format=url_format,
                    processing_time_ms=self._get_processing_time(start_time)
                )
            elif url_format == "company":
                validation_errors.append("This appears to be a company URL, not a profile URL")
                return URLValidationResult(
                    is_valid=False,
                    validation_errors=validation_errors,
                    url_format=url_format,
                    processing_time_ms=self._get_processing_time(start_time)
                )
            
            # Step 4: Sanitize the URL
            try:
                sanitized_url, sanitize_warnings = self.sanitize_url(url)
                warnings.extend(sanitize_warnings)
            except ValueError as e:
                validation_errors.append(f"URL sanitization failed: {str(e)}")
                return URLValidationResult(
                    is_valid=False,
                    validation_errors=validation_errors,
                    warnings=warnings,
                    url_format=url_format,
                    processing_time_ms=self._get_processing_time(start_time)
                )
            
            # Step 5: Final validation result
            is_valid = len(validation_errors) == 0
            
            return URLValidationResult(
                is_valid=is_valid,
                sanitized_url=sanitized_url if is_valid else None,
                validation_errors=validation_errors,
                warnings=warnings,
                url_format=url_format,
                processing_time_ms=self._get_processing_time(start_time)
            )
        
        except Exception as e:
            self.logger.error(f"Unexpected error during URL validation: {str(e)}")
            validation_errors.append(f"Validation failed due to unexpected error: {str(e)}")
            
            return URLValidationResult(
                is_valid=False,
                validation_errors=validation_errors,
                warnings=warnings,
                processing_time_ms=self._get_processing_time(start_time)
            )
    
    def _get_processing_time(self, start_time: datetime) -> float:
        """Calculate processing time in milliseconds"""
        end_time = datetime.now()
        return (end_time - start_time).total_seconds() * 1000


class URLValidationService:
    """
    Service wrapper for LinkedIn URL validation
    
    This provides a clean interface for the main application to use URL validation
    as part of the quality gates system.
    """
    
    def __init__(self, config: Optional[URLSanitizationConfig] = None):
        self.validator = LinkedInURLValidator(config)
        self.logger = get_logger(__name__)
    
    def validate_and_sanitize(self, url: str) -> URLValidationResult:
        """
        Main entry point for URL validation and sanitization
        
        This is the method that should be called from the ingestion pipeline
        as part of Stage 1 of the quality gates system.
        """
        self.logger.info(f"Starting URL validation for: {url}")
        
        result = self.validator.validate_linkedin_url(url)
        
        if result.is_valid:
            self.logger.info(
                f"URL validation successful: {url} -> {result.sanitized_url}",
                extra={
                    "original_url": url,
                    "sanitized_url": result.sanitized_url,
                    "url_format": result.url_format,
                    "processing_time_ms": result.processing_time_ms,
                    "warnings_count": len(result.warnings)
                }
            )
        else:
            self.logger.warning(
                f"URL validation failed: {url}",
                extra={
                    "original_url": url,
                    "validation_errors": result.validation_errors,
                    "url_format": result.url_format,
                    "processing_time_ms": result.processing_time_ms
                }
            )
        
        return result


# Convenience function for easy integration
def validate_linkedin_url(url: str) -> URLValidationResult:
    """
    Convenience function for validating a single LinkedIn URL
    
    This can be used directly in the ingestion pipeline without creating a service instance.
    """
    service = URLValidationService()
    return service.validate_and_sanitize(url)
