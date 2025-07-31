"""
HTTP client for Cassidy AI workflows

Handles communication with Cassidy webhook endpoints for LinkedIn profile 
and company data scraping with robust error handling and retry logic.
"""

import asyncio
import json
from typing import Dict, Any, Optional, Union
from datetime import datetime, timedelta, timezone
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from app.core.config import settings
from app.core.logging import LoggerMixin
from .exceptions import (
    CassidyAPIError,
    CassidyTimeoutError,
    CassidyWorkflowError,
    CassidyRateLimitError,
    CassidyConnectionError,
    CassidyValidationError,
)
from .models import (
    LinkedInProfile,
    CompanyProfile,
    CassidyWorkflowResponse,
    WorkflowStatus,
)


class CassidyClient(LoggerMixin):
    """
    HTTP client for Cassidy AI workflows
    
    Provides methods to interact with Cassidy webhook endpoints for 
    LinkedIn profile and company data extraction.
    """
    
    def __init__(self):
        self.profile_workflow_url = settings.CASSIDY_PROFILE_WORKFLOW_URL
        self.company_workflow_url = settings.CASSIDY_COMPANY_WORKFLOW_URL
        self.timeout = settings.CASSIDY_TIMEOUT
        self.max_retries = settings.CASSIDY_MAX_RETRIES
        self.backoff_factor = settings.CASSIDY_BACKOFF_FACTOR
        
        # HTTP client configuration
        self.client_config = {
            "timeout": httpx.Timeout(
                connect=30.0,
                read=self.timeout,
                write=30.0,
                pool=30.0
            ),
            "limits": httpx.Limits(
                max_keepalive_connections=10,
                max_connections=20,
                keepalive_expiry=30.0
            ),
            "headers": {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": f"LinkedIn-Ingestion-Service/{settings.VERSION}",
            }
        }
    
    async def fetch_profile(self, linkedin_url: str) -> LinkedInProfile:
        """
        Fetch LinkedIn profile data using Cassidy workflow
        
        Args:
            linkedin_url: LinkedIn profile URL to scrape
            
        Returns:
            LinkedInProfile: Parsed profile data
            
        Raises:
            CassidyException: Various Cassidy-related errors
        """
        self.logger.info("Starting profile fetch", linkedin_url=linkedin_url)
        
        try:
            # Prepare request payload based on blueprint structure
            payload = {
                "profile": linkedin_url
            }
            
            # Execute workflow with retry logic
            response_data = await self._execute_workflow_with_retry(
                url=self.profile_workflow_url,
                payload=payload,
                workflow_type="profile"
            )
            
            # Parse and validate response
            profile_data = self._extract_profile_data(response_data)
            
            # Transform API response to match LinkedInProfile model
            transformed_data = self._transform_profile_data(profile_data)
            profile = LinkedInProfile(**transformed_data)
            
            self.logger.info(
                "Profile fetch completed successfully",
                linkedin_url=linkedin_url,
                profile_id=profile.id,
                experience_count=len(profile.experience) if profile.experience else 0
            )
            
            return profile
            
        except Exception as e:
            self.logger.error(
                "Profile fetch failed",
                linkedin_url=linkedin_url,
                error=str(e),
                error_type=type(e).__name__
            )
            raise
    
    async def fetch_company(self, company_url: str) -> CompanyProfile:
        """
        Fetch company profile data using Cassidy workflow
        
        Args:
            company_url: LinkedIn company URL to scrape
            
        Returns:
            CompanyProfile: Parsed company data
            
        Raises:
            CassidyException: Various Cassidy-related errors
        """
        self.logger.info("Starting company fetch", company_url=company_url)
        
        try:
            # Prepare request payload based on blueprint structure
            payload = {
                "profile": company_url
            }
            
            # Execute workflow with retry logic
            response_data = await self._execute_workflow_with_retry(
                url=self.company_workflow_url,
                payload=payload,
                workflow_type="company"
            )
            
            # Parse and validate response
            company_data = self._extract_company_data(response_data)
            
            # Transform API response to match CompanyProfile model
            transformed_data = self._transform_company_data(company_data)
            company = CompanyProfile(**transformed_data)
            
            self.logger.info(
                "Company fetch completed successfully",
                company_url=company_url,
                company_name=company.company_name,
                employee_count=company.employee_count
            )
            
            return company
            
        except Exception as e:
            self.logger.error(
                "Company fetch failed",
                company_url=company_url,
                error=str(e),
                error_type=type(e).__name__
            )
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=4, max=60),
        retry=retry_if_exception_type((
            CassidyConnectionError,
            CassidyRateLimitError,
            httpx.TimeoutException,
            httpx.ConnectError,
        )),
        # Note: before_sleep logging removed due to initialization order
    )
    async def _execute_workflow_with_retry(
        self, 
        url: str, 
        payload: Dict[str, Any], 
        workflow_type: str
    ) -> Dict[str, Any]:
        """
        Execute Cassidy workflow with retry logic
        
        Args:
            url: Cassidy workflow webhook URL
            payload: Request payload
            workflow_type: Type of workflow (profile/company) for logging
            
        Returns:
            Dict containing workflow response data
            
        Raises:
            CassidyException: Various workflow execution errors
        """
        start_time = datetime.now(timezone.utc)
        
        try:
            async with httpx.AsyncClient(**self.client_config) as client:
                self.logger.debug(
                    f"Executing {workflow_type} workflow",
                    url=url,
                    payload=payload
                )
                
                response = await client.post(
                    url=url,
                    json=payload
                )
                
                # Handle HTTP errors
                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After", "60")
                    raise CassidyRateLimitError(
                        f"Rate limit exceeded. Retry after {retry_after} seconds",
                        status_code=response.status_code,
                        details={"retry_after": retry_after}
                    )
                
                if response.status_code >= 400:
                    error_details = {}
                    try:
                        error_details = response.json()
                    except json.JSONDecodeError:
                        pass
                    
                    raise CassidyAPIError(
                        f"Cassidy API error: HTTP {response.status_code}",
                        status_code=response.status_code,
                        details=error_details
                    )
                
                # Parse response JSON
                try:
                    response_data = response.json()
                except json.JSONDecodeError as e:
                    raise CassidyValidationError(
                        f"Invalid JSON response from Cassidy API: {str(e)}",
                        details={"raw_response": response.text[:1000]}
                    )
                
                execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
                
                # DEBUG: Log the actual response structure to understand format
                self.logger.info(
                    f"DEBUG: Cassidy {workflow_type} response structure",
                    response_keys=list(response_data.keys()),
                    response_sample=str(response_data)[:500]
                )
                
                self.logger.debug(
                    f"Workflow {workflow_type} completed",
                    execution_time_seconds=execution_time,
                    status_code=response.status_code
                )
                
                return response_data
                
        except httpx.TimeoutException as e:
            raise CassidyTimeoutError(
                f"Cassidy workflow timeout after {self.timeout} seconds",
                details={"timeout_seconds": self.timeout}
            ) from e
            
        except httpx.ConnectError as e:
            raise CassidyConnectionError(
                f"Failed to connect to Cassidy API: {str(e)}",
                details={"url": url}
            ) from e
    
    def _extract_profile_data(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract and normalize profile data from Cassidy workflow response
        
        Real Cassidy API structure:
        - workflowRun.status indicates success/failure
        - workflowRun.actionResults[].output.value contains the parsed JSON on success
        - workflowRun.actionResults[].error contains error message on failure
        
        Args:
            response_data: Raw response from Cassidy workflow
            
        Returns:
            Dict containing normalized profile data
            
        Raises:
            CassidyWorkflowError: If response structure is invalid or workflow failed
        """
        try:
            # Navigate through the workflow response structure
            workflow_run = response_data.get("workflowRun", {})
            workflow_status = workflow_run.get("status", "UNKNOWN")
            action_results = workflow_run.get("actionResults", [])
            
            # Check if workflow failed  
            if workflow_status in ["FAILED", "failed"]:
                error_messages = []
                for action_result in action_results:
                    if action_result.get("status") in ["FAILED", "failed"] and "error" in action_result:
                        error_messages.append(action_result["error"])
                
                error_summary = "; ".join(error_messages) if error_messages else "Workflow failed with no specific error"
                raise CassidyWorkflowError(
                    f"Cassidy workflow failed: {error_summary}",
                    details={"workflow_status": workflow_status, "action_results": action_results}
                )
            
            if not action_results:
                raise CassidyWorkflowError(
                    "No action results found in workflow response",
                    details={"response_keys": list(response_data.keys())}
                )
            
            # Find the action result with profile data
            # Look for successful action with output.value (case-insensitive)
            profile_data = None
            for action_result in action_results:
                status = action_result.get("status", "").lower()
                if status in ["success", "SUCCESS", "completed"]:
                    output = action_result.get("output", {})
                    value = output.get("value")
                    
                    if value and isinstance(value, (dict, str)):
                        # If value is a string, parse it as JSON
                        if isinstance(value, str):
                            try:
                                profile_data = json.loads(value)
                            except json.JSONDecodeError:
                                continue
                        else:
                            profile_data = value
                        break
            
            if not profile_data:
                raise CassidyWorkflowError(
                    "No valid profile data found in successful workflow response",
                    details={
                        "action_results_count": len(action_results),
                        "workflow_status": workflow_status,
                        "action_statuses": [ar.get("status") for ar in action_results]
                    }
                )
            
            # Handle case where profile_data might be wrapped in an array
            if isinstance(profile_data, list) and len(profile_data) > 0:
                profile_data = profile_data[0]
            
            # ENHANCED DEBUG: Log the actual profile data structure to understand what's missing
            self.logger.info(
                "DEBUG: Extracted profile data structure",
                profile_keys=list(profile_data.keys()) if isinstance(profile_data, dict) else "NOT_DICT",
                has_experiences=('experiences' in profile_data) if isinstance(profile_data, dict) else False,
                experiences_type=type(profile_data.get('experiences', None)).__name__ if isinstance(profile_data, dict) else "N/A",
                experiences_length=len(profile_data.get('experiences', [])) if isinstance(profile_data, dict) and isinstance(profile_data.get('experiences'), list) else "N/A",
                has_educations=('educations' in profile_data) if isinstance(profile_data, dict) else False,
                sample_fields={k: str(v)[:100] + "..." if isinstance(v, str) and len(str(v)) > 100 else v for k, v in list(profile_data.items())[:5]} if isinstance(profile_data, dict) else "NOT_DICT"
            )
            
            return profile_data
            
        except (KeyError, ValueError, TypeError) as e:
            raise CassidyWorkflowError(
                f"Failed to extract profile data from response: {str(e)}",
                details={"response_structure": str(response_data)[:500]}
            ) from e
    
    def _extract_company_data(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract and normalize company data from Cassidy workflow response
        
        Args:
            response_data: Raw response from Cassidy workflow
            
        Returns:
            Dict containing normalized company data
            
        Raises:
            CassidyWorkflowError: If response structure is invalid
        """
        try:
            # Use similar extraction logic as profile data
            workflow_run = response_data.get("workflowRun", {})
            action_results = workflow_run.get("actionResults", [])
            
            if not action_results:
                raise CassidyWorkflowError(
                    "No action results found in company workflow response",
                    details={"response_keys": list(response_data.keys())}
                )
            
            # Find the action result with company data
            company_data = None
            for action_result in action_results:
                output = action_result.get("output", {})
                value = output.get("value")
                
                if value and isinstance(value, (dict, str)):
                    if isinstance(value, str):
                        try:
                            company_data = json.loads(value)
                        except json.JSONDecodeError:
                            continue
                    else:
                        company_data = value
                    break
            
            if not company_data:
                # For company workflows, there might be an error fallback
                # Check if this is an expected empty response
                self.logger.warning("No company data found, using empty fallback")
                return {
                    "company_name": "Unknown Company",
                    "description": None,
                    "employee_count": None,
                    "industries": [],
                }
            
            # Handle case where company_data might be wrapped in an array
            if isinstance(company_data, list) and len(company_data) > 0:
                company_data = company_data[0]
            
            return company_data
            
        except (KeyError, ValueError, TypeError) as e:
            raise CassidyWorkflowError(
                f"Failed to extract company data from response: {str(e)}",
                details={"response_structure": str(response_data)[:500]}
            ) from e
    
    async def batch_fetch_companies(
        self, 
        company_urls: list[str], 
        delay_seconds: float = 10.0
    ) -> list[CompanyProfile]:
        """
        Fetch multiple company profiles with delay between requests
        
        Based on the blueprint, there's a 10-second sleep between company requests
        to respect rate limits.
        
        Args:
            company_urls: List of LinkedIn company URLs to fetch
            delay_seconds: Delay between requests (default 10 seconds)
            
        Returns:
            List of CompanyProfile objects (may contain None for failed fetches)
        """
        self.logger.info(
            "Starting batch company fetch",
            company_count=len(company_urls),
            delay_seconds=delay_seconds
        )
        
        companies = []
        
        for i, company_url in enumerate(company_urls):
            try:
                company = await self.fetch_company(company_url)
                companies.append(company)
                
                # Add delay between requests (except for the last one)
                if i < len(company_urls) - 1:
                    self.logger.debug(
                        f"Waiting {delay_seconds}s before next company fetch",
                        current_index=i,
                        remaining=len(company_urls) - i - 1
                    )
                    await asyncio.sleep(delay_seconds)
                    
            except Exception as e:
                self.logger.warning(
                    "Company fetch failed, continuing with batch",
                    company_url=company_url,
                    error=str(e)
                )
                companies.append(None)  # Add None for failed fetches
        
        successful_fetches = sum(1 for c in companies if c is not None)
        self.logger.info(
            "Batch company fetch completed",
            total_requested=len(company_urls),
            successful=successful_fetches,
            failed=len(company_urls) - successful_fetches
        )
        
        return companies
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check connectivity to Cassidy API
        
        Returns:
            Dict with health check results
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.head("https://app.cassidyai.com")
                return {
                    "status": "healthy" if response.status_code < 400 else "unhealthy",
                    "status_code": response.status_code,
                    "response_time_ms": response.elapsed.total_seconds() * 1000
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    def _transform_profile_data(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform raw API response to match LinkedInProfile model fields
        
        The API returns fields like 'id', 'name', 'url' but the model expects
        'profile_id', 'full_name', 'linkedin_url' (with aliases).
        
        Args:
            profile_data: Raw profile data from API
            
        Returns:
            Dict with transformed field names and processed nested data
        """
        from datetime import datetime
        
        # Handle the core field mapping - Pydantic aliases will handle this,
        # but we need to ensure nested data is properly structured
        transformed = profile_data.copy()
        
        # Map API fields to model fields
        if 'name' in profile_data:
            transformed['full_name'] = profile_data['name']
        if 'id' in profile_data:
            transformed['profile_id'] = profile_data['id']
        if 'url' in profile_data:
            transformed['linkedin_url'] = profile_data['url']
        
        # Transform experience array
        if 'experiences' in profile_data and isinstance(profile_data['experiences'], list):
            transformed_experiences = []
            for exp in profile_data['experiences']:
                if isinstance(exp, dict):
                    # Transform experience entry to match ExperienceEntry model
                    transformed_exp = {
                        'title': exp.get('title'),
                        'company': exp.get('company'),
                        'company_id': exp.get('company_id'),
                        'company_linkedin_url': exp.get('company_linkedin_url'),
                        'location': exp.get('location'),
                        'description': exp.get('description'),
                        'start_date': exp.get('start_date'),
                        'end_date': exp.get('end_date'),
                        'start_year': self._parse_year(exp.get('start_date')),
                        'end_year': self._parse_year(exp.get('end_date')),
                        'start_month': self._parse_month(exp.get('start_date')),
                        'end_month': self._parse_month(exp.get('end_date')),
                        'url': exp.get('url'),
                        'company_logo_url': exp.get('company_logo_url')
                    }
                    transformed_experiences.append(transformed_exp)
            transformed['experiences'] = transformed_experiences
        else:
            transformed['experiences'] = []
        
        # Transform education array
        if 'educations' in profile_data and isinstance(profile_data['educations'], list):
            transformed_educations = []
            for edu in profile_data['educations']:
                if isinstance(edu, dict):
                    # Transform education entry to match EducationEntry model
                    transformed_edu = {
                        'school': edu.get('school'),  # API uses 'school' for school name
                        'degree': edu.get('degree'),
                        'field_of_study': edu.get('field_of_study'),
                        'start_year': self._parse_year(edu.get('start_date')),
                        'end_year': self._parse_year(edu.get('end_date')),
                        'start_month': self._parse_month(edu.get('start_date')),
                        'end_month': self._parse_month(edu.get('end_date')),
                        'url': edu.get('url'),
                        'institute_logo_url': edu.get('institute_logo_url')
                    }
                    transformed_educations.append(transformed_edu)
            transformed['educations'] = transformed_educations
        else:
            transformed['educations'] = []
        
        # Map position field to headline for the alias to work
        if 'position' in profile_data:
            transformed['headline'] = profile_data['position']
        
        # Map country_code to country for the model
        if 'country_code' in profile_data:
            transformed['country'] = profile_data['country_code']
        
        # Handle timestamp conversion
        if 'timestamp' in profile_data and profile_data['timestamp']:
            try:
                # Parse ISO timestamp
                if isinstance(profile_data['timestamp'], str):
                    transformed['timestamp'] = datetime.fromisoformat(profile_data['timestamp'].replace('Z', '+00:00'))
            except (ValueError, TypeError):
                transformed['timestamp'] = None
        
        # Transform certifications array and store in model
        # Note: The model returns certifications via property, but we store raw data 
        # for the property to access
        if 'certifications' in profile_data and isinstance(profile_data['certifications'], list):
            # Store certifications in a field the model can access
            transformed['_certifications'] = profile_data['certifications']
        else:
            transformed['_certifications'] = []
        
        # Map additional social fields
        if 'followers' in profile_data:
            transformed['follower_count'] = profile_data['followers']
        
        if 'connections' in profile_data:
            transformed['connection_count'] = profile_data['connections']
        
        return transformed
    
    def _transform_company_data(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform raw company API response to match CompanyProfile model fields
        
        Args:
            company_data: Raw company data from API
            
        Returns:
            Dict with transformed field names and processed nested data
        """
        transformed = company_data.copy()
        
        # Ensure required fields have defaults
        if 'company_name' not in transformed:
            transformed['company_name'] = transformed.get('name', 'Unknown Company')
        
        if 'company_id' not in transformed:
            transformed['company_id'] = transformed.get('id', 'unknown')
        
        # Convert year_founded to integer if it's a string
        if 'year_founded' in transformed and transformed['year_founded']:
            try:
                if isinstance(transformed['year_founded'], str):
                    transformed['year_founded'] = int(transformed['year_founded'])
            except (ValueError, TypeError):
                transformed['year_founded'] = None
        
        # Ensure industries is a list
        if 'industries' not in transformed or not isinstance(transformed['industries'], list):
            transformed['industries'] = []
        
        # Transform locations array
        if 'locations' in transformed and isinstance(transformed['locations'], list):
            transformed_locations = []
            for loc in transformed['locations']:
                if isinstance(loc, dict):
                    # Ensure location has required fields
                    transformed_loc = {
                        'city': loc.get('city'),
                        'country': loc.get('country'),
                        'region': loc.get('region'),
                        'is_headquarter': loc.get('is_headquarter', False),
                        'full_address': loc.get('full_address'),
                        'line1': loc.get('line1'),
                        'line2': loc.get('line2'),
                        'zipcode': loc.get('zipcode')
                    }
                    transformed_locations.append(transformed_loc)
            transformed['locations'] = transformed_locations
        else:
            transformed['locations'] = []
        
        # Transform funding_info
        if 'funding_info' in transformed and isinstance(transformed['funding_info'], dict):
            funding = transformed['funding_info']
            transformed_funding = {
                'crunchbase_url': funding.get('crunchbase_url'),
                'last_funding_round_amount': funding.get('last_funding_round_amount'),
                'last_funding_round_currency': funding.get('last_funding_round_currency'),
                'last_funding_round_investor_count': funding.get('last_funding_round_investor_count'),
                'last_funding_round_month': funding.get('last_funding_round_month'),
                'last_funding_round_type': funding.get('last_funding_round_type'),
                'last_funding_round_year': funding.get('last_funding_round_year')
            }
            transformed['funding_info'] = transformed_funding
        else:
            transformed['funding_info'] = {}
        
        # Ensure affiliated_companies is a list
        if 'affiliated_companies' not in transformed:
            transformed['affiliated_companies'] = []
        
        return transformed
    
    def _parse_year(self, date_str: str) -> Optional[int]:
        """
        Parse year from date string like '2021' or 'Present'
        
        Args:
            date_str: Date string from API
            
        Returns:
            Parsed year as integer or None
        """
        if not date_str or date_str.lower() in ['present', 'current', 'now']:
            return None
        
        try:
            # Try to extract year from string
            if date_str.isdigit() and len(date_str) == 4:
                return int(date_str)
            # Handle formats like "Jan 2021" or "2021-01"
            import re
            year_match = re.search(r'(\d{4})', date_str)
            if year_match:
                return int(year_match.group(1))
        except (ValueError, TypeError):
            pass
        
        return None
    
    def _parse_month(self, date_str: str) -> Optional[int]:
        """
        Parse month from date string
        
        Args:
            date_str: Date string from API
            
        Returns:
            Parsed month as integer (1-12) or None
        """
        if not date_str or date_str.lower() in ['present', 'current', 'now']:
            return None
        
        try:
            # Handle formats like "2021-01" or "01/2021"
            import re
            month_match = re.search(r'(\d{1,2})[/-](\d{4})', date_str)
            if month_match:
                return int(month_match.group(1))
            
            # Handle month names
            month_names = {
                'jan': 1, 'january': 1,
                'feb': 2, 'february': 2,
                'mar': 3, 'march': 3,
                'apr': 4, 'april': 4,
                'may': 5,
                'jun': 6, 'june': 6,
                'jul': 7, 'july': 7,
                'aug': 8, 'august': 8,
                'sep': 9, 'september': 9,
                'oct': 10, 'october': 10,
                'nov': 11, 'november': 11,
                'dec': 12, 'december': 12
            }
            
            for month_name, month_num in month_names.items():
                if month_name in date_str.lower():
                    return month_num
        except (ValueError, TypeError):
            pass
        
        return None
