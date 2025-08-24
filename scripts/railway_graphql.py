#!/usr/bin/env python3
"""
Railway GraphQL API Client

This module provides a robust GraphQL client for interacting with Railway's API
to retrieve logs without hanging terminal issues.

Usage:
    from railway_graphql import RailwayGraphQL
    
    client = RailwayGraphQL()
    logs = client.get_deployment_logs(deployment_id="your-deployment-id")
"""

import os
import json
import time
import random
import requests
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class RailwayConfig:
    """Configuration for Railway API access"""
    api_token: str
    project_id: str
    environment_id: str
    service_id: str
    api_endpoint: str = "https://backboard.railway.app/graphql/v2"
    timeout: int = 30
    max_retries: int = 3
    rate_limit_per_hour: int = 1000
    rate_limit_per_second: int = 10


class RateLimitHandler:
    """Handle rate limiting with exponential backoff"""
    
    def __init__(self, max_requests_per_second: int = 10):
        self.max_requests_per_second = max_requests_per_second
        self.request_times: List[float] = []
    
    def wait_if_needed(self):
        """Wait if we're hitting rate limits"""
        now = time.time()
        # Remove requests older than 1 second
        self.request_times = [t for t in self.request_times if now - t < 1.0]
        
        if len(self.request_times) >= self.max_requests_per_second:
            sleep_time = 1.0 - (now - self.request_times[0])
            if sleep_time > 0:
                time.sleep(sleep_time)
                self.request_times = []
        
        self.request_times.append(now)


class RailwayGraphQL:
    """Main client for Railway GraphQL API"""
    
    def __init__(self, config: Optional[RailwayConfig] = None):
        if config:
            self.config = config
        else:
            self.config = self._load_config()
        
        self.rate_limiter = RateLimitHandler(self.config.rate_limit_per_second)
        self._validate_config()
    
    def _load_config(self) -> RailwayConfig:
        """Load configuration from environment variables and Railway CLI"""
        # Try to get Railway token from various sources
        api_token = (
            os.getenv("RAILWAY_TOKEN") or
            os.getenv("RAILWAY_API_TOKEN") or
            self._get_railway_token_from_config()
        )
        
        if not api_token:
            raise ValueError(
                "Railway API token not found. Please set RAILWAY_TOKEN environment variable "
                "or run 'railway login' first."
            )
        
        project_id = os.getenv("RAILWAY_PROJECT_ID")
        environment_id = os.getenv("RAILWAY_ENVIRONMENT_ID")
        service_id = os.getenv("RAILWAY_SERVICE_ID")
        
        if not all([project_id, environment_id, service_id]):
            raise ValueError(
                "Missing Railway configuration. Ensure you're in a Railway project directory "
                "or set RAILWAY_PROJECT_ID, RAILWAY_ENVIRONMENT_ID, and RAILWAY_SERVICE_ID"
            )
        
        return RailwayConfig(
            api_token=api_token,
            project_id=project_id,
            environment_id=environment_id,
            service_id=service_id
        )
    
    def _get_railway_token_from_config(self) -> Optional[str]:
        """Try to get Railway token from CLI config file"""
        try:
            # Railway stores config in ~/.railway/config.json
            config_path = os.path.expanduser("~/.railway/config.json")
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config_data = json.load(f)
                    return config_data.get("token")
        except Exception:
            pass
        return None
    
    def _validate_config(self):
        """Validate configuration values"""
        if not self.config.api_token.startswith(('railway_', 'rlwy_')):
            print("Warning: API token doesn't appear to be a Railway token")
    
    def _make_request(self, query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Make a GraphQL request with rate limiting and error handling"""
        self.rate_limiter.wait_if_needed()
        
        headers = {
            'Authorization': f'Bearer {self.config.api_token}',
            'Content-Type': 'application/json',
        }
        
        payload = {
            'query': query,
            'variables': variables
        }
        
        for attempt in range(self.config.max_retries):
            try:
                response = requests.post(
                    self.config.api_endpoint,
                    json=payload,
                    headers=headers,
                    timeout=self.config.timeout
                )
                
                if response.status_code == 429:
                    # Rate limited - exponential backoff
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    print(f"Rate limited. Waiting {wait_time:.1f}s before retry...")
                    time.sleep(wait_time)
                    continue
                
                response.raise_for_status()
                data = response.json()
                
                if 'errors' in data:
                    raise Exception(f"GraphQL errors: {data['errors']}")
                
                return data
                
            except requests.exceptions.Timeout:
                if attempt == self.config.max_retries - 1:
                    raise
                print(f"Request timeout. Retrying in {2 ** attempt}s...")
                time.sleep(2 ** attempt)
            
            except requests.exceptions.RequestException as e:
                if attempt == self.config.max_retries - 1:
                    raise
                print(f"Request failed: {e}. Retrying in {2 ** attempt}s...")
                time.sleep(2 ** attempt)
        
        raise Exception(f"Failed after {self.config.max_retries} retries")
    
    def get_deployment_logs(
        self,
        deployment_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 200,
        log_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get deployment/runtime logs"""
        
        if not deployment_id:
            # Get the latest deployment ID
            deployment_id = self._get_latest_deployment_id()
        
        # Default to last hour if no time range specified
        if not start_date and not end_date:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(hours=1)
        
        query = """
        query GetDeploymentLogs($deploymentId: String!, $startDate: DateTime, $endDate: DateTime, $limit: Int, $filter: String) {
            deploymentLogs(
                deploymentId: $deploymentId,
                startDate: $startDate,
                endDate: $endDate,
                limit: $limit,
                filter: $filter
            ) {
                timestamp
                severity
                message
            }
        }
        """
        
        variables = {
            "deploymentId": deployment_id,
            "startDate": start_date.isoformat() + "Z" if start_date else None,
            "endDate": end_date.isoformat() + "Z" if end_date else None,
            "limit": limit,
            "filter": log_filter
        }
        
        response = self._make_request(query, variables)
        return response.get('data', {}).get('deploymentLogs', [])
    
    def get_build_logs(
        self,
        deployment_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 200,
        log_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get build logs for a deployment"""
        
        if not deployment_id:
            deployment_id = self._get_latest_deployment_id()
        
        query = """
        query GetBuildLogs($deploymentId: String!, $startDate: DateTime, $endDate: DateTime, $limit: Int, $filter: String) {
            buildLogs(
                deploymentId: $deploymentId,
                startDate: $startDate,
                endDate: $endDate,
                limit: $limit,
                filter: $filter
            ) {
                timestamp
                severity
                message
            }
        }
        """
        
        variables = {
            "deploymentId": deployment_id,
            "startDate": start_date.isoformat() + "Z" if start_date else None,
            "endDate": end_date.isoformat() + "Z" if end_date else None,
            "limit": limit,
            "filter": log_filter
        }
        
        response = self._make_request(query, variables)
        return response.get('data', {}).get('buildLogs', [])
    
    def get_http_logs(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 200,
        log_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get HTTP request logs"""
        
        # Default to last hour if no time range specified
        if not start_date and not end_date:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(hours=1)
        
        query = """
        query GetHttpLogs($projectId: String!, $environmentId: String!, $startDate: DateTime, $endDate: DateTime, $limit: Int, $filter: String) {
            httpLogs(
                projectId: $projectId,
                environmentId: $environmentId,
                startDate: $startDate,
                endDate: $endDate,
                limit: $limit,
                filter: $filter
            ) {
                timestamp
                message
                severity
            }
        }
        """
        
        variables = {
            "projectId": self.config.project_id,
            "environmentId": self.config.environment_id,
            "startDate": start_date.isoformat() + "Z" if start_date else None,
            "endDate": end_date.isoformat() + "Z" if end_date else None,
            "limit": limit,
            "filter": log_filter
        }
        
        response = self._make_request(query, variables)
        return response.get('data', {}).get('httpLogs', [])
    
    def _get_latest_deployment_id(self) -> str:
        """Get the ID of the latest deployment"""
        query = """
        query GetLatestDeployment($projectId: String!, $environmentId: String!) {
            project(id: $projectId) {
                environments(where: { id: $environmentId }) {
                    edges {
                        node {
                            deployments(orderBy: { createdAt: desc }, first: 1) {
                                edges {
                                    node {
                                        id
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        """
        
        variables = {
            "projectId": self.config.project_id,
            "environmentId": self.config.environment_id
        }
        
        response = self._make_request(query, variables)
        
        try:
            deployment = (
                response['data']['project']['environments']['edges'][0]['node']
                ['deployments']['edges'][0]['node']
            )
            return deployment['id']
        except (KeyError, IndexError):
            raise Exception("No deployments found for this environment")


if __name__ == "__main__":
    # Quick test/demo
    try:
        client = RailwayGraphQL()
        print("✅ Railway GraphQL client initialized successfully")
        print(f"Project: {client.config.project_id}")
        print(f"Environment: {client.config.environment_id}")
        print(f"Service: {client.config.service_id}")
    except Exception as e:
        print(f"❌ Failed to initialize Railway GraphQL client: {e}")
