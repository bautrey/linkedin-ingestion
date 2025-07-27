"""
Unit tests for ProfileController workflow integration

Tests Task 1.2: Verify create_profile() uses LinkedInWorkflow.process_profile()
instead of bypassing to cassidy_client.fetch_profile()
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from main import ProfileController, ProfileCreateRequest, normalize_linkedin_url
from app.cassidy.models import ProfileIngestionRequest
from app.cassidy.workflows import EnrichedProfile
from app.cassidy.models import LinkedInProfile


class TestProfileControllerWorkflowIntegration:
    """Test ProfileController workflow integration fixes"""
    
    @pytest.fixture
    def mock_db_client(self):
        """Mock database client"""
        db_client = Mock()
        db_client.get_profile_by_url = AsyncMock()
        db_client.get_profile_by_id = AsyncMock()
        db_client.store_profile = AsyncMock()
        return db_client
    
    @pytest.fixture
    def mock_cassidy_client(self):
        """Mock Cassidy client (should NOT be called in new workflow)"""
        cassidy_client = Mock()
        cassidy_client.fetch_profile = AsyncMock()
        return cassidy_client
    
    @pytest.fixture
    def mock_linkedin_workflow(self):
        """Mock LinkedIn workflow"""
        workflow = Mock()
        workflow.process_profile = AsyncMock()
        return workflow
    
    @pytest.fixture
    def profile_controller(self, mock_db_client, mock_cassidy_client, mock_linkedin_workflow):
        """ProfileController with mocked dependencies"""
        return ProfileController(mock_db_client, mock_cassidy_client, mock_linkedin_workflow)
    
    @pytest.fixture
    def sample_linkedin_profile(self):
        """Sample LinkedIn profile with complete data"""
        return LinkedInProfile(
            profile_id="test123",
            full_name="Test User",
            linkedin_url="https://www.linkedin.com/in/testuser/",
            headline="Test Position",
            about="Test about section",
            experiences=[
                {
                    "company": "Test Company",
                    "title": "Test Role",
                    "company_linkedin_url": "https://www.linkedin.com/company/testcompany/"
                }
            ],
            educations=[
                {
                    "school": "Test University",
                    "degree": "Test Degree"
                }
            ]
        )
    
    @pytest.fixture
    def sample_enriched_profile(self, sample_linkedin_profile):
        """Sample enriched profile with company data"""
        return EnrichedProfile(
            profile=sample_linkedin_profile,
            companies=[]  # Mock company data
        )

    @pytest.mark.asyncio
    async def test_create_profile_uses_workflow_not_direct_cassidy(
        self, 
        profile_controller, 
        mock_db_client, 
        mock_cassidy_client, 
        mock_linkedin_workflow,
        sample_enriched_profile
    ):
        """Test that create_profile() uses LinkedInWorkflow.process_profile() instead of direct Cassidy client"""
        
        # Setup - Use valid URL format that passes Pydantic validation
        request = ProfileCreateRequest(linkedin_url="https://linkedin.com/in/testuser")
        mock_db_client.get_profile_by_url.return_value = None  # No existing profile
        mock_linkedin_workflow.process_profile.return_value = ("request123", sample_enriched_profile)
        mock_db_client.store_profile.return_value = "stored_id_123"
        mock_db_client.get_profile_by_id.return_value = {
            "id": "stored_id_123",
            "url": "https://www.linkedin.com/in/testuser/",
            "name": "Test User",
            "position": "Test Position",
            "about": "Test about section",
            "experience": [{"company": "Test Company", "title": "Test Role"}],
            "education": [{"school": "Test University", "degree": "Test Degree"}],
            "certifications": [],
            "created_at": "2025-07-27T14:50:00Z"
        }
        
        # Execute
        result = await profile_controller.create_profile(request)
        
        # Verify workflow was called correctly
        mock_linkedin_workflow.process_profile.assert_called_once()
        workflow_call_args = mock_linkedin_workflow.process_profile.call_args[0][0]
        assert isinstance(workflow_call_args, ProfileIngestionRequest)
        # The workflow receives the original URL, not normalized (this is the actual behavior)
        assert str(workflow_call_args.linkedin_url) == "https://linkedin.com/in/testuser"
        assert workflow_call_args.include_companies is True  # Default should be True
        
        # Verify direct Cassidy client was NOT called
        mock_cassidy_client.fetch_profile.assert_not_called()
        
        # Verify profile was stored and returned
        mock_db_client.store_profile.assert_called_once_with(sample_enriched_profile.profile)
        assert result.id == "stored_id_123"

    @pytest.mark.asyncio 
    async def test_create_profile_url_normalization(
        self,
        profile_controller,
        mock_db_client,
        mock_linkedin_workflow,
        sample_enriched_profile
    ):
        """Test that LinkedIn URLs are normalized before database lookup"""
        
        # Test with URLs that pass Pydantic validation
        test_urls = [
            "https://linkedin.com/in/testuser", 
            "https://www.linkedin.com/in/testuser",
            "https://www.linkedin.com/in/testuser/"
        ]
        
        expected_normalized = "https://www.linkedin.com/in/testuser/"
        
        for test_url in test_urls:
            # Reset mocks
            mock_db_client.reset_mock()
            mock_linkedin_workflow.reset_mock()
            
            # Setup
            request = ProfileCreateRequest(linkedin_url=test_url)
            mock_db_client.get_profile_by_url.return_value = None
            mock_linkedin_workflow.process_profile.return_value = ("request123", sample_enriched_profile)
            mock_db_client.store_profile.return_value = "stored_id"
            mock_db_client.get_profile_by_id.return_value = {"id": "stored_id", "url": expected_normalized, "name": "Test", "created_at": "2025-07-27T14:50:00Z", "experience": [], "education": [], "certifications": []}
            
            # Execute
            await profile_controller.create_profile(request)
            
            # Verify normalized URL was used for lookup
            mock_db_client.get_profile_by_url.assert_called_once_with(expected_normalized)

    @pytest.mark.asyncio
    async def test_create_profile_duplicate_detection_with_normalization(
        self,
        profile_controller,
        mock_db_client,
        mock_linkedin_workflow,
        sample_enriched_profile
    ):
        """Test that duplicate detection works with URL normalization and updates existing profile"""
        
        # Setup - existing profile with normalized URL
        request = ProfileCreateRequest(linkedin_url="https://linkedin.com/in/testuser")  # Valid URL format
        existing_profile = {"id": "existing123", "url": "https://www.linkedin.com/in/testuser/"}
        mock_db_client.get_profile_by_url.return_value = existing_profile
        
        # Mock the delete operation and workflow
        from unittest.mock import AsyncMock
        mock_db_client.delete_profile = AsyncMock(return_value=True)
        mock_linkedin_workflow.process_profile.return_value = ("request123", sample_enriched_profile)
        mock_db_client.store_profile.return_value = "updated_id"
        mock_db_client.get_profile_by_id.return_value = {
            "id": "updated_id", 
            "url": "https://www.linkedin.com/in/testuser/", 
            "name": "Updated User", 
            "created_at": "2025-07-27T14:50:00Z", 
            "experience": [], 
            "education": [], 
            "certifications": []
        }
        
        # Execute - should update instead of throwing exception
        result = await profile_controller.create_profile(request)
        
        # Should detect duplicate with normalized URL
        mock_db_client.get_profile_by_url.assert_called_once_with("https://www.linkedin.com/in/testuser/")
        
        # Should delete existing profile and create new one (smart update)
        mock_db_client.delete_profile.assert_called_once_with("existing123")
        mock_linkedin_workflow.process_profile.assert_called_once()
        mock_db_client.store_profile.assert_called_once()
        
        # Should return updated profile
        assert result.id == "updated_id"
        assert result.name == "Updated User"

    def test_normalize_linkedin_url_function(self):
        """Test the normalize_linkedin_url utility function"""
        
        test_cases = [
            ("linkedin.com/in/user", "https://www.linkedin.com/in/user/"),
            ("https://linkedin.com/in/user", "https://www.linkedin.com/in/user/"), 
            ("https://www.linkedin.com/in/user", "https://www.linkedin.com/in/user/"),
            ("https://www.linkedin.com/in/user/", "https://www.linkedin.com/in/user/"),
            ("  https://linkedin.com/in/user  ", "https://www.linkedin.com/in/user/"),  # Whitespace
        ]
        
        for input_url, expected_output in test_cases:
            result = normalize_linkedin_url(input_url)
            assert result == expected_output, f"Failed for input: {input_url}"

    @pytest.mark.asyncio
    async def test_workflow_includes_companies_by_default(
        self,
        profile_controller,
        mock_db_client,
        mock_linkedin_workflow,
        sample_enriched_profile
    ):
        """Test that workflow is called with include_companies=True by default"""
        
        # Setup
        request = ProfileCreateRequest(linkedin_url="https://linkedin.com/in/testuser")
        mock_db_client.get_profile_by_url.return_value = None
        mock_linkedin_workflow.process_profile.return_value = ("request123", sample_enriched_profile)
        mock_db_client.store_profile.return_value = "stored_id"
        mock_db_client.get_profile_by_id.return_value = {"id": "stored_id", "url": "https://www.linkedin.com/in/testuser/", "name": "Test", "created_at": "2025-07-27T14:50:00Z", "experience": [], "education": [], "certifications": []}
        
        # Execute
        await profile_controller.create_profile(request)
        
        # Verify workflow was called with include_companies=True
        workflow_call_args = mock_linkedin_workflow.process_profile.call_args[0][0]
        assert workflow_call_args.include_companies is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
