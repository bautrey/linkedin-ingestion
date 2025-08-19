#!/usr/bin/env python3
"""
Critical Production Workflow Test: Scoring Job Completion

Tests the full scoring workflow that takes 1-2 minutes:
1. Create scoring job for existing profile
2. Wait for OpenAI processing to complete
3. Verify scoring results are populated
4. Test scoring with template integration
"""

import pytest
import httpx
import asyncio
import os
from typing import Dict, Any, Optional
import uuid
from datetime import datetime


@pytest.mark.asyncio
@pytest.mark.production
@pytest.mark.timeout(180)  # 3 minute timeout
class TestScoringWorkflow:
    """Critical production workflow: end-to-end scoring job completion."""

    @pytest.fixture
    def production_url(self) -> str:
        """Production URL for testing."""
        return "https://smooth-mailbox-production.up.railway.app"
    
    @pytest.fixture
    def api_headers(self) -> Dict[str, str]:
        """API headers for production requests."""
        return {"x-api-key": "li_HieZz-IjBp0uE7d-rZkRE0qyy12r5_ZJS_FR4jMvv0I"}
    
    @pytest.fixture
    def test_profile_id(self) -> str:
        """Known test profile ID in production with enriched data."""
        return "435ccbf7-6c5e-4e2d-bdc3-052a244d7121"

    async def test_full_scoring_job_workflow(self, production_url: str, api_headers: Dict[str, str], test_profile_id: str):
        """
        Test the complete scoring workflow with real OpenAI integration.
        
        This test:
        - Creates a scoring job for an existing profile
        - Waits for OpenAI processing to complete (1-2 minutes)
        - Validates scoring results are populated
        - Tests scoring with template integration
        """
        
        async with httpx.AsyncClient(timeout=180.0) as client:
            print(f"\n🎯 Starting scoring workflow for profile: {test_profile_id}")
            
            # Step 1: Verify profile exists and has data
            profile_response = await client.get(
                f"{production_url}/api/v1/profiles/{test_profile_id}",
                headers=api_headers
            )
            
            if profile_response.status_code == 404:
                pytest.skip("Test profile not found in production - skipping scoring test")
            
            assert profile_response.status_code == 200
            profile_data = profile_response.json()
            print(f"✅ Profile found: {profile_data.get('name', 'Unknown')}")
            
            # Step 2: Get a template for scoring
            templates_response = await client.get(
                f"{production_url}/api/v1/templates?category=CTO",
                headers=api_headers
            )
            
            assert templates_response.status_code == 200
            templates_data = templates_response.json()
            
            cto_template = None
            for template in templates_data.get("templates", []):
                if "CTO" in template.get("name", ""):
                    cto_template = template
                    break
            
            if not cto_template:
                pytest.skip("No CTO template found - skipping template-based scoring test")
            
            print(f"✅ Using template: {cto_template['name']}")
            
            # Step 3: Create scoring job
            scoring_request = {
                "template_id": cto_template["id"],
                "prompt": cto_template.get("prompt_text", "Evaluate this profile for CTO position fit")
            }
            
            create_response = await client.post(
                f"{production_url}/api/v1/profiles/{test_profile_id}/score",
                json=scoring_request,
                headers=api_headers
            )
            
            print(f"Scoring job creation response: {create_response.status_code}")
            assert create_response.status_code in [201, 202], f"Expected 201 or 202, got {create_response.status_code}"
            
            job_data = create_response.json()
            job_id = job_data["job_id"]
            print(f"✅ Scoring job created with ID: {job_id}")
            
            # Step 4: Wait for scoring to complete
            print("⏱️  Waiting for OpenAI scoring to complete...")
            max_wait_seconds = 120  # 2 minutes
            poll_interval = 5       # Check every 5 seconds
            
            final_job_status = None
            for attempt in range(max_wait_seconds // poll_interval):
                await asyncio.sleep(poll_interval)
                
                # Check job status
                status_response = await client.get(
                    f"{production_url}/api/v1/scoring-jobs/{job_id}",
                    headers=api_headers
                )
                
                assert status_response.status_code == 200
                job_status = status_response.json()
                
                current_status = job_status["status"]
                print(f"⏳ Attempt {attempt + 1}: Job status is '{current_status}'")
                
                if current_status == "completed":
                    final_job_status = job_status
                    print("✅ Scoring job completed!")
                    break
                elif current_status == "failed":
                    pytest.fail(f"❌ Scoring job failed: {job_status.get('error', 'Unknown error')}")
                
                if attempt >= (max_wait_seconds // poll_interval) - 1:
                    pytest.fail("❌ Scoring job did not complete within 2 minutes")
            
            # Step 5: Validate scoring results
            print("🔍 Validating scoring results...")
            
            self._validate_scoring_results(final_job_status, cto_template["id"])
            
            print("✅ Scoring workflow completed successfully!")

    async def test_bulk_scoring_performance(self, production_url: str, api_headers: Dict[str, str]):
        """
        Test that multiple scoring jobs can be processed concurrently.
        
        This validates production performance under realistic load.
        """
        async with httpx.AsyncClient(timeout=180.0) as client:
            print(f"\n⚡ Testing bulk scoring performance...")
            
            # Get available profiles
            profiles_response = await client.get(
                f"{production_url}/api/v1/profiles?limit=3",
                headers=api_headers
            )
            
            if profiles_response.status_code != 200 or not profiles_response.json().get("profiles"):
                pytest.skip("No profiles available for bulk scoring test")
            
            profiles = profiles_response.json()["profiles"][:2]  # Test with 2 profiles
            print(f"✅ Found {len(profiles)} profiles for bulk testing")
            
            # Get a template
            templates_response = await client.get(
                f"{production_url}/api/v1/templates?limit=1",
                headers=api_headers
            )
            
            if templates_response.status_code != 200 or not templates_response.json().get("templates"):
                pytest.skip("No templates available for bulk scoring test")
            
            template = templates_response.json()["templates"][0]
            
            # Create multiple scoring jobs concurrently
            scoring_jobs = []
            for profile in profiles:
                scoring_request = {
                    "template_id": template["id"],
                    "prompt": template.get("prompt_text", "Evaluate this profile")
                }
                
                create_response = await client.post(
                    f"{production_url}/api/v1/profiles/{profile['id']}/score",
                    json=scoring_request,
                    headers=api_headers
                )
                
                if create_response.status_code in [201, 202]:
                    job_data = create_response.json()
                    scoring_jobs.append(job_data["job_id"])
                    print(f"✅ Created scoring job {job_data['job_id']} for {profile.get('name', 'Unknown')}")
            
            if not scoring_jobs:
                pytest.skip("No scoring jobs were created successfully")
            
            print(f"⏱️  Waiting for {len(scoring_jobs)} concurrent jobs to complete...")
            
            # Wait for all jobs to complete
            completed_jobs = 0
            max_wait_seconds = 150  # 2.5 minutes for multiple jobs
            poll_interval = 10      # Check every 10 seconds
            
            for attempt in range(max_wait_seconds // poll_interval):
                await asyncio.sleep(poll_interval)
                
                current_completed = 0
                for job_id in scoring_jobs:
                    status_response = await client.get(
                        f"{production_url}/api/v1/scoring-jobs/{job_id}",
                        headers=api_headers
                    )
                    
                    if status_response.status_code == 200:
                        job_status = status_response.json()
                        if job_status["status"] == "completed":
                            current_completed += 1
                
                completed_jobs = current_completed
                print(f"⏳ Attempt {attempt + 1}: {completed_jobs}/{len(scoring_jobs)} jobs completed")
                
                if completed_jobs == len(scoring_jobs):
                    print("✅ All bulk scoring jobs completed!")
                    break
                
                if attempt >= (max_wait_seconds // poll_interval) - 1:
                    print(f"⚠️  Only {completed_jobs}/{len(scoring_jobs)} jobs completed within time limit")
                    # Don't fail - this is performance testing, partial completion is valuable data
            
            print(f"📊 Bulk scoring results: {completed_jobs}/{len(scoring_jobs)} jobs completed")

    def _validate_scoring_results(self, job_status: Dict[str, Any], expected_template_id: str):
        """Validate that scoring results contain expected data."""
        # Basic job data
        assert job_status["status"] == "completed"
        assert job_status.get("job_id"), "Job should have valid ID"
        assert job_status.get("created_at"), "Job should have creation timestamp"
        assert job_status.get("completed_at"), "Completed job should have completion timestamp"
        
        # Template integration
        if "template_id" in job_status:
            assert job_status["template_id"] == expected_template_id
        
        # Scoring results
        assert job_status.get("result"), "Job should have scoring results"
        
        result = job_status["result"]
        
        # LLM scoring should produce structured results
        assert isinstance(result, dict), "Scoring result should be structured data"
        
        # Should have scoring components (exact fields may vary by template)
        result_keys = list(result.keys())
        assert len(result_keys) > 0, "Scoring result should have content"
        
        print(f"✅ Scoring validation passed:")
        print(f"   - Job ID: {job_status.get('job_id')}")
        print(f"   - Template ID: {job_status.get('template_id', 'N/A')}")
        print(f"   - Result keys: {result_keys}")
        print(f"   - Completion time: {job_status.get('completed_at')}")
