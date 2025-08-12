"""
Tests for V1.85 LLM Scoring Service

Tests cover OpenAI integration, profile text conversion, prompt formatting,
response parsing, and job processing functionality.
"""

import pytest
import json
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

import pytest_asyncio
import openai

# Import the service and models
from app.services.llm_scoring_service import LLMScoringService
from app.models.canonical.profile import CanonicalProfile, CanonicalExperienceEntry, CanonicalEducationEntry
from app.models.scoring import JobStatus, ScoringJob


class TestLLMScoringServiceInit:
    """Test LLM service initialization"""
    
    def test_init_with_api_key(self):
        """Test service initialization with API key"""
        with patch('app.services.llm_scoring_service.AsyncOpenAI') as mock_openai:
            service = LLMScoringService(api_key="test-key")
            
            assert service.api_key == "test-key"
            assert service.client is not None
            assert service.default_model == "gpt-3.5-turbo"
            assert service.max_tokens == 2000
            assert service.temperature == 0.1
    
    def test_init_without_api_key(self):
        """Test service initialization without API key"""
        with patch('app.services.llm_scoring_service.settings') as mock_settings:
            mock_settings.OPENAI_API_KEY = None
            mock_settings.OPENAI_DEFAULT_MODEL = "gpt-3.5-turbo"
            mock_settings.OPENAI_MAX_TOKENS = 2000
            mock_settings.OPENAI_TEMPERATURE = 0.1
            
            service = LLMScoringService()
            
            assert service.api_key is None
            assert service.client is None
    
    def test_init_with_custom_settings(self):
        """Test initialization with custom configuration values"""
        with patch('app.services.llm_scoring_service.settings') as mock_settings:
            mock_settings.OPENAI_API_KEY = "settings-key"
            mock_settings.OPENAI_DEFAULT_MODEL = "gpt-4"
            mock_settings.OPENAI_MAX_TOKENS = 3000
            mock_settings.OPENAI_TEMPERATURE = 0.2
            
            with patch('app.services.llm_scoring_service.AsyncOpenAI'):
                service = LLMScoringService()
                
                assert service.default_model == "gpt-4"
                assert service.max_tokens == 3000
                assert service.temperature == 0.2


class TestTokenHandling:
    """Test token counting and text truncation"""
    
    @pytest.fixture
    def service(self):
        with patch('app.services.llm_scoring_service.AsyncOpenAI'):
            return LLMScoringService(api_key="test-key")
    
    def test_count_tokens_empty_text(self, service):
        """Test token counting with empty text"""
        assert service.count_tokens("") == 0
        assert service.count_tokens(None) == 0
    
    def test_count_tokens_simple_text(self, service):
        """Test token counting with simple text"""
        token_count = service.count_tokens("Hello world")
        assert token_count > 0
        assert isinstance(token_count, int)
    
    def test_truncate_text_no_truncation_needed(self, service):
        """Test text truncation when no truncation is needed"""
        text = "Short text"
        result = service.truncate_text(text, 1000)
        assert result == text
    
    def test_truncate_text_with_truncation(self, service):
        """Test text truncation when truncation is needed"""
        long_text = "word " * 1000  # Create long text
        max_tokens = 10
        
        result = service.truncate_text(long_text, max_tokens)
        
        assert len(result) < len(long_text)
        assert service.count_tokens(result) <= max_tokens
    
    def test_truncate_empty_text(self, service):
        """Test truncation with empty text"""
        assert service.truncate_text("", 100) == ""
        assert service.truncate_text(None, 100) == ""


class TestProfileToText:
    """Test profile serialization to text"""
    
    @pytest.fixture
    def service(self):
        with patch('app.services.llm_scoring_service.AsyncOpenAI'):
            return LLMScoringService(api_key="test-key")
    
    @pytest.fixture
    def sample_profile(self):
        """Create a sample CanonicalProfile for testing"""
        return CanonicalProfile(
            profile_id="test-123",
            full_name="John Doe",
            job_title="Senior Software Engineer",
            company="TechCorp Inc",
            city="San Francisco",
            country="USA",
            about="Experienced software engineer with 10+ years in web development",
            connection_count=500,
            follower_count=1000,
            experiences=[
                CanonicalExperienceEntry(
                    title="Senior Software Engineer",
                    company="TechCorp Inc",
                    duration="2020-Present",
                    description="Lead development of web applications"
                ),
                CanonicalExperienceEntry(
                    title="Software Engineer",
                    company="StartupCo",
                    duration="2018-2020",
                    description="Built scalable backend systems"
                )
            ],
            educations=[
                CanonicalEducationEntry(
                    degree="Bachelor of Science",
                    field_of_study="Computer Science",
                    school="Stanford University",
                    date_range="2014-2018"
                )
            ],
            linkedin_url="https://linkedin.com/in/johndoe",
            timestamp=datetime.now(timezone.utc)
        )
    
    def test_profile_to_text_complete_profile(self, service, sample_profile):
        """Test converting complete profile to text"""
        result = service.profile_to_text(sample_profile)
        
        # Verify basic info is included
        assert "Name: John Doe" in result
        assert "Current Title: Senior Software Engineer" in result
        assert "Current Company: TechCorp Inc" in result
        assert "Location: San Francisco, USA" in result
        assert "About: Experienced software engineer" in result
        
        # Verify experience section
        assert "Experience:" in result
        assert "TechCorp Inc" in result
        assert "StartupCo" in result
        
        # Verify education section
        assert "Education:" in result
        assert "Bachelor of Science" in result
        assert "Stanford University" in result
        
        # Verify metrics
        assert "Connections: 500" in result
        assert "Followers: 1000" in result
    
    def test_profile_to_text_minimal_profile(self, service):
        """Test converting minimal profile to text"""
        minimal_profile = CanonicalProfile(
            profile_id="test-456",
            full_name="Jane Smith",
            linkedin_url="https://linkedin.com/in/janesmith",
            timestamp=datetime.now(timezone.utc)
        )
        
        result = service.profile_to_text(minimal_profile)
        
        assert "Name: Jane Smith" in result
        assert "Experience:" not in result  # No experience section
        assert "Education:" not in result   # No education section
    
    def test_profile_to_text_truncation(self, service, sample_profile):
        """Test profile text truncation when too long"""
        # Mock a very long about section to trigger truncation
        sample_profile.about = "Very long description " * 1000
        
        with patch.object(service, 'max_input_tokens', 100):  # Force truncation
            result = service.profile_to_text(sample_profile)
            
            token_count = service.count_tokens(result)
            assert token_count <= 100


class TestPromptFormatting:
    """Test LLM prompt formatting"""
    
    @pytest.fixture
    def service(self):
        with patch('app.services.llm_scoring_service.AsyncOpenAI'):
            return LLMScoringService(api_key="test-key")
    
    def test_format_prompt_basic(self, service):
        """Test basic prompt formatting"""
        profile_text = "Name: John Doe\\nTitle: Engineer"
        user_prompt = "Evaluate for senior engineering role"
        
        result = service.format_prompt(profile_text, user_prompt)
        
        assert "expert recruiter and talent evaluator" in result
        assert profile_text in result
        assert user_prompt in result
        assert "JSON format" in result
    
    def test_format_prompt_structure(self, service):
        """Test that formatted prompt has correct structure"""
        profile_text = "Test profile"
        user_prompt = "Test evaluation"
        
        result = service.format_prompt(profile_text, user_prompt)
        
        # Check for key sections
        assert "PROFILE TO EVALUATE:" in result
        assert "EVALUATION REQUEST:" in result
        assert "Please provide your evaluation in JSON format:" in result


class TestResponseParsing:
    """Test LLM response parsing and validation"""
    
    @pytest.fixture
    def service(self):
        with patch('app.services.llm_scoring_service.AsyncOpenAI'):
            return LLMScoringService(api_key="test-key")
    
    def test_parse_valid_json_response(self, service):
        """Test parsing valid JSON response"""
        response_content = json.dumps({
            "score": 85,
            "fit_verdict": "Strong Fit",
            "rationale": "Excellent technical background"
        })
        
        result = service.parse_llm_response(response_content)
        
        assert result["score"] == 85
        assert result["fit_verdict"] == "Strong Fit"
        assert result["rationale"] == "Excellent technical background"
    
    def test_parse_empty_response(self, service):
        """Test parsing empty response"""
        with pytest.raises(ValueError, match="Empty response from LLM"):
            service.parse_llm_response("")
        
        with pytest.raises(ValueError, match="Empty response from LLM"):
            service.parse_llm_response("   ")
        
        with pytest.raises(ValueError, match="Empty response from LLM"):
            service.parse_llm_response(None)
    
    def test_parse_invalid_json(self, service):
        """Test parsing invalid JSON"""
        with pytest.raises(ValueError, match="Invalid JSON in LLM response"):
            service.parse_llm_response("This is not JSON")
        
        with pytest.raises(ValueError, match="Invalid JSON in LLM response"):
            service.parse_llm_response("{invalid json}")
    
    def test_parse_non_object_json(self, service):
        """Test parsing JSON that's not an object"""
        with pytest.raises(ValueError, match="LLM response is not a JSON object"):
            service.parse_llm_response('"just a string"')
        
        with pytest.raises(ValueError, match="LLM response is not a JSON object"):
            service.parse_llm_response('[1, 2, 3]')


class TestOpenAIAPIIntegration:
    """Test OpenAI API integration"""
    
    @pytest.fixture
    def service(self):
        with patch('app.services.llm_scoring_service.AsyncOpenAI'):
            return LLMScoringService(api_key="test-key")
    
    @pytest.fixture
    def mock_openai_response(self):
        """Mock successful OpenAI response"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "score": 90,
            "verdict": "Excellent fit"
        })
        mock_response.choices[0].finish_reason = "stop"
        mock_response.model = "gpt-3.5-turbo"
        mock_response.usage.prompt_tokens = 500
        mock_response.usage.completion_tokens = 100
        mock_response.usage.total_tokens = 600
        return mock_response
    
    @pytest.mark.asyncio
    async def test_call_openai_api_success(self, service, mock_openai_response):
        """Test successful OpenAI API call"""
        with patch.object(service.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_openai_response
            
            result = await service._call_openai_api("Test prompt")
            
            assert result["content"] == '{"score": 90, "verdict": "Excellent fit"}'
            assert result["model"] == "gpt-3.5-turbo"
            assert result["usage"]["total_tokens"] == 600
            assert result["finish_reason"] == "stop"
    
    @pytest.mark.asyncio
    async def test_call_openai_api_no_client(self):
        """Test API call without initialized client"""
        service = LLMScoringService()  # No API key
        
        with pytest.raises(ValueError, match="OpenAI client not initialized"):
            await service._call_openai_api("Test prompt")
    
    @pytest.mark.asyncio
    async def test_call_openai_api_auth_error(self, service):
        """Test handling of authentication errors"""
        with patch.object(service.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_create.side_effect = openai.AuthenticationError(
                "Invalid API key",
                response=mock_response,
                body={"error": "Invalid API key"}
            )
            
            with pytest.raises(ValueError, match="OpenAI authentication failed"):
                await service._call_openai_api("Test prompt")
    
    @pytest.mark.asyncio
    async def test_call_openai_api_bad_request(self, service):
        """Test handling of bad request errors"""
        with patch.object(service.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_create.side_effect = openai.BadRequestError(
                "Invalid model",
                response=mock_response,
                body={"error": "Invalid model"}
            )
            
            with pytest.raises(ValueError, match="Invalid request to OpenAI"):
                await service._call_openai_api("Test prompt")
    
    @pytest.mark.asyncio
    async def test_call_openai_api_rate_limit_retry(self, service, mock_openai_response):
        """Test retry logic for rate limit errors"""
        with patch.object(service.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            # First call fails with rate limit, second succeeds
            mock_response = MagicMock()
            mock_response.status_code = 429
            mock_create.side_effect = [
                openai.RateLimitError(
                    "Rate limit exceeded",
                    response=mock_response,
                    body={"error": "Rate limit exceeded"}
                ),
                mock_openai_response
            ]
            
            result = await service._call_openai_api("Test prompt")
            
            # Should succeed after retry
            assert result["content"] == '{"score": 90, "verdict": "Excellent fit"}'
            assert mock_create.call_count == 2


class TestProfileScoring:
    """Test profile scoring functionality"""
    
    @pytest.fixture
    def service(self):
        with patch('app.services.llm_scoring_service.AsyncOpenAI'):
            return LLMScoringService(api_key="test-key")
    
    @pytest.fixture
    def sample_profile(self):
        return CanonicalProfile(
            profile_id="test-123",
            full_name="John Doe",
            job_title="Software Engineer",
            company="TechCorp",
            linkedin_url="https://linkedin.com/in/johndoe",
            timestamp=datetime.now(timezone.utc)
        )
    
    @pytest.mark.asyncio
    async def test_score_profile_success(self, service, sample_profile):
        """Test successful profile scoring"""
        mock_response = {
            "content": json.dumps({"score": 85, "verdict": "Good fit"}),
            "model": "gpt-3.5-turbo",
            "usage": {"prompt_tokens": 400, "completion_tokens": 50, "total_tokens": 450},
            "finish_reason": "stop"
        }
        
        with patch.object(service, '_call_openai_api', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = mock_response
            
            raw_response, parsed_score = await service.score_profile(
                profile=sample_profile,
                prompt="Evaluate for software engineering role"
            )
            
            assert raw_response == mock_response
            assert parsed_score["score"] == 85
            assert parsed_score["verdict"] == "Good fit"
            assert "_metadata" in parsed_score
            assert parsed_score["_metadata"]["model_used"] == "gpt-3.5-turbo"
            assert parsed_score["_metadata"]["tokens_used"] == 450
    
    @pytest.mark.asyncio
    async def test_score_profile_no_profile(self, service):
        """Test scoring with no profile"""
        with pytest.raises(ValueError, match="Profile is required for scoring"):
            await service.score_profile(profile=None, prompt="Test prompt")
    
    @pytest.mark.asyncio
    async def test_score_profile_empty_prompt(self, service, sample_profile):
        """Test scoring with empty prompt"""
        with pytest.raises(ValueError, match="Evaluation prompt is required"):
            await service.score_profile(profile=sample_profile, prompt="")
        
        with pytest.raises(ValueError, match="Evaluation prompt is required"):
            await service.score_profile(profile=sample_profile, prompt="   ")
    
    @pytest.mark.asyncio
    async def test_score_profile_prompt_too_long(self, service, sample_profile):
        """Test scoring with prompt that's too long"""
        with patch.object(service, 'count_tokens', return_value=16000):
            with pytest.raises(ValueError, match="Prompt too long"):
                await service.score_profile(
                    profile=sample_profile,
                    prompt="Very long prompt"
                )


class TestJobProcessing:
    """Test async job processing"""
    
    @pytest.fixture
    def service(self):
        with patch('app.services.llm_scoring_service.AsyncOpenAI'):
            return LLMScoringService(api_key="test-key")
    
    @pytest.fixture
    def mock_job(self):
        return ScoringJob(
            id="job-123",
            profile_id="profile-456",
            status=JobStatus.PENDING,
            prompt="Evaluate for CTO role",
            model_name="gpt-4"
        )
    
    @pytest.mark.asyncio
    async def test_process_scoring_job_success(self, service, mock_job):
        """Test successful job processing"""
        sample_profile = CanonicalProfile(
            profile_id="profile-456",
            full_name="Jane Doe",
            job_title="VP Engineering",
            company="TechCorp",
            linkedin_url="https://linkedin.com/in/janedoe",
            timestamp=datetime.now(timezone.utc)
        )
        
        raw_response = {
            "content": json.dumps({"score": 92, "verdict": "Excellent CTO fit"}),
            "model": "gpt-4",
            "usage": {"total_tokens": 800},
            "finish_reason": "stop"
        }
        
        with patch.object(service.job_service, 'get_job', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_job
            
            with patch.object(service.job_service, 'update_job_status', new_callable=AsyncMock) as mock_update:
                with patch.object(service.job_service, 'complete_job', new_callable=AsyncMock) as mock_complete:
                    with patch.object(service, '_get_profile_by_id', new_callable=AsyncMock) as mock_get_profile:
                        mock_get_profile.return_value = sample_profile
                        
                        with patch.object(service, 'score_profile', new_callable=AsyncMock) as mock_score:
                            mock_score.return_value = (raw_response, {"score": 92})
                            
                            result = await service.process_scoring_job("job-123")
                            
                            assert result is True
                            mock_get.assert_called_once_with("job-123")
                            mock_update.assert_called_once()
                            mock_complete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_scoring_job_not_found(self, service):
        """Test processing job that doesn't exist"""
        with patch.object(service.job_service, 'get_job', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None
            
            result = await service.process_scoring_job("nonexistent-job")
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_process_scoring_job_not_pending(self, service, mock_job):
        """Test processing job that's not in pending status"""
        mock_job.status = JobStatus.COMPLETED
        
        with patch.object(service.job_service, 'get_job', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_job
            
            result = await service.process_scoring_job("job-123")
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_process_scoring_job_profile_not_found(self, service, mock_job):
        """Test processing job when profile doesn't exist"""
        with patch.object(service.job_service, 'get_job', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_job
            
            with patch.object(service.job_service, 'update_job_status', new_callable=AsyncMock):
                with patch.object(service.job_service, 'fail_job', new_callable=AsyncMock) as mock_fail:
                    with patch.object(service, '_get_profile_by_id', new_callable=AsyncMock) as mock_get_profile:
                        mock_get_profile.return_value = None
                        
                        result = await service.process_scoring_job("job-123")
                        
                        assert result is False
                        mock_fail.assert_called_once_with("job-123", "Profile not found: profile-456")
    
    @pytest.mark.asyncio
    async def test_process_scoring_job_scoring_error(self, service, mock_job):
        """Test processing job when scoring fails"""
        sample_profile = CanonicalProfile(
            profile_id="profile-456",
            full_name="Jane Doe",
            job_title="Engineer",
            company="TechCorp",
            linkedin_url="https://linkedin.com/in/janedoe",
            timestamp=datetime.now(timezone.utc)
        )
        
        with patch.object(service.job_service, 'get_job', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_job
            
            with patch.object(service.job_service, 'update_job_status', new_callable=AsyncMock):
                with patch.object(service.job_service, 'fail_job', new_callable=AsyncMock) as mock_fail:
                    with patch.object(service, '_get_profile_by_id', new_callable=AsyncMock) as mock_get_profile:
                        mock_get_profile.return_value = sample_profile
                        
                        with patch.object(service, 'score_profile', new_callable=AsyncMock) as mock_score:
                            mock_score.side_effect = ValueError("API error")
                            
                            result = await service.process_scoring_job("job-123")
                            
                            assert result is False
                            mock_fail.assert_called_once()
                            error_msg = mock_fail.call_args[0][1]
                            assert "ValueError: API error" in error_msg


class TestConfigurationIntegration:
    """Test integration with configuration settings"""
    
    @pytest.mark.asyncio
    async def test_service_uses_config_values(self):
        """Test that service correctly uses configuration values"""
        with patch('app.services.llm_scoring_service.settings') as mock_settings:
            mock_settings.OPENAI_API_KEY = "config-key"
            mock_settings.OPENAI_DEFAULT_MODEL = "gpt-4-turbo"
            mock_settings.OPENAI_MAX_TOKENS = 4000
            mock_settings.OPENAI_TEMPERATURE = 0.3
            
            with patch('app.services.llm_scoring_service.AsyncOpenAI'):
                service = LLMScoringService()
                
                assert service.api_key == "config-key"
                assert service.default_model == "gpt-4-turbo"
                assert service.max_tokens == 4000
                assert service.temperature == 0.3


class TestErrorHandling:
    """Test comprehensive error handling"""
    
    @pytest.fixture
    def service(self):
        with patch('app.services.llm_scoring_service.AsyncOpenAI'):
            return LLMScoringService(api_key="test-key")
    
    @pytest.mark.asyncio
    async def test_network_error_handling(self, service):
        """Test handling of network errors"""
        with patch.object(service.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = Exception("Network error")
            
            with pytest.raises(Exception, match="Network error"):
                await service._call_openai_api("Test prompt")
    
    def test_malformed_profile_handling(self, service):
        """Test handling of malformed profile data"""
        # Create profile with missing required fields
        incomplete_profile = CanonicalProfile(
            profile_id=None,  # Missing required field
            linkedin_url="https://linkedin.com/in/test",
            timestamp=datetime.now(timezone.utc)
        )
        
        # Should not crash, should handle gracefully
        result = service.profile_to_text(incomplete_profile)
        assert isinstance(result, str)
    
    def test_token_counting_edge_cases(self, service):
        """Test token counting with edge cases"""
        # Test with special characters
        special_text = "🚀 ñáéíóú 中文 العربية"
        count = service.count_tokens(special_text)
        assert count > 0
        
        # Test with very long text
        long_text = "a" * 100000
        count = service.count_tokens(long_text)
        assert count > 0
