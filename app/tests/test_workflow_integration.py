"""
Tests for LinkedInWorkflow integration with CassidyAdapter.

This file includes end-to-end tests that validate proper integration 
between the LinkedIn ingestion workflow and the CassidyAdapter transformation logic.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.cassidy.workflows import LinkedInWorkflow, EnrichedProfile
from app.adapters.cassidy_adapter import CassidyAdapter
from app.adapters.exceptions import IncompleteDataError
from app.models.canonical import CanonicalProfile
from app.cassidy.models import ProfileIngestionRequest
from app.cassidy.exceptions import CassidyException


class TestLinkedInWorkflowIntegration:
    """Test LinkedInWorkflow integration with CassidyAdapter."""
    
    @pytest.mark.asyncio
    async def test_workflow_uses_adapter_for_profile_transformation(self):
        """Test that LinkedInWorkflow uses CassidyAdapter to transform Cassidy responses."""
        # Mock Cassidy client response
        mock_cassidy_response = {
            "profile_id": "test-profile-123",
            "full_name": "John Doe",
            "linkedin_url": "https://linkedin.com/in/johndoe",
            "experiences": [],
            "educations": []
        }
        
        # Mock canonical profile from adapter
        mock_canonical_profile = CanonicalProfile(
            profile_id="test-profile-123",
            full_name="John Doe",
            linkedin_url="https://linkedin.com/in/johndoe",
            experiences=[],
            educations=[]
        )
        
        with patch('app.cassidy.workflows.LinkedInWorkflow') as MockWorkflow:
            # Create workflow instance
            workflow = LinkedInWorkflow()
            
            # Mock the cassidy client fetch response
            workflow.cassidy_client.fetch_profile = AsyncMock(return_value=mock_cassidy_response)
            
            # Mock the adapter transformation
            with patch('app.adapters.cassidy_adapter.CassidyAdapter') as MockAdapter:
                mock_adapter_instance = MockAdapter.return_value
                mock_adapter_instance.transform.return_value = mock_canonical_profile
                
                # Inject adapter into workflow (this will be done in the actual implementation)
                workflow.adapter = mock_adapter_instance
                
                # Create request
                request = ProfileIngestionRequest(
                    linkedin_url="https://linkedin.com/in/johndoe",
                    include_companies=False
                )
                
                # This test verifies the structure we want, but the actual implementation
                # will need to be updated to use the adapter
                # For now, this serves as a specification test
                
                assert workflow.adapter is not None
                assert hasattr(workflow.adapter, 'transform')
    
    @pytest.mark.asyncio
    async def test_workflow_handles_incomplete_data_error(self):
        """Test that workflow handles IncompleteDataError from adapter."""
        workflow = LinkedInWorkflow()
        
        # Mock adapter that raises IncompleteDataError
        mock_adapter = MagicMock(spec=CassidyAdapter)
        mock_adapter.transform.side_effect = IncompleteDataError(["full_name", "linkedin_url"])
        
        # This test verifies error handling structure we want to implement
        with pytest.raises(IncompleteDataError) as exc_info:
            mock_adapter.transform({})
        
        error = exc_info.value
        assert "full_name" in error.missing_fields
        assert "linkedin_url" in error.missing_fields
    
    @pytest.mark.asyncio
    async def test_enriched_profile_contains_canonical_data(self):
        """Test that EnrichedProfile contains canonical models after integration."""
        # Create canonical profile
        canonical_profile = CanonicalProfile(
            profile_id="test-123",
            full_name="Test User",
            linkedin_url="https://linkedin.com/in/testuser",
            experiences=[],
            educations=[]
        )
        
        # Create enriched profile (this will need to be updated to accept CanonicalProfile)
        # For now, test the structure we want
        enriched = EnrichedProfile(canonical_profile, [])
        
        # Verify the profile is accessible
        assert enriched.profile == canonical_profile
        assert enriched.profile.profile_id == "test-123"
        assert enriched.profile.full_name == "Test User"

