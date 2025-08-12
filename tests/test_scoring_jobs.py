"""
Tests for V1.85 LLM Scoring Job functionality

Tests cover ScoringJob model validation, database operations, and constraint handling.
"""

import pytest
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from typing import Dict, Any, Optional

import pytest_asyncio
from pydantic import ValidationError

# Import the models we'll create
from app.models.scoring import ScoringJob, ScoringRequest, ScoringResponse, JobStatus
from app.services.scoring_job_service import ScoringJobService


class TestScoringJobModel:
    """Test ScoringJob Pydantic model validation"""
    
    def test_scoring_job_valid_creation(self):
        """Test creating a valid ScoringJob instance"""
        job_data = {
            "id": str(uuid.uuid4()),
            "profile_id": str(uuid.uuid4()),
            "status": "pending",
            "prompt": "Evaluate this profile for CIO/CTO/CISO fit",
            "model_name": "gpt-3.5-turbo",
            "retry_count": 0,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        job = ScoringJob(**job_data)
        
        assert job.id == job_data["id"]
        assert job.profile_id == job_data["profile_id"]
        assert job.status == JobStatus.PENDING
        assert job.prompt == job_data["prompt"]
        assert job.model_name == job_data["model_name"]
        assert job.retry_count == 0
        assert job.llm_response is None
        assert job.parsed_score is None
        assert job.error_message is None
    
    def test_scoring_job_status_validation(self):
        """Test status field validation with enum"""
        job_data = {
            "id": str(uuid.uuid4()),
            "profile_id": str(uuid.uuid4()),
            "status": "invalid_status",
            "prompt": "Test prompt",
            "model_name": "gpt-3.5-turbo"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            ScoringJob(**job_data)
        
        assert "status" in str(exc_info.value)
    
    def test_scoring_job_required_fields(self):
        """Test that required fields are validated"""
        # Missing prompt
        with pytest.raises(ValidationError) as exc_info:
            ScoringJob(
                profile_id=str(uuid.uuid4()),
                status="pending",
                model_name="gpt-3.5-turbo"
            )
        
        assert "prompt" in str(exc_info.value)
    
    def test_scoring_job_defaults(self):
        """Test default values are set correctly"""
        job_data = {
            "profile_id": str(uuid.uuid4()),
            "prompt": "Test prompt"
        }
        
        job = ScoringJob(**job_data)
        
        assert job.status == JobStatus.PENDING
        assert job.model_name == "gpt-3.5-turbo"
        assert job.retry_count == 0
        assert job.id is not None  # Should be auto-generated
    
    def test_scoring_job_with_response_data(self):
        """Test ScoringJob with LLM response and parsed score"""
        llm_response = {"gatekeeper_result": "Pass", "total_score": 85}
        parsed_score = {"fit_verdict": "Strong Fit", "rationale": "Excellent background"}
        
        job = ScoringJob(
            profile_id=str(uuid.uuid4()),
            prompt="CTO evaluation",
            status="completed",
            llm_response=llm_response,
            parsed_score=parsed_score,
            completed_at=datetime.now(timezone.utc)
        )
        
        assert job.status == JobStatus.COMPLETED
        assert job.llm_response == llm_response
        assert job.parsed_score == parsed_score
        assert job.completed_at is not None
    
    def test_scoring_job_retry_count_validation(self):
        """Test retry count validation and limits"""
        # Valid retry count
        job = ScoringJob(
            profile_id=str(uuid.uuid4()),
            prompt="Test",
            retry_count=3
        )
        assert job.retry_count == 3
        
        # Max retry count validation (if we implement it)
        job_over_limit = ScoringJob(
            profile_id=str(uuid.uuid4()),
            prompt="Test",
            retry_count=10  # Should be valid at model level, business logic handles limits
        )
        assert job_over_limit.retry_count == 10


class TestScoringRequest:
    """Test ScoringRequest model for API requests"""
    
    def test_scoring_request_valid(self):
        """Test valid scoring request"""
        request_data = {
            "prompt": "Evaluate for executive role fit",
            "model": "gpt-4",
            "max_tokens": 2000,
            "temperature": 0.1
        }
        
        request = ScoringRequest(**request_data)
        
        assert request.prompt == request_data["prompt"]
        assert request.model == request_data["model"]
        assert request.max_tokens == request_data["max_tokens"]
        assert request.temperature == request_data["temperature"]
    
    def test_scoring_request_defaults(self):
        """Test default values for optional fields"""
        request = ScoringRequest(prompt="Test prompt")
        
        assert request.model == "gpt-3.5-turbo"
        assert request.max_tokens == 2000
        assert request.temperature == 0.1
    
    def test_scoring_request_empty_prompt(self):
        """Test that empty prompt is rejected"""
        with pytest.raises(ValidationError) as exc_info:
            ScoringRequest(prompt="")
        
        assert "prompt" in str(exc_info.value)
    
    def test_scoring_request_temperature_validation(self):
        """Test temperature range validation"""
        # Valid temperature
        request = ScoringRequest(prompt="Test", temperature=0.5)
        assert request.temperature == 0.5
        
        # Invalid temperature (outside 0-1 range)
        with pytest.raises(ValidationError):
            ScoringRequest(prompt="Test", temperature=1.5)
        
        with pytest.raises(ValidationError):
            ScoringRequest(prompt="Test", temperature=-0.1)


class TestScoringResponse:
    """Test ScoringResponse model for API responses"""
    
    def test_scoring_response_pending(self):
        """Test response for pending job"""
        response_data = {
            "job_id": str(uuid.uuid4()),
            "status": "pending",
            "profile_id": str(uuid.uuid4()),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        response = ScoringResponse(**response_data)
        
        assert response.job_id == response_data["job_id"]
        assert response.status == JobStatus.PENDING
        assert response.result is None
        assert response.error is None
    
    def test_scoring_response_completed(self):
        """Test response for completed job with results"""
        result_data = {
            "llm_response": {"total_score": 90},
            "parsed_score": {"fit_verdict": "Elite Fit"},
            "model_used": "gpt-4",
            "tokens_used": 1500
        }
        
        response_data = {
            "job_id": str(uuid.uuid4()),
            "status": "completed",
            "profile_id": str(uuid.uuid4()),
            "result": result_data,
            "created_at": datetime.now(timezone.utc),
            "completed_at": datetime.now(timezone.utc)
        }
        
        response = ScoringResponse(**response_data)
        
        assert response.status == JobStatus.COMPLETED
        # result_data gets parsed into ScoringResultData model, so check the fields
        assert response.result.llm_response == result_data["llm_response"]
        assert response.result.parsed_score == result_data["parsed_score"]
        assert response.result.model_used == result_data["model_used"]
        assert response.result.tokens_used == result_data["tokens_used"]
        assert response.completed_at is not None
    
    def test_scoring_response_failed(self):
        """Test response for failed job with error"""
        error_data = {
            "code": "openai_api_error",
            "message": "Rate limit exceeded",
            "retryable": True
        }
        
        response_data = {
            "job_id": str(uuid.uuid4()),
            "status": "failed",
            "profile_id": str(uuid.uuid4()),
            "error": error_data,
            "created_at": datetime.now(timezone.utc),
            "failed_at": datetime.now(timezone.utc)
        }
        
        response = ScoringResponse(**response_data)
        
        assert response.status == JobStatus.FAILED
        # error_data gets parsed into ScoringErrorData model, so check the fields
        assert response.error.code == error_data["code"]
        assert response.error.message == error_data["message"]
        assert response.error.retryable == error_data["retryable"]
        assert response.failed_at is not None


class TestScoringJobService:
    """Test ScoringJobService database operations"""
    
    @pytest_asyncio.fixture
    async def mock_supabase_client(self):
        """Mock Supabase client for testing"""
        mock_client = MagicMock()
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table
        return mock_client, mock_table
    
    @pytest_asyncio.fixture
    async def scoring_service(self, mock_supabase_client):
        """ScoringJobService with mocked client"""
        mock_client, mock_table = mock_supabase_client
        service = ScoringJobService()
        service.client = mock_client
        service._client_initialized = True
        return service, mock_table
    
    @pytest.mark.asyncio
    async def test_create_scoring_job(self, scoring_service):
        """Test creating a new scoring job"""
        service, mock_table = scoring_service
        
        # Mock successful insert
        mock_result = MagicMock()
        mock_result.data = [{"id": "job-123", "status": "pending"}]
        mock_table.insert.return_value.execute = AsyncMock(return_value=mock_result)
        
        profile_id = str(uuid.uuid4())
        prompt = "Evaluate CTO fit"
        
        job_id = await service.create_job(
            profile_id=profile_id,
            prompt=prompt,
            model_name="gpt-4"
        )
        
        # Verify Supabase call
        mock_table.insert.assert_called_once()
        insert_data = mock_table.insert.call_args[0][0]
        
        assert insert_data["profile_id"] == profile_id
        assert insert_data["prompt"] == prompt
        assert insert_data["model_name"] == "gpt-4"
        assert insert_data["status"] == "pending"
        assert "id" in insert_data
        
        # Verify return value
        assert job_id is not None
    
    @pytest.mark.asyncio
    async def test_get_scoring_job(self, scoring_service):
        """Test retrieving a scoring job by ID"""
        service, mock_table = scoring_service
        
        # Mock successful select
        job_data = {
            "id": "job-123",
            "profile_id": str(uuid.uuid4()),
            "status": "completed",
            "prompt": "Test prompt",
            "model_name": "gpt-3.5-turbo",
            "llm_response": {"score": 85},
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        mock_result = MagicMock()
        mock_result.data = [job_data]
        mock_table.select.return_value.eq.return_value.execute = AsyncMock(return_value=mock_result)
        
        job = await service.get_job("job-123")
        
        # Verify Supabase call
        mock_table.select.assert_called_once()
        mock_table.select.return_value.eq.assert_called_with("id", "job-123")
        
        # Verify returned job
        assert job is not None
        assert job.id == job_data["id"]
        assert job.status == JobStatus.COMPLETED
        assert job.llm_response == job_data["llm_response"]
    
    @pytest.mark.asyncio
    async def test_get_scoring_job_not_found(self, scoring_service):
        """Test retrieving non-existent job returns None"""
        service, mock_table = scoring_service
        
        # Mock empty result
        mock_result = MagicMock()
        mock_result.data = []
        mock_table.select.return_value.eq.return_value.execute = AsyncMock(return_value=mock_result)
        
        job = await service.get_job("nonexistent-job")
        
        assert job is None
    
    @pytest.mark.asyncio
    async def test_update_job_status(self, scoring_service):
        """Test updating job status"""
        service, mock_table = scoring_service
        
        # Mock successful update
        mock_result = MagicMock()
        mock_result.data = [{"id": "job-123", "status": "processing"}]
        mock_table.update.return_value.eq.return_value.execute = AsyncMock(return_value=mock_result)
        
        success = await service.update_job_status("job-123", JobStatus.PROCESSING)
        
        # Verify Supabase call
        mock_table.update.assert_called_once()
        update_data = mock_table.update.call_args[0][0]
        assert update_data["status"] == "processing"
        assert "updated_at" in update_data
        
        assert success is True
    
    @pytest.mark.asyncio
    async def test_update_job_with_result(self, scoring_service):
        """Test updating job with LLM response and completion"""
        service, mock_table = scoring_service
        
        # Mock successful update
        mock_result = MagicMock()
        mock_result.data = [{"id": "job-123", "status": "completed"}]
        mock_table.update.return_value.eq.return_value.execute = AsyncMock(return_value=mock_result)
        
        llm_response = {"total_score": 92, "fit_verdict": "Elite Fit"}
        parsed_score = {"score": 92, "category": "elite"}
        
        success = await service.complete_job(
            job_id="job-123",
            llm_response=llm_response,
            parsed_score=parsed_score
        )
        
        # Verify Supabase call
        mock_table.update.assert_called_once()
        update_data = mock_table.update.call_args[0][0]
        
        assert update_data["status"] == "completed"
        assert update_data["llm_response"] == llm_response
        assert update_data["parsed_score"] == parsed_score
        assert "completed_at" in update_data
        assert "updated_at" in update_data
        
        assert success is True
    
    @pytest.mark.asyncio
    async def test_fail_job_with_error(self, scoring_service):
        """Test marking job as failed with error message"""
        service, mock_table = scoring_service
        
        # Mock successful update
        mock_result = MagicMock()
        mock_result.data = [{"id": "job-123", "status": "failed"}]
        mock_table.update.return_value.eq.return_value.execute = AsyncMock(return_value=mock_result)
        
        error_message = "OpenAI API rate limit exceeded"
        
        success = await service.fail_job("job-123", error_message)
        
        # Verify Supabase call
        mock_table.update.assert_called_once()
        update_data = mock_table.update.call_args[0][0]
        
        assert update_data["status"] == "failed"
        assert update_data["error_message"] == error_message
        assert "updated_at" in update_data
        
        assert success is True
    
    @pytest.mark.asyncio
    async def test_increment_retry_count(self, scoring_service):
        """Test incrementing retry count for failed job"""
        service, mock_table = scoring_service
        
        # Mock the select operation to get current retry count
        mock_select_result = MagicMock()
        mock_select_result.data = [{"retry_count": 1}]
        mock_table.select.return_value.eq.return_value.execute = AsyncMock(return_value=mock_select_result)
        
        # Mock successful update
        mock_update_result = MagicMock()
        mock_update_result.data = [{"id": "job-123", "retry_count": 2}]
        mock_table.update.return_value.eq.return_value.execute = AsyncMock(return_value=mock_update_result)
        
        success = await service.increment_retry_count("job-123")
        
        # Verify Supabase calls - should first select then update
        assert mock_table.select.call_count == 1
        mock_table.update.assert_called_once()
        update_data = mock_table.update.call_args[0][0]
        
        assert update_data["retry_count"] == 2  # Incremented from 1 to 2
        assert update_data["status"] == "pending"
        assert update_data["error_message"] is None  # Should clear previous error
        assert "updated_at" in update_data
        
        assert success is True
    
    @pytest.mark.asyncio
    async def test_get_jobs_by_profile(self, scoring_service):
        """Test retrieving all jobs for a specific profile"""
        service, mock_table = scoring_service
        
        profile_id = str(uuid.uuid4())
        jobs_data = [
            {
                "id": "job-1",
                "profile_id": profile_id,
                "status": "completed",
                "prompt": "CTO evaluation",
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": "job-2", 
                "profile_id": profile_id,
                "status": "pending",
                "prompt": "CISO evaluation",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        ]
        
        mock_result = MagicMock()
        mock_result.data = jobs_data
        mock_table.select.return_value.eq.return_value.order.return_value.limit.return_value.execute = AsyncMock(return_value=mock_result)
        
        jobs = await service.get_jobs_by_profile(profile_id)
        
        # Verify Supabase call
        mock_table.select.assert_called_once()
        mock_table.select.return_value.eq.assert_called_with("profile_id", profile_id)
        
        # Verify results
        assert len(jobs) == 2
        assert jobs[0].id == "job-1"
        assert jobs[1].id == "job-2"
        assert all(job.profile_id == profile_id for job in jobs)
    
    @pytest.mark.asyncio
    async def test_database_constraint_violation(self, scoring_service):
        """Test handling of database constraint violations"""
        service, mock_table = scoring_service
        
        # Mock constraint violation (invalid profile_id reference)
        mock_table.insert.return_value.execute = AsyncMock(
            side_effect=Exception("Foreign key constraint violation")
        )
        
        with pytest.raises(Exception) as exc_info:
            await service.create_job(
                profile_id="nonexistent-profile",
                prompt="Test prompt"
            )
        
        assert "constraint violation" in str(exc_info.value).lower() or "foreign key" in str(exc_info.value).lower()


class TestJobStatus:
    """Test JobStatus enum"""
    
    def test_job_status_values(self):
        """Test all expected job status values"""
        assert JobStatus.PENDING == "pending"
        assert JobStatus.PROCESSING == "processing"
        assert JobStatus.COMPLETED == "completed"
        assert JobStatus.FAILED == "failed"
    
    def test_job_status_in_model(self):
        """Test JobStatus enum works in model validation"""
        # Valid status
        job = ScoringJob(
            profile_id=str(uuid.uuid4()),
            prompt="test",
            status=JobStatus.PROCESSING
        )
        assert job.status == JobStatus.PROCESSING
        
        # String status gets converted to enum
        job2 = ScoringJob(
            profile_id=str(uuid.uuid4()),
            prompt="test",
            status="completed"
        )
        assert job2.status == JobStatus.COMPLETED
