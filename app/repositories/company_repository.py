"""
Company repository for database operations with CanonicalCompany model.

Handles all database CRUD operations for companies including:
- Insert/update company records
- Query companies with filters and search
- Vector similarity search
- Size and startup filtering
- Domain and location-based queries
"""

from typing import List, Optional, Dict, Any, Union
import uuid
from datetime import datetime, timezone
import json
import logging

from supabase import Client as SupabaseClient
from pydantic import ValidationError

from app.models.canonical.company import CanonicalCompany, CanonicalFundingInfo, CanonicalCompanyLocation, CanonicalAffiliatedCompany


logger = logging.getLogger(__name__)


class CompanyRepository:
    """Repository class for company database operations."""
    
    def __init__(self, supabase_client: SupabaseClient):
        """
        Initialize the company repository.
        
        Args:
            supabase_client: Supabase client instance for database operations
        """
        self.client = supabase_client
        self.table_name = "companies"
    
    def create(self, company: CanonicalCompany) -> Dict[str, Any]:
        """
        Insert a new company record into the database.
        
        Args:
            company: CanonicalCompany model instance
            
        Returns:
            Dict containing the created company record
            
        Raises:
            Exception: If database operation fails
        """
        try:
            # Convert the CanonicalCompany model to database format
            db_data = self._model_to_db_format(company)
            
            # Insert into database
            result = self.client.table(self.table_name).insert(db_data).execute()
            
            if result.data:
                logger.info(f"Created company record: {company.company_name} (ID: {result.data[0]['id']})")
                return result.data[0]
            else:
                raise Exception(f"Failed to create company record: {result}")
                
        except Exception as e:
            logger.error(f"Failed to create company {company.company_name}: {str(e)}")
            raise
    
    def update(self, company_id: Union[str, uuid.UUID], company: CanonicalCompany) -> Dict[str, Any]:
        """
        Update an existing company record.
        
        Args:
            company_id: UUID of the company to update
            company: Updated CanonicalCompany model instance
            
        Returns:
            Dict containing the updated company record
            
        Raises:
            Exception: If database operation fails
        """
        try:
            # Convert the CanonicalCompany model to database format
            db_data = self._model_to_db_format(company, is_update=True)
            
            # Update in database
            result = self.client.table(self.table_name).update(db_data).eq("id", str(company_id)).execute()
            
            if result.data:
                logger.info(f"Updated company record: {company.company_name} (ID: {company_id})")
                return result.data[0]
            else:
                raise Exception(f"No company found with ID: {company_id}")
                
        except Exception as e:
            logger.error(f"Failed to update company {company_id}: {str(e)}")
            raise
    
    def upsert_by_linkedin_id(self, company: CanonicalCompany) -> Dict[str, Any]:
        """
        Insert or update a company based on LinkedIn company ID.
        
        Args:
            company: CanonicalCompany model instance
            
        Returns:
            Dict containing the upserted company record
        """
        try:
            # Convert to database format
            db_data = self._model_to_db_format(company)
            
            # Upsert based on linkedin_company_id
            result = self.client.table(self.table_name).upsert(
                db_data,
                on_conflict="linkedin_company_id"
            ).execute()
            
            if result.data:
                action = "Updated" if len(result.data) == 1 else "Created"
                logger.info(f"{action} company record: {company.company_name} (LinkedIn ID: {company.company_id})")
                return result.data[0]
            else:
                raise Exception(f"Failed to upsert company record: {result}")
                
        except Exception as e:
            logger.error(f"Failed to upsert company {company.company_name}: {str(e)}")
            raise
    
    def get_by_id(self, company_id: Union[str, uuid.UUID]) -> Optional[CanonicalCompany]:
        """
        Get a company by its database ID.
        
        Args:
            company_id: UUID of the company
            
        Returns:
            CanonicalCompany instance or None if not found
        """
        try:
            result = self.client.table(self.table_name).select("*").eq("id", str(company_id)).execute()
            
            if result.data:
                return self._db_to_model_format(result.data[0])
            return None
            
        except Exception as e:
            logger.error(f"Failed to get company by ID {company_id}: {str(e)}")
            return None
    
    def get_by_linkedin_id(self, linkedin_company_id: str) -> Optional[CanonicalCompany]:
        """
        Get a company by its LinkedIn company ID.
        
        Args:
            linkedin_company_id: LinkedIn company ID
            
        Returns:
            CanonicalCompany instance or None if not found
        """
        try:
            result = self.client.table(self.table_name).select("*").eq("linkedin_company_id", linkedin_company_id).execute()
            
            if result.data:
                return self._db_to_model_format(result.data[0])
            return None
            
        except Exception as e:
            logger.error(f"Failed to get company by LinkedIn ID {linkedin_company_id}: {str(e)}")
            return None
    
    def search_by_name(self, name_query: str, limit: int = 20) -> List[CanonicalCompany]:
        """
        Search companies by name.
        
        Args:
            name_query: Company name search query
            limit: Maximum number of results to return
            
        Returns:
            List of CanonicalCompany instances
        """
        try:
            result = self.client.table(self.table_name).select("*").ilike(
                "company_name", f"%{name_query}%"
            ).limit(limit).execute()
            
            return [self._db_to_model_format(row) for row in result.data]
            
        except Exception as e:
            logger.error(f"Failed to search companies by name '{name_query}': {str(e)}")
            return []
    
    def search_by_domain(self, domain: str, exact_match: bool = False) -> List[CanonicalCompany]:
        """
        Search companies by domain.
        
        Args:
            domain: Domain to search for
            exact_match: Whether to match exactly or use partial matching
            
        Returns:
            List of CanonicalCompany instances
        """
        try:
            query = self.client.table(self.table_name).select("*")
            
            if exact_match:
                query = query.eq("domain", domain.lower())
            else:
                query = query.ilike("domain", f"%{domain.lower()}%")
            
            result = query.limit(50).execute()
            return [self._db_to_model_format(row) for row in result.data]
            
        except Exception as e:
            logger.error(f"Failed to search companies by domain '{domain}': {str(e)}")
            return []
    
    def get_companies_by_size_category(self, category: str = "all", limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get companies filtered by size category.
        
        Args:
            category: Size category (startup, small, medium, large, enterprise, unknown, all)
            limit: Maximum number of results
            
        Returns:
            List of company records with size information
        """
        try:
            # Use the database function if available, otherwise implement logic here
            result = self.client.rpc("get_companies_by_size_category", {
                "category": category,
                "limit_count": limit
            }).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            # Fallback to manual filtering if function doesn't exist
            logger.warning(f"Database function not available, using fallback: {str(e)}")
            return self._get_companies_by_size_fallback(category, limit)
    
    def get_startup_companies(self, limit: int = 25) -> List[Dict[str, Any]]:
        """
        Get companies that match startup criteria.
        
        Args:
            limit: Maximum number of results
            
        Returns:
            List of startup company records
        """
        try:
            result = self.client.rpc("get_startup_companies", {
                "limit_count": limit
            }).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            # Fallback implementation
            logger.warning(f"Database function not available, using fallback: {str(e)}")
            return self._get_startup_companies_fallback(limit)
    
    def vector_similarity_search(self, query_embedding: List[float], threshold: float = 0.2, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Perform vector similarity search for companies.
        
        Args:
            query_embedding: Query embedding vector (1536 dimensions for OpenAI)
            threshold: Similarity threshold (0.0 to 1.0)
            limit: Maximum number of results
            
        Returns:
            List of similar companies with similarity scores
        """
        try:
            result = self.client.rpc("match_companies", {
                "query_embedding": query_embedding,
                "match_threshold": threshold,
                "match_count": limit
            }).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Failed to perform vector similarity search: {str(e)}")
            return []
    
    def get_companies_by_location(self, city: Optional[str] = None, country: Optional[str] = None, limit: int = 50) -> List[CanonicalCompany]:
        """
        Get companies by location (city and/or country).
        
        Args:
            city: City name to filter by
            country: Country name to filter by
            limit: Maximum number of results
            
        Returns:
            List of CanonicalCompany instances
        """
        try:
            query = self.client.table(self.table_name).select("*")
            
            if city:
                query = query.ilike("hq_city", f"%{city}%")
            if country:
                query = query.ilike("hq_country", f"%{country}%")
            
            result = query.limit(limit).execute()
            return [self._db_to_model_format(row) for row in result.data]
            
        except Exception as e:
            logger.error(f"Failed to get companies by location (city: {city}, country: {country}): {str(e)}")
            return []
    
    def get_companies_by_industry(self, industry: str, limit: int = 50) -> List[CanonicalCompany]:
        """
        Get companies by industry.
        
        Args:
            industry: Industry name to filter by
            limit: Maximum number of results
            
        Returns:
            List of CanonicalCompany instances
        """
        try:
            # PostgreSQL array contains query
            result = self.client.table(self.table_name).select("*").contains(
                "industries", [industry]
            ).limit(limit).execute()
            
            return [self._db_to_model_format(row) for row in result.data]
            
        except Exception as e:
            logger.error(f"Failed to get companies by industry '{industry}': {str(e)}")
            return []
    
    def delete(self, company_id: Union[str, uuid.UUID]) -> bool:
        """
        Delete a company record.
        
        Args:
            company_id: UUID of the company to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            result = self.client.table(self.table_name).delete().eq("id", str(company_id)).execute()
            
            if result.data:
                logger.info(f"Deleted company record: {company_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete company {company_id}: {str(e)}")
            return False
    
    def _model_to_db_format(self, company: CanonicalCompany, is_update: bool = False) -> Dict[str, Any]:
        """
        Convert CanonicalCompany model to database format.
        
        Args:
            company: CanonicalCompany model instance
            is_update: Whether this is for an update operation
            
        Returns:
            Dictionary formatted for database insertion/update
        """
        # Get the model data
        data = company.model_dump()
        
        # Map to database column names and handle special cases
        db_data = {
            "linkedin_company_id": data.get("company_id", ""),
            "company_name": data["company_name"],
            "description": data.get("description"),
            "website": str(data["website"]) if data.get("website") else None,
            "linkedin_url": str(data["linkedin_url"]) if data.get("linkedin_url") else None,
            "employee_count": data.get("employee_count"),
            "employee_range": data.get("employee_range"),
            "year_founded": data.get("year_founded"),
            "industries": data.get("industries", []),
            "hq_city": data.get("hq_city"),
            "hq_region": data.get("hq_region"),
            "hq_country": data.get("hq_country"),
            "locations": data.get("locations", []),
            "funding_info": data.get("funding_info"),
            # Enhanced fields (will be ignored if columns don't exist yet)
            "tagline": data.get("tagline"),
            "domain": data.get("domain"),
            "logo_url": str(data["logo_url"]) if data.get("logo_url") else None,
            "specialties": data.get("specialties"),
            "follower_count": data.get("follower_count"),
            "hq_address_line1": data.get("hq_address_line1"),
            "hq_address_line2": data.get("hq_address_line2"),
            "hq_postalcode": data.get("hq_postalcode"),
            "hq_full_address": data.get("hq_full_address"),
            "email": data.get("email"),
            "phone": data.get("phone"),
            "affiliated_companies": data.get("affiliated_companies", []),
            "raw_data": data.get("raw_data"),
            "timestamp": data.get("timestamp", datetime.now(timezone.utc)).isoformat()
        }
        
        # Remove None values and computed fields
        computed_fields = {"display_name", "company_age", "size_category", "headquarters", "specialties_list"}
        db_data = {k: v for k, v in db_data.items() if v is not None and k not in computed_fields}
        
        # Set updated_at for updates
        if is_update:
            db_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        return db_data
    
    def _db_to_model_format(self, db_row: Dict[str, Any]) -> CanonicalCompany:
        """
        Convert database row to CanonicalCompany model.
        
        Args:
            db_row: Database row data
            
        Returns:
            CanonicalCompany model instance
        """
        # Map database columns to model fields
        model_data = {
            "company_id": db_row.get("linkedin_company_id"),
            "company_name": db_row["company_name"],
            "linkedin_url": db_row.get("linkedin_url"),
            "tagline": db_row.get("tagline"),
            "description": db_row.get("description"),
            "website": db_row.get("website"),
            "domain": db_row.get("domain"),
            "logo_url": db_row.get("logo_url"),
            "year_founded": db_row.get("year_founded"),
            "industries": db_row.get("industries", []),
            "specialties": db_row.get("specialties"),
            "employee_count": db_row.get("employee_count"),
            "employee_range": db_row.get("employee_range"),
            "follower_count": db_row.get("follower_count"),
            "hq_address_line1": db_row.get("hq_address_line1"),
            "hq_address_line2": db_row.get("hq_address_line2"),
            "hq_city": db_row.get("hq_city"),
            "hq_region": db_row.get("hq_region"),
            "hq_country": db_row.get("hq_country"),
            "hq_postalcode": db_row.get("hq_postalcode"),
            "hq_full_address": db_row.get("hq_full_address"),
            "email": db_row.get("email"),
            "phone": db_row.get("phone"),
            "funding_info": db_row.get("funding_info"),
            "locations": db_row.get("locations", []),
            "affiliated_companies": db_row.get("affiliated_companies", []),
            "timestamp": db_row.get("timestamp") or db_row.get("created_at"),
            "raw_data": db_row.get("raw_data")
        }
        
        # Remove None values
        model_data = {k: v for k, v in model_data.items() if v is not None}
        
        try:
            return CanonicalCompany(**model_data)
        except ValidationError as e:
            logger.error(f"Failed to create CanonicalCompany from database row: {str(e)}")
            # Log the problematic data for debugging
            logger.debug(f"Problematic data: {model_data}")
            raise
    
    def _get_companies_by_size_fallback(self, category: str, limit: int) -> List[Dict[str, Any]]:
        """Fallback implementation for size category filtering."""
        try:
            query = self.client.table(self.table_name).select("id, company_name, employee_count")
            
            # Apply size filters
            if category == "startup":
                query = query.lt("employee_count", 10)
            elif category == "small":
                query = query.gte("employee_count", 10).lt("employee_count", 50)
            elif category == "medium":
                query = query.gte("employee_count", 50).lt("employee_count", 200)
            elif category == "large":
                query = query.gte("employee_count", 200).lt("employee_count", 1000)
            elif category == "enterprise":
                query = query.gte("employee_count", 1000)
            elif category == "unknown":
                query = query.is_("employee_count", "null")
            
            result = query.limit(limit).execute()
            
            # Add size_category to results
            for row in result.data:
                emp_count = row.get("employee_count")
                if emp_count is None:
                    row["size_category"] = "Unknown"
                elif emp_count < 10:
                    row["size_category"] = "Startup"
                elif emp_count < 50:
                    row["size_category"] = "Small"
                elif emp_count < 200:
                    row["size_category"] = "Medium"
                elif emp_count < 1000:
                    row["size_category"] = "Large"
                else:
                    row["size_category"] = "Enterprise"
            
            return result.data
            
        except Exception as e:
            logger.error(f"Fallback size category query failed: {str(e)}")
            return []
    
    def _get_startup_companies_fallback(self, limit: int) -> List[Dict[str, Any]]:
        """Fallback implementation for startup filtering."""
        try:
            current_year = datetime.now().year
            
            # Get companies with startup characteristics
            result = self.client.table(self.table_name).select(
                "id, company_name, employee_count, year_founded, funding_info, domain"
            ).or_(
                f"employee_count.lt.200,and(employee_count.lt.50,year_founded.gt.{current_year - 7})"
            ).limit(limit * 2).execute()  # Get more to filter
            
            # Filter and enhance results
            startup_companies = []
            for row in result.data:
                emp_count = row.get("employee_count")
                year_founded = row.get("year_founded")
                funding_info = row.get("funding_info", {})
                
                # Calculate company age
                company_age = current_year - year_founded if year_founded else None
                
                # Check startup criteria
                is_small = emp_count is None or emp_count < 200
                is_young = year_founded is None or year_founded > current_year - 10
                has_startup_funding = False
                
                if funding_info and isinstance(funding_info, dict):
                    funding_type = funding_info.get("last_funding_round_type", "").lower()
                    has_startup_funding = any(term in funding_type for term in ["seed", "series a", "series b", "angel"])
                
                is_startup = is_small and is_young and (
                    has_startup_funding or 
                    ((emp_count is None or emp_count < 50) and (company_age is None or company_age <= 7))
                )
                
                if is_startup:
                    row["company_age"] = company_age
                    row["has_funding"] = bool(funding_info)
                    startup_companies.append(row)
                
                if len(startup_companies) >= limit:
                    break
            
            return startup_companies
            
        except Exception as e:
            logger.error(f"Fallback startup query failed: {str(e)}")
            return []
