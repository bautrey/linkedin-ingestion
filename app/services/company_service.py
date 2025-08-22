"""
Company Service Layer

Handles business logic for company operations including:
- Company creation and updates with deduplication
- Smart company matching and similarity algorithms
- Profile-company relationship management
- Batch processing with error resilience
- URL normalization and validation
"""

import re
import logging
from typing import List, Optional, Dict, Any, Union
from urllib.parse import urlparse, parse_qs
from difflib import SequenceMatcher
import uuid

from app.models.canonical.company import CanonicalCompany
from app.repositories.company_repository import CompanyRepository


logger = logging.getLogger(__name__)


class CompanyService:
    """Service layer for company business logic operations."""
    
    def __init__(self, company_repository: CompanyRepository):
        """
        Initialize the company service.
        
        Args:
            company_repository: Repository for company database operations
        """
        self.company_repo = company_repository
        self.similarity_threshold = 0.85  # Threshold for considering companies similar

    async def create_or_update_company(self, company: CanonicalCompany) -> Dict[str, Any]:
        """
        Create a new company or update an existing one.
        
        Args:
            company: CanonicalCompany model instance
            
        Returns:
            Dict containing the created/updated company record
            
        Raises:
            ValueError: If company data is invalid
            Exception: If database operation fails
        """
        try:
            # Validate company data
            if not company.company_name or not company.company_name.strip():
                raise ValueError("Company name cannot be empty")
            
            # Check if company already exists
            existing_company = None
            if company.company_id:
                existing_company = await self.company_repo.get_by_linkedin_id(company.company_id)
            
            if existing_company:
                # Merge new data with existing data
                merged_company = self._merge_company_data(existing_company, company)
                
                # Update existing company using database ID
                result = await self.company_repo.update(existing_company.id, merged_company)
                logger.info(f"Updated company: {company.company_name} (LinkedIn ID: {company.company_id})")
                return result
            else:
                # Create new company
                result = await self.company_repo.create(company)
                logger.info(f"Created new company: {company.company_name}")
                return result
                
        except ValueError as e:
            logger.error(f"Validation error for company {company.company_name}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Failed to create/update company {company.company_name}: {str(e)}")
            raise

    async def find_company_by_url(self, linkedin_url: str) -> Optional[CanonicalCompany]:
        """
        Find a company by its LinkedIn URL.
        
        Args:
            linkedin_url: LinkedIn company page URL
            
        Returns:
            CanonicalCompany instance or None if not found
        """
        try:
            # Extract company ID from URL
            company_id = self._extract_company_id_from_url(linkedin_url)
            if not company_id:
                logger.warning(f"Could not extract company ID from URL: {linkedin_url}")
                return None
            
            # Search by LinkedIn company ID
            company = await self.company_repo.get_by_linkedin_id(company_id)
            return company
            
        except Exception as e:
            logger.error(f"Failed to find company by URL {linkedin_url}: {str(e)}")
            return None

    async def deduplicate_company(self, company: CanonicalCompany) -> Optional[CanonicalCompany]:
        """
        Find existing company that matches the given company data.
        
        Uses LinkedIn URL first, then name similarity matching.
        
        Args:
            company: Company data to check for duplicates
            
        Returns:
            Existing CanonicalCompany if found, None otherwise
        """
        try:
            # First try LinkedIn ID matching (most reliable)
            if company.company_id:
                existing = await self.company_repo.get_by_linkedin_id(company.company_id)
                if existing:
                    logger.info(f"Found existing company by LinkedIn ID: {company.company_name}")
                    return existing
            
            # Try name similarity matching
            similar_companies = await self.company_repo.search_by_name(company.company_name)
            if similar_companies:
                # Find the most similar company
                best_match = None
                best_similarity = 0.0
                
                for existing_company in similar_companies:
                    similarity = self._calculate_name_similarity(
                        company.company_name, 
                        existing_company.company_name
                    )
                    
                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_match = existing_company
                
                if best_match and best_similarity >= self.similarity_threshold:
                    logger.info(f"Found similar company: {best_match.company_name} "
                              f"(similarity: {best_similarity:.2f})")
                    return best_match
            
            logger.debug(f"No existing company found for: {company.company_name}")
            return None
            
        except Exception as e:
            logger.error(f"Error during company deduplication for {company.company_name}: {str(e)}")
            return None

    async def batch_process_companies(self, companies: List[CanonicalCompany]) -> List[Dict[str, Any]]:
        """
        Process multiple companies efficiently with error resilience.
        
        Args:
            companies: List of CanonicalCompany instances to process
            
        Returns:
            List of results with success status and data/error information
        """
        results = []
        
        logger.info(f"DEBUG: Starting batch processing of {len(companies)} companies")
        
        for i, company in enumerate(companies):
            try:
                logger.info(f"DEBUG: Processing company {i+1}/{len(companies)}: {company.company_name} (LinkedIn ID: {getattr(company, 'company_id', 'None')})")
                
                # Check for duplicates
                logger.info(f"DEBUG: Checking for duplicates for company: {company.company_name}")
                existing = await self.deduplicate_company(company)
                
                if existing:
                    logger.info(f"DEBUG: Found existing company, will update: {existing.company_name} (DB ID: {existing.id})")
                    # Update existing company with new data
                    merged = self._merge_company_data(existing, company)
                    logger.info(f"DEBUG: Calling repository update for company: {company.company_name}")
                    result = await self.company_repo.update(existing.id, merged)
                    logger.info(f"DEBUG: Successfully updated company in database: {company.company_name} (DB ID: {result['id']})")
                    
                    results.append({
                        "success": True,
                        "action": "updated",
                        "company_id": result["id"],
                        "company_name": company.company_name,
                        "data": result
                    })
                else:
                    logger.info(f"DEBUG: No existing company found, will create new: {company.company_name}")
                    # Create new company
                    logger.info(f"DEBUG: Calling repository create for company: {company.company_name}")
                    result = await self.company_repo.create(company)
                    logger.info(f"DEBUG: Successfully created company in database: {company.company_name} (DB ID: {result['id']})")
                    
                    results.append({
                        "success": True,
                        "action": "created", 
                        "company_id": result["id"],
                        "company_name": company.company_name,
                        "data": result
                    })
                    
            except Exception as e:
                logger.error(f"Failed to process company {i+1}/{len(companies)} "
                          f"({company.company_name}): {str(e)}")
                
                results.append({
                    "success": False,
                    "action": "error",
                    "company_name": company.company_name,
                    "error": str(e)
                })
        
        successful = len([r for r in results if r["success"]])
        logger.info(f"Batch processing complete: {successful}/{len(companies)} successful")
        
        return results

    def link_profile_to_company(self, profile_id: str, company_id: str, work_experience: Dict[str, Any]) -> Dict[str, Any]:
        """
        Link a profile to a company with work experience details.
        
        Args:
            profile_id: UUID of the profile
            company_id: UUID of the company
            work_experience: Dict containing work experience details
            
        Returns:
            Dict containing the relationship record
        """
        try:
            # Validate work experience data
            required_fields = ["position_title"]
            for field in required_fields:
                if field not in work_experience:
                    raise ValueError(f"Missing required field: {field}")
            
            # Create the relationship
            result = self.company_repo.link_to_profile(profile_id, company_id, work_experience)
            
            logger.info(f"Linked profile {profile_id} to company {company_id} "
                       f"as {work_experience.get('position_title', 'Unknown')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to link profile {profile_id} to company {company_id}: {str(e)}")
            raise

    def unlink_profile_from_company(self, profile_id: str, company_id: str) -> None:
        """
        Unlink a profile from a company.
        
        Args:
            profile_id: UUID of the profile
            company_id: UUID of the company
        """
        try:
            self.company_repo.unlink_from_profile(profile_id, company_id)
            logger.info(f"Unlinked profile {profile_id} from company {company_id}")
            
        except Exception as e:
            logger.error(f"Failed to unlink profile {profile_id} from company {company_id}: {str(e)}")
            raise

    def get_companies_for_profile(self, profile_id: str) -> List[CanonicalCompany]:
        """
        Get all companies associated with a profile.
        
        Args:
            profile_id: UUID of the profile
            
        Returns:
            List of CanonicalCompany instances
        """
        try:
            companies = self.company_repo.get_companies_for_profile(profile_id)
            logger.debug(f"Found {len(companies)} companies for profile {profile_id}")
            return companies
            
        except Exception as e:
            logger.error(f"Failed to get companies for profile {profile_id}: {str(e)}")
            return []

    # Private helper methods

    def _extract_company_id_from_url(self, linkedin_url: str) -> Optional[str]:
        """
        Extract company ID from LinkedIn URL.
        
        Args:
            linkedin_url: LinkedIn company page URL
            
        Returns:
            Company ID string or None if extraction fails
        """
        try:
            # Normalize URL - ensure it has a protocol
            if not linkedin_url.startswith(('http://', 'https://')):
                linkedin_url = 'https://' + linkedin_url
            
            # Parse the URL
            parsed = urlparse(linkedin_url)
            
            # Extract path and remove leading/trailing slashes
            path = parsed.path.strip('/')
            
            # Match LinkedIn company URL pattern
            # Examples: /company/test-corp, /company/123456
            pattern = r'^company/([^/?]+)'
            match = re.match(pattern, path)
            
            if match:
                company_id = match.group(1)
                return company_id
            
            logger.warning(f"Could not extract company ID from URL path: {path}")
            return None
            
        except Exception as e:
            logger.error(f"Error parsing LinkedIn URL {linkedin_url}: {str(e)}")
            return None

    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """
        Calculate similarity between two company names.
        
        Uses sequence matching with normalization for common variations.
        
        Args:
            name1: First company name
            name2: Second company name
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        if not name1 or not name2:
            return 0.0
        
        # Normalize names for comparison
        normalized1 = self._normalize_company_name(name1)
        normalized2 = self._normalize_company_name(name2)
        
        if normalized1 == normalized2:
            return 1.0
        
        # Calculate sequence similarity
        return SequenceMatcher(None, normalized1, normalized2).ratio()

    def _normalize_company_name(self, name: str) -> str:
        """
        Normalize company name for similarity comparison.
        
        Args:
            name: Company name to normalize
            
        Returns:
            Normalized company name
        """
        if not name:
            return ""
        
        # Convert to lowercase and remove extra whitespace
        normalized = name.lower().strip()
        
        # Remove common company suffixes and words
        suffixes_to_remove = [
            'inc', 'inc.', 'incorporated', 
            'corp', 'corp.', 'corporation',
            'ltd', 'ltd.', 'limited',
            'llc', 'l.l.c.',
            'co', 'co.', 'company',
            'the '  # Remove leading "the"
        ]
        
        for suffix in suffixes_to_remove:
            if normalized.endswith(' ' + suffix):
                normalized = normalized[:-len(' ' + suffix)]
            elif normalized.startswith(suffix + ' '):
                normalized = normalized[len(suffix + ' '):]
        
        # Replace multiple spaces with single space
        normalized = re.sub(r'\s+', ' ', normalized)
        
        return normalized.strip()

    def _merge_company_data(self, existing: CanonicalCompany, updated: CanonicalCompany) -> CanonicalCompany:
        """
        Merge updated company data with existing data.
        
        Preserves existing data while updating with new non-null fields.
        
        Args:
            existing: Current company data
            updated: New company data to merge
            
        Returns:
            Merged CanonicalCompany instance
        """
        # Create a dict with existing data
        merged_data = existing.model_dump()
        updated_data = updated.model_dump()
        
        # Update fields that have new values
        for field, new_value in updated_data.items():
            if new_value is not None:
                # For lists, extend rather than replace if both have values
                if field == "industries" and isinstance(new_value, list) and merged_data.get(field):
                    # Merge and deduplicate industries
                    existing_industries = merged_data[field] or []
                    merged_industries = list(dict.fromkeys(existing_industries + new_value))
                    merged_data[field] = merged_industries
                elif field == "locations" and isinstance(new_value, list) and merged_data.get(field):
                    # Merge locations, preferring new ones for conflicts
                    existing_locations = merged_data[field] or []
                    merged_data[field] = existing_locations + new_value
                else:
                    # For most fields, new value takes precedence
                    merged_data[field] = new_value
        
        # Create new instance with merged data
        return CanonicalCompany(**merged_data)
