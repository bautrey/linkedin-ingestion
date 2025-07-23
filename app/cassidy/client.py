"""
HTTP client for Cassidy AI workflows

Handles communication with Cassidy webhook endpoints for LinkedIn profile 
and company data scraping with robust error handling and retry logic.
"""

import asyncio
import json
from typing import Dict, Any, Optional, Union
from datetime import datetime, timedelta
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
            profile = LinkedInProfile(**profile_data)
            
            self.logger.info(
                "Profile fetch completed successfully",
                linkedin_url=linkedin_url,
                profile_id=profile.id,
                experience_count=len(profile.experience)
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
            company = CompanyProfile(**company_data)
            
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
        before_sleep=before_sleep_log(None, log_level="WARNING"),
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
        start_time = datetime.utcnow()
        
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
                
                execution_time = (datetime.utcnow() - start_time).total_seconds()
                
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
        
        Based on the blueprint structure:
        - workflowRun.actionResults[].output.value contains the parsed JSON
        
        Args:
            response_data: Raw response from Cassidy workflow
            
        Returns:
            Dict containing normalized profile data
            
        Raises:
            CassidyWorkflowError: If response structure is invalid
        """
        try:
            # Navigate through the workflow response structure
            workflow_run = response_data.get("workflowRun", {})
            action_results = workflow_run.get("actionResults", [])
            
            if not action_results:
                raise CassidyWorkflowError(
                    "No action results found in workflow response",
                    details={"response_keys": list(response_data.keys())}
                )
            
            # Find the action result with profile data
            # Based on blueprint, this should be in the first action result's output.value
            profile_data = None
            for action_result in action_results:
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
                    "No valid profile data found in workflow response",
                    details={"action_results_count": len(action_results)}
                )
            
            # Handle case where profile_data might be wrapped in an array
            if isinstance(profile_data, list) and len(profile_data) > 0:
                profile_data = profile_data[0]
            
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
