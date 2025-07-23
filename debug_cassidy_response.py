#!/usr/bin/env python3
"""
Debug Cassidy API Response Structure

This script makes a real API call and shows the actual response structure
to help us fix the Pydantic model validation issues.
"""

import asyncio
import json
import httpx
from app.core.config import settings
from app.core.logging import LoggerMixin


class CassidyResponseDebugger(LoggerMixin):
    """Debug the actual Cassidy API responses"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=settings.CASSIDY_TIMEOUT)
    
    async def debug_profile_response(self):
        """Get and analyze a real profile response"""
        print("=" * 60)
        print("DEBUGGING CASSIDY PROFILE API RESPONSE")
        print("=" * 60)
        
        linkedin_url = "https://www.linkedin.com/in/satyanadella/"
        payload = {"profile": linkedin_url}
        
        try:
            print(f"Sending request to: {settings.CASSIDY_PROFILE_WORKFLOW_URL}")
            print(f"Payload: {payload}")
            print()
            
            response = await self.client.post(
                settings.CASSIDY_PROFILE_WORKFLOW_URL,
                json=payload
            )
            
            print(f"Status Code: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            print()
            
            if response.status_code == 200:
                data = response.json()
                
                print("Raw Response Structure:")
                print(f"Keys: {list(data.keys())}")
                print()
                
                if 'workflowRun' in data:
                    workflow_run = data['workflowRun']
                    print(f"Workflow Status: {workflow_run.get('status')}")
                    
                    if 'actionResults' in workflow_run:
                        action_results = workflow_run['actionResults']
                        print(f"Action Results Count: {len(action_results)}")
                        
                        for i, action in enumerate(action_results):
                            print(f"Action {i+1}: {action.get('name')} - {action.get('status')}")
                            
                            if action.get('status') == 'SUCCESS' and 'output' in action:
                                output_value = action['output'].get('value')
                                if output_value:
                                    try:
                                        profile_data = json.loads(output_value)
                                        print()
                                        print("ACTUAL PROFILE DATA STRUCTURE:")
                                        print("=" * 40)
                                        print(f"Top-level keys: {list(profile_data.keys())}")
                                        print()
                                        
                                        # Show each field with type and sample value
                                        for key, value in profile_data.items():
                                            value_type = type(value).__name__
                                            if isinstance(value, str):
                                                sample = value[:50] + "..." if len(value) > 50 else value
                                            elif isinstance(value, list):
                                                sample = f"[{len(value)} items]"
                                            else:
                                                sample = str(value)[:50]
                                            
                                            print(f"  {key}: {value_type} = {sample}")
                                        
                                        print()
                                        print("Full Profile JSON (formatted):")
                                        print(json.dumps(profile_data, indent=2)[:2000] + "...")
                                        
                                    except json.JSONDecodeError as e:
                                        print(f"Error parsing profile JSON: {e}")
                                        print(f"Raw value: {output_value[:500]}...")
            else:
                print(f"Error: {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"Request failed: {e}")
    
    async def debug_company_response(self):
        """Get and analyze a real company response"""
        print("\n" + "=" * 60)
        print("DEBUGGING CASSIDY COMPANY API RESPONSE")
        print("=" * 60)
        
        company_url = "https://www.linkedin.com/company/microsoft/"
        payload = {"profile": company_url}
        
        try:
            print(f"Sending request to: {settings.CASSIDY_COMPANY_WORKFLOW_URL}")
            print(f"Payload: {payload}")
            print()
            
            response = await self.client.post(
                settings.CASSIDY_COMPANY_WORKFLOW_URL,
                json=payload
            )
            
            print(f"Status Code: {response.status_code}")
            print()
            
            if response.status_code == 200:
                data = response.json()
                
                if 'workflowRun' in data:
                    workflow_run = data['workflowRun']
                    print(f"Workflow Status: {workflow_run.get('status')}")
                    
                    if 'actionResults' in workflow_run:
                        action_results = workflow_run['actionResults']
                        
                        for i, action in enumerate(action_results):
                            print(f"Action {i+1}: {action.get('name')} - {action.get('status')}")
                            
                            if action.get('status') == 'SUCCESS' and 'output' in action:
                                output_value = action['output'].get('value')
                                if output_value:
                                    try:
                                        company_data = json.loads(output_value)  
                                        print()
                                        print("ACTUAL COMPANY DATA STRUCTURE:")
                                        print("=" * 40)
                                        print(f"Top-level keys: {list(company_data.keys())}")
                                        print()
                                        
                                        # Show each field with type and sample value
                                        for key, value in company_data.items():
                                            value_type = type(value).__name__
                                            if isinstance(value, str):
                                                sample = value[:50] + "..." if len(value) > 50 else value
                                            elif isinstance(value, list):
                                                sample = f"[{len(value)} items]"
                                            elif isinstance(value, dict):
                                                sample = f"{{dict with {len(value)} keys}}"
                                            else:
                                                sample = str(value)[:50]
                                            
                                            print(f"  {key}: {value_type} = {sample}")
                                        
                                        print()
                                        print("Full Company JSON (formatted):")
                                        print(json.dumps(company_data, indent=2)[:2000] + "...")
                                        
                                    except json.JSONDecodeError as e:
                                        print(f"Error parsing company JSON: {e}")
                                        print(f"Raw value: {output_value[:500]}...")
            else:
                print(f"Error: {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"Request failed: {e}")
    
    async def close(self):
        await self.client.aclose()


async def main():
    """Debug both profile and company API responses"""
    print("🔍 DEBUGGING ACTUAL CASSIDY API RESPONSES")
    print("This will help us fix the Pydantic model validation issues")
    print()
    
    debugger = CassidyResponseDebugger()
    
    try:
        await debugger.debug_profile_response()
        await debugger.debug_company_response()
        
        print("\n" + "=" * 80)
        print("🎯 DEBUGGING COMPLETE")
        print("=" * 80)
        print("Use the structure shown above to fix the Pydantic models in:")
        print("- app/cassidy/models.py")
        print()
        print("Key issues to fix:")
        print("1. Missing required fields in profile response")
        print("2. Type mismatches (strings vs integers)")
        print("3. Optional fields that should be required or vice versa")
        
    finally:
        await debugger.close()


if __name__ == "__main__":
    asyncio.run(main())
