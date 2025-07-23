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
                )\n                \n                response = await client.post(\n                    url=url,\n                    json=payload\n                )\n                \n                # Handle HTTP errors\n                if response.status_code == 429:\n                    retry_after = response.headers.get(\"Retry-After\", \"60\")\n                    raise CassidyRateLimitError(\n                        f\"Rate limit exceeded. Retry after {retry_after} seconds\",\n                        status_code=response.status_code,\n                        details={\"retry_after\": retry_after}\n                    )\n                \n                if response.status_code >= 400:\n                    error_details = {}\n                    try:\n                        error_details = response.json()\n                    except json.JSONDecodeError:\n                        pass\n                    \n                    raise CassidyAPIError(\n                        f\"Cassidy API error: HTTP {response.status_code}\",\n                        status_code=response.status_code,\n                        details=error_details\n                    )\n                \n                # Parse response JSON\n                try:\n                    response_data = response.json()\n                except json.JSONDecodeError as e:\n                    raise CassidyValidationError(\n                        f\"Invalid JSON response from Cassidy API: {str(e)}\",\n                        details={\"raw_response\": response.text[:1000]}\n                    )\n                \n                execution_time = (datetime.utcnow() - start_time).total_seconds()\n                \n                self.logger.debug(\n                    f\"Workflow {workflow_type} completed\",\n                    execution_time_seconds=execution_time,\n                    status_code=response.status_code\n                )\n                \n                return response_data\n                \n        except httpx.TimeoutException as e:\n            raise CassidyTimeoutError(\n                f\"Cassidy workflow timeout after {self.timeout} seconds\",\n                details={\"timeout_seconds\": self.timeout}\n            ) from e\n            \n        except httpx.ConnectError as e:\n            raise CassidyConnectionError(\n                f\"Failed to connect to Cassidy API: {str(e)}\",\n                details={\"url\": url}\n            ) from e\n    \n    def _extract_profile_data(self, response_data: Dict[str, Any]) -> Dict[str, Any]:\n        \"\"\"\n        Extract and normalize profile data from Cassidy workflow response\n        \n        Based on the blueprint structure:\n        - workflowRun.actionResults[].output.value contains the parsed JSON\n        \n        Args:\n            response_data: Raw response from Cassidy workflow\n            \n        Returns:\n            Dict containing normalized profile data\n            \n        Raises:\n            CassidyWorkflowError: If response structure is invalid\n        \"\"\"\n        try:\n            # Navigate through the workflow response structure\n            workflow_run = response_data.get(\"workflowRun\", {})\n            action_results = workflow_run.get(\"actionResults\", [])\n            \n            if not action_results:\n                raise CassidyWorkflowError(\n                    \"No action results found in workflow response\",\n                    details={\"response_keys\": list(response_data.keys())}\n                )\n            \n            # Find the action result with profile data\n            # Based on blueprint, this should be in the first action result's output.value\n            profile_data = None\n            for action_result in action_results:\n                output = action_result.get(\"output\", {})\n                value = output.get(\"value\")\n                \n                if value and isinstance(value, (dict, str)):\n                    # If value is a string, parse it as JSON\n                    if isinstance(value, str):\n                        try:\n                            profile_data = json.loads(value)\n                        except json.JSONDecodeError:\n                            continue\n                    else:\n                        profile_data = value\n                    break\n            \n            if not profile_data:\n                raise CassidyWorkflowError(\n                    \"No valid profile data found in workflow response\",\n                    details={\"action_results_count\": len(action_results)}\n                )\n            \n            # Handle case where profile_data might be wrapped in an array\n            if isinstance(profile_data, list) and len(profile_data) > 0:\n                profile_data = profile_data[0]\n            \n            return profile_data\n            \n        except (KeyError, ValueError, TypeError) as e:\n            raise CassidyWorkflowError(\n                f\"Failed to extract profile data from response: {str(e)}\",\n                details={\"response_structure\": str(response_data)[:500]}\n            ) from e\n    \n    def _extract_company_data(self, response_data: Dict[str, Any]) -> Dict[str, Any]:\n        \"\"\"\n        Extract and normalize company data from Cassidy workflow response\n        \n        Args:\n            response_data: Raw response from Cassidy workflow\n            \n        Returns:\n            Dict containing normalized company data\n            \n        Raises:\n            CassidyWorkflowError: If response structure is invalid\n        \"\"\"\n        try:\n            # Use similar extraction logic as profile data\n            workflow_run = response_data.get(\"workflowRun\", {})\n            action_results = workflow_run.get(\"actionResults\", [])\n            \n            if not action_results:\n                raise CassidyWorkflowError(\n                    \"No action results found in company workflow response\",\n                    details={\"response_keys\": list(response_data.keys())}\n                )\n            \n            # Find the action result with company data\n            company_data = None\n            for action_result in action_results:\n                output = action_result.get(\"output\", {})\n                value = output.get(\"value\")\n                \n                if value and isinstance(value, (dict, str)):\n                    if isinstance(value, str):\n                        try:\n                            company_data = json.loads(value)\n                        except json.JSONDecodeError:\n                            continue\n                    else:\n                        company_data = value\n                    break\n            \n            if not company_data:\n                # For company workflows, there might be an error fallback\n                # Check if this is an expected empty response\n                self.logger.warning(\"No company data found, using empty fallback\")\n                return {\n                    \"company_name\": \"Unknown Company\",\n                    \"description\": None,\n                    \"employee_count\": None,\n                    \"industries\": [],\n                }\n            \n            # Handle case where company_data might be wrapped in an array\n            if isinstance(company_data, list) and len(company_data) > 0:\n                company_data = company_data[0]\n            \n            return company_data\n            \n        except (KeyError, ValueError, TypeError) as e:\n            raise CassidyWorkflowError(\n                f\"Failed to extract company data from response: {str(e)}\",\n                details={\"response_structure\": str(response_data)[:500]}\n            ) from e\n    \n    async def batch_fetch_companies(\n        self, \n        company_urls: list[str], \n        delay_seconds: float = 10.0\n    ) -> list[CompanyProfile]:\n        \"\"\"\n        Fetch multiple company profiles with delay between requests\n        \n        Based on the blueprint, there's a 10-second sleep between company requests\n        to respect rate limits.\n        \n        Args:\n            company_urls: List of LinkedIn company URLs to fetch\n            delay_seconds: Delay between requests (default 10 seconds)\n            \n        Returns:\n            List of CompanyProfile objects (may contain None for failed fetches)\n        \"\"\"\n        self.logger.info(\n            \"Starting batch company fetch\",\n            company_count=len(company_urls),\n            delay_seconds=delay_seconds\n        )\n        \n        companies = []\n        \n        for i, company_url in enumerate(company_urls):\n            try:\n                company = await self.fetch_company(company_url)\n                companies.append(company)\n                \n                # Add delay between requests (except for the last one)\n                if i < len(company_urls) - 1:\n                    self.logger.debug(\n                        f\"Waiting {delay_seconds}s before next company fetch\",\n                        current_index=i,\n                        remaining=len(company_urls) - i - 1\n                    )\n                    await asyncio.sleep(delay_seconds)\n                    \n            except Exception as e:\n                self.logger.warning(\n                    \"Company fetch failed, continuing with batch\",\n                    company_url=company_url,\n                    error=str(e)\n                )\n                companies.append(None)  # Add None for failed fetches\n        \n        successful_fetches = sum(1 for c in companies if c is not None)\n        self.logger.info(\n            \"Batch company fetch completed\",\n            total_requested=len(company_urls),\n            successful=successful_fetches,\n            failed=len(company_urls) - successful_fetches\n        )\n        \n        return companies\n    \n    async def health_check(self) -> Dict[str, Any]:\n        \"\"\"\n        Check connectivity to Cassidy API\n        \n        Returns:\n            Dict with health check results\n        \"\"\"\n        try:\n            async with httpx.AsyncClient(timeout=5.0) as client:\n                response = await client.head(\"https://app.cassidyai.com\")\n                return {\n                    \"status\": \"healthy\" if response.status_code < 400 else \"unhealthy\",\n                    \"status_code\": response.status_code,\n                    \"response_time_ms\": response.elapsed.total_seconds() * 1000\n                }\n        except Exception as e:\n            return {\n                \"status\": \"unhealthy\",\n                \"error\": str(e),\n                \"error_type\": type(e).__name__\n            }"
