#!/usr/bin/env python3
"""
Critical Production Workflow Test: Profile Creation

Tests the full LinkedIn profile creation workflow that takes 2-3 minutes:
1. Create profile via API
2. Wait for LinkedIn scraping to complete
3. Verify enriched data is populated
4. Verify profile is ready for scoring
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
@pytest.mark.timeout(300)  # 5 minute timeout
class TestProfileCreationWorkflow:
    """Critical production workflow: end-to-end profile creation."""

    @pytest.fixture
    def production_url(self) -> str:
        """Production URL for testing."""
        return "https://smooth-mailbox-production.up.railway.app"
    
    @pytest.fixture
    def api_headers(self) -> Dict[str, str]:
        """API headers for production requests."""
        return {"x-api-key": "li_HieZz-IjBp0uE7d-rZkRE0qyy12r5_ZJS_FR4jMvv0I"}

    async def test_full_profile_creation_workflow(self, production_url: str, api_headers: Dict[str, str]):
        """
        Test the complete profile creation workflow with real LinkedIn data.
        
        This test:
        - Creates a profile via POST /api/v1/profiles
        - Waits for LinkedIn scraping to complete (2-3 minutes)
        - Validates that enriched data is populated
        - Ensures profile is ready for scoring workflows
        """
        
        # Use a real LinkedIn profile for testing (public profile)
        test_linkedin_url = "https://www.linkedin.com/in/reidhoffman/"
        unique_suffix = str(uuid.uuid4())[:8]
        
        profile_request = {
            "linkedin_url": test_linkedin_url,
            "suggested_role": "CTO",
            "notes": f"Production workflow test {unique_suffix}"
        }
        
        async with httpx.AsyncClient(timeout=300.0) as client:
            print(f"\n🚀 Starting profile creation for: {test_linkedin_url}")
            
            # Step 1: Create profile
            create_response = await client.post(
                f"{production_url}/api/v1/profiles",
                json=profile_request,
                headers=api_headers
            )
            
            print(f"Profile creation response: {create_response.status_code}")
            assert create_response.status_code in [201, 202], f"Expected 201 or 202, got {create_response.status_code}"
            
            profile_data = create_response.json()
            profile_id = profile_data["id"]
            print(f"✅ Profile created with ID: {profile_id}")
            
            # Step 2: Wait for enrichment to complete
            print("⏱️  Waiting for LinkedIn scraping and enrichment...")
            max_wait_seconds = 180  # 3 minutes
            poll_interval = 10      # Check every 10 seconds
            
            for attempt in range(max_wait_seconds // poll_interval):
                await asyncio.sleep(poll_interval)
                
                # Check profile status
                status_response = await client.get(
                    f"{production_url}/api/v1/profiles/{profile_id}",
                    headers=api_headers
                )
                
                assert status_response.status_code == 200
                current_profile = status_response.json()
                
                print(f"⏳ Attempt {attempt + 1}: Status check...")
                
                # Check if enrichment is complete
                is_enriched = self._is_profile_enriched(current_profile)
                if is_enriched:
                    print("✅ Profile enrichment completed!")
                    break
                    
                if attempt >= (max_wait_seconds // poll_interval) - 1:
                    pytest.fail("❌ Profile enrichment did not complete within 3 minutes")
            
            # Step 3: Validate enriched data
            print("🔍 Validating enriched profile data...")
            
            final_response = await client.get(
                f"{production_url}/api/v1/profiles/{profile_id}",
                headers=api_headers
            )
            assert final_response.status_code == 200
            
            final_profile = final_response.json()
            self._validate_enriched_profile(final_profile, test_linkedin_url)
            
            print("✅ Profile creation workflow completed successfully!")
            
            # Cleanup: Delete test profile
            delete_response = await client.delete(
                f"{production_url}/api/v1/profiles/{profile_id}",
                headers=api_headers
            )
            print(f"🧹 Cleanup: Profile deleted (status: {delete_response.status_code})")

    def _is_profile_enriched(self, profile: Dict[str, Any]) -> bool:
        """Check if profile has been enriched with LinkedIn data."""
        # Profile is enriched if it has key LinkedIn data populated
        required_fields = ["name", "headline", "summary"]
        
        for field in required_fields:
            if not profile.get(field):
                return False
        
        # Check if experience or education data exists
        has_experience = bool(profile.get("experience", []))
        has_education = bool(profile.get("education", []))
        
        return has_experience or has_education
    
    def _validate_enriched_profile(self, profile: Dict[str, Any], expected_linkedin_url: str):
        """Validate that the profile has been properly enriched."""
        # Basic profile fields
        assert profile["linkedin_url"] == expected_linkedin_url
        assert profile["name"], "Profile name should be populated"
        assert profile["headline"], "Profile headline should be populated"
        
        # LinkedIn enrichment data
        assert profile.get("summary"), "Profile summary should be populated from LinkedIn"
        
        # Should have either experience or education
        has_experience = bool(profile.get("experience", []))
        has_education = bool(profile.get("education", []))
        assert has_experience or has_education, "Profile should have experience or education data"
        
        # Profile should be ready for scoring
        assert profile["id"], "Profile should have valid ID"
        assert profile.get("created_at"), "Profile should have creation timestamp"
        
        print(f"✅ Profile validation passed:")
        print(f"   - Name: {profile['name']}")
        print(f"   - Headline: {profile['headline']}")
        print(f"   - Has Experience: {has_experience}")
        print(f"   - Has Education: {has_education}")
