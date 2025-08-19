"""
Unit tests for TemplateService

Tests all CRUD operations with mocked Supabase client following existing test patterns
"""

import pytest
import uuid
from unittest.mock import AsyncMock, Mock
from datetime import datetime, timezone
from typing import Dict, Any, List

from app.services.template_service import TemplateService
from app.models.template_models import (
    PromptTemplate,
    CreateTemplateRequest,
    UpdateTemplateRequest,
    TemplateSummary
)


class TestTemplateService:
    """Test suite for TemplateService CRUD operations"""

    @pytest.fixture
    def mock_supabase_client(self):
        """Mock Supabase client for testing"""
        client = AsyncMock()
        client._ensure_client = AsyncMock()
        client.client = Mock()
        return client

    @pytest.fixture
    def template_service(self, mock_supabase_client):
        """TemplateService instance with mocked Supabase client"""
        return TemplateService(mock_supabase_client)

    @pytest.fixture
    def sample_template_data(self) -> Dict[str, Any]:
        """Sample template data from database"""
        return {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "Senior Software Engineer CTO Evaluation",
            "category": "CTO",
            "prompt_text": "Evaluate candidate for CTO role focusing on technical leadership...",
            "description": "Comprehensive CTO evaluation template",
            "version": 2,
            "is_active": True,
            "metadata": {
                "focus_areas": ["Technical Leadership", "Team Management"],
                "scoring_criteria": {"technical_skills": 0.4, "leadership": 0.6}
            },
            "created_at": "2025-08-17T20:00:00Z",
            "updated_at": "2025-08-17T21:00:00Z"
        }

    @pytest.fixture
    def sample_create_request(self) -> CreateTemplateRequest:
        """Sample create template request"""
        return CreateTemplateRequest(
            name="New CTO Template",
            category="CTO",
            prompt_text="Evaluate technical leadership capabilities...",
            description="New template for CTO evaluation",
            is_active=True,
            metadata={"created_by": "test"}
        )

    @pytest.fixture  
    def sample_update_request(self) -> UpdateTemplateRequest:
        """Sample update template request"""
        return UpdateTemplateRequest(
            name="Updated CTO Template",
            description="Updated description",
            prompt_text="Updated prompt text...",
            is_active=True,
            metadata={"updated_by": "test"}
        )

    @pytest.mark.asyncio
    async def test_get_template_by_id_success(
        self, 
        template_service: TemplateService,
        mock_supabase_client: AsyncMock,
        sample_template_data: Dict[str, Any]
    ):
        """Test successful template retrieval by ID"""
        # Setup mock
        mock_table = Mock()
        mock_supabase_client.client.table.return_value = mock_table
        
        mock_result = Mock()
        mock_result.data = [sample_template_data]
        mock_table.select.return_value.eq.return_value.execute = AsyncMock(return_value=mock_result)

        # Execute
        template_id = sample_template_data["id"]
        result = await template_service.get_template_by_id(template_id)

        # Verify
        assert result is not None
        assert isinstance(result, PromptTemplate)
        assert str(result.id) == template_id
        assert result.name == sample_template_data["name"]
        assert result.category == sample_template_data["category"]
        assert result.version == sample_template_data["version"]
        
        # Verify Supabase calls
        mock_supabase_client.client.table.assert_called_once_with("prompt_templates")
        mock_table.select.assert_called_once_with("*")
        mock_table.select.return_value.eq.assert_called_once_with("id", template_id)

    @pytest.mark.asyncio
    async def test_get_template_by_id_not_found(
        self,
        template_service: TemplateService,
        mock_supabase_client: AsyncMock
    ):
        """Test template not found scenario"""
        # Setup mock
        mock_table = Mock()
        mock_supabase_client.client.table.return_value = mock_table
        
        mock_result = Mock()
        mock_result.data = []
        mock_table.select.return_value.eq.return_value.execute = AsyncMock(return_value=mock_result)

        # Execute
        result = await template_service.get_template_by_id("nonexistent-id")

        # Verify
        assert result is None

    @pytest.mark.asyncio
    async def test_list_templates_success(
        self,
        template_service: TemplateService,
        mock_supabase_client: AsyncMock,
        sample_template_data: Dict[str, Any]
    ):
        """Test successful template listing"""
        # Setup mock
        mock_table = Mock()
        mock_supabase_client.client.table.return_value = mock_table
        
        mock_result = Mock()
        mock_result.data = [sample_template_data]
        # Mock the chained query: select().eq().eq().limit().order().execute()
        mock_query = Mock()
        mock_table.select.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.order.return_value = mock_query
        mock_query.execute = AsyncMock(return_value=mock_result)

        # Execute
        result = await template_service.list_templates(
            category="CTO",
            include_inactive=False,
            limit=10
        )

        # Verify
        assert len(result) == 1
        assert isinstance(result[0], PromptTemplate)
        assert result[0].category == "CTO"
        
        # Verify Supabase calls
        mock_query.eq.assert_any_call("category", "CTO")
        mock_query.eq.assert_any_call("is_active", True)
        mock_query.limit.assert_called_once_with(10)
        mock_query.order.assert_called_once_with("created_at", desc=True)

    @pytest.mark.asyncio
    async def test_list_templates_no_filters(
        self,
        template_service: TemplateService,
        mock_supabase_client: AsyncMock,
        sample_template_data: Dict[str, Any]
    ):
        """Test template listing without filters"""
        # Setup mock
        mock_table = Mock()
        mock_supabase_client.client.table.return_value = mock_table
        
        mock_result = Mock()
        mock_result.data = [sample_template_data]
        # Mock the chained query: select().eq().order().execute()
        mock_query = Mock()
        mock_table.select.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.order.return_value = mock_query
        mock_query.execute = AsyncMock(return_value=mock_result)

        # Execute
        result = await template_service.list_templates()

        # Verify
        assert len(result) == 1
        # Should only filter by is_active=True by default
        mock_query.eq.assert_called_once_with("is_active", True)

    @pytest.mark.asyncio
    async def test_list_template_summaries_success(
        self,
        template_service: TemplateService,
        mock_supabase_client: AsyncMock,
        sample_template_data: Dict[str, Any]
    ):
        """Test successful template summaries listing"""
        # Setup mock
        mock_table = Mock()
        mock_supabase_client.client.table.return_value = mock_table
        
        # Remove prompt_text from summary data
        summary_data = {k: v for k, v in sample_template_data.items() if k != "prompt_text"}
        mock_result = Mock()
        mock_result.data = [summary_data]
        # Mock the chained query: select().eq().order().execute()
        mock_query = Mock()
        mock_table.select.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.order.return_value = mock_query
        mock_query.execute = AsyncMock(return_value=mock_result)

        # Execute
        result = await template_service.list_template_summaries(category="CTO")

        # Verify
        assert len(result) == 1
        assert isinstance(result[0], TemplateSummary)
        assert result[0].name == sample_template_data["name"]
        
        # Verify correct fields selected (no prompt_text)
        expected_fields = "id, name, category, description, version, is_active, created_at, updated_at, metadata"
        mock_table.select.assert_called_once_with(expected_fields)

    @pytest.mark.asyncio
    async def test_create_template_success(
        self,
        template_service: TemplateService,
        mock_supabase_client: AsyncMock,
        sample_create_request: CreateTemplateRequest,
        sample_template_data: Dict[str, Any]
    ):
        """Test successful template creation"""
        # Setup mock
        mock_table = Mock()
        mock_supabase_client.client.table.return_value = mock_table
        
        mock_result = Mock()
        mock_result.data = [sample_template_data]
        mock_table.insert.return_value.execute = AsyncMock(return_value=mock_result)

        # Execute
        result = await template_service.create_template(sample_create_request)

        # Verify
        assert result is not None
        assert isinstance(result, PromptTemplate)
        assert result.name == sample_template_data["name"]
        assert result.category == sample_template_data["category"]
        
        # Verify insert was called with correct data structure
        mock_table.insert.assert_called_once()
        insert_data = mock_table.insert.call_args[0][0]
        assert insert_data["name"] == sample_create_request.name
        assert insert_data["category"] == sample_create_request.category
        assert insert_data["version"] == 1  # New templates start at version 1
        assert "id" in insert_data
        assert "created_at" in insert_data
        assert "updated_at" in insert_data

    @pytest.mark.asyncio
    async def test_create_template_failure(
        self,
        template_service: TemplateService,
        mock_supabase_client: AsyncMock,
        sample_create_request: CreateTemplateRequest
    ):
        """Test template creation failure"""
        # Setup mock to return no data
        mock_table = Mock()
        mock_supabase_client.client.table.return_value = mock_table
        
        mock_result = Mock()
        mock_result.data = []  # No data returned
        mock_table.insert.return_value.execute = AsyncMock(return_value=mock_result)

        # Execute and verify exception
        with pytest.raises(ValueError, match="Template creation failed"):
            await template_service.create_template(sample_create_request)

    @pytest.mark.asyncio
    async def test_update_template_success(
        self,
        template_service: TemplateService,
        mock_supabase_client: AsyncMock,
        sample_update_request: UpdateTemplateRequest,
        sample_template_data: Dict[str, Any]
    ):
        """Test successful template update"""
        # Setup mock
        mock_table = Mock()
        mock_supabase_client.client.table.return_value = mock_table
        
        # Update sample data with new values
        updated_data = sample_template_data.copy()
        updated_data.update({
            "name": sample_update_request.name,
            "description": sample_update_request.description,
            "updated_at": "2025-08-17T22:00:00Z"
        })
        
        mock_result = Mock()
        mock_result.data = [updated_data]
        mock_table.update.return_value.eq.return_value.execute = AsyncMock(return_value=mock_result)

        # Execute
        template_id = sample_template_data["id"]
        result = await template_service.update_template(template_id, sample_update_request)

        # Verify
        assert result is not None
        assert isinstance(result, PromptTemplate)
        assert result.name == sample_update_request.name
        assert result.description == sample_update_request.description
        
        # Verify update was called correctly
        mock_table.update.assert_called_once()
        update_data = mock_table.update.call_args[0][0]
        assert update_data["name"] == sample_update_request.name
        assert update_data["description"] == sample_update_request.description
        assert "updated_at" in update_data
        mock_table.update.return_value.eq.assert_called_once_with("id", template_id)

    @pytest.mark.asyncio
    async def test_update_template_not_found(
        self,
        template_service: TemplateService,
        mock_supabase_client: AsyncMock,
        sample_update_request: UpdateTemplateRequest
    ):
        """Test template update when template not found"""
        # Setup mock to return no data
        mock_table = Mock()
        mock_supabase_client.client.table.return_value = mock_table
        
        mock_result = Mock()
        mock_result.data = []
        mock_table.update.return_value.eq.return_value.execute = AsyncMock(return_value=mock_result)

        # Execute
        result = await template_service.update_template("nonexistent-id", sample_update_request)

        # Verify
        assert result is None

    @pytest.mark.asyncio
    async def test_update_template_partial_update(
        self,
        template_service: TemplateService,
        mock_supabase_client: AsyncMock,
        sample_template_data: Dict[str, Any]
    ):
        """Test partial template update (only some fields)"""
        # Setup mock
        mock_table = Mock()
        mock_supabase_client.client.table.return_value = mock_table
        
        mock_result = Mock()
        mock_result.data = [sample_template_data]
        mock_table.update.return_value.eq.return_value.execute = AsyncMock(return_value=mock_result)

        # Create partial update request
        partial_request = UpdateTemplateRequest(name="New Name Only")

        # Execute
        template_id = sample_template_data["id"]
        result = await template_service.update_template(template_id, partial_request)

        # Verify
        assert result is not None
        
        # Verify only name and updated_at were in update data
        update_data = mock_table.update.call_args[0][0]
        assert update_data["name"] == "New Name Only"
        assert "updated_at" in update_data
        assert len(update_data) == 2  # Only name and updated_at

    @pytest.mark.asyncio
    async def test_delete_template_success(
        self,
        template_service: TemplateService,
        mock_supabase_client: AsyncMock,
        sample_template_data: Dict[str, Any]
    ):
        """Test successful template soft deletion"""
        # Setup mock
        mock_table = Mock()
        mock_supabase_client.client.table.return_value = mock_table
        
        mock_result = Mock()
        mock_result.data = [sample_template_data]
        mock_table.update.return_value.eq.return_value.execute = AsyncMock(return_value=mock_result)

        # Execute
        template_id = sample_template_data["id"]
        result = await template_service.delete_template(template_id)

        # Verify
        assert result is True
        
        # Verify soft delete (set is_active=False)
        update_data = mock_table.update.call_args[0][0]
        assert update_data["is_active"] is False
        assert "updated_at" in update_data
        mock_table.update.return_value.eq.assert_called_once_with("id", template_id)

    @pytest.mark.asyncio
    async def test_delete_template_not_found(
        self,
        template_service: TemplateService,
        mock_supabase_client: AsyncMock
    ):
        """Test template deletion when template not found"""
        # Setup mock to return no data
        mock_table = Mock()
        mock_supabase_client.client.table.return_value = mock_table
        
        mock_result = Mock()
        mock_result.data = []
        mock_table.update.return_value.eq.return_value.execute = AsyncMock(return_value=mock_result)

        # Execute
        result = await template_service.delete_template("nonexistent-id")

        # Verify
        assert result is False

    @pytest.mark.asyncio
    async def test_get_templates_by_category(
        self,
        template_service: TemplateService,
        mock_supabase_client: AsyncMock,
        sample_template_data: Dict[str, Any]
    ):
        """Test getting templates by category (convenience method)"""
        # Setup mock
        mock_table = Mock()
        mock_supabase_client.client.table.return_value = mock_table
        
        mock_result = Mock()
        mock_result.data = [sample_template_data]
        # Mock the chained query: select().eq().order().execute() 
        mock_query = Mock()
        mock_table.select.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.order.return_value = mock_query
        mock_query.execute = AsyncMock(return_value=mock_result)

        # Execute
        result = await template_service.get_templates_by_category("CTO")

        # Verify
        assert len(result) == 1
        assert result[0].category == "CTO"
        
        # Verify it calls list_templates with category filter
        mock_query.eq.assert_any_call("category", "CTO")
        mock_query.eq.assert_any_call("is_active", True)

    @pytest.mark.asyncio
    async def test_convert_db_to_model_datetime_conversion(
        self,
        template_service: TemplateService,
        sample_template_data: Dict[str, Any]
    ):
        """Test datetime conversion in _convert_db_to_model"""
        # Test with ISO string timestamps (as they come from database)
        db_data = sample_template_data.copy()
        
        # Execute conversion
        result = template_service._convert_db_to_model(db_data)

        # Verify
        assert isinstance(result, PromptTemplate)
        assert isinstance(result.created_at, datetime)
        assert isinstance(result.updated_at, datetime)
        assert result.created_at.tzinfo is not None  # Should have timezone info

    @pytest.mark.asyncio
    async def test_error_handling_supabase_exception(
        self,
        template_service: TemplateService,
        mock_supabase_client: AsyncMock
    ):
        """Test error handling when Supabase operations fail"""
        # Setup mock to raise exception
        mock_table = Mock()
        mock_supabase_client.client.table.return_value = mock_table
        mock_table.select.return_value.eq.return_value.execute = AsyncMock(side_effect=Exception("Database connection failed"))

        # Execute and verify exception is propagated
        with pytest.raises(Exception, match="Database connection failed"):
            await template_service.get_template_by_id("test-id")

    def test_convert_db_to_model_with_minimal_data(self, template_service: TemplateService):
        """Test model conversion with minimal required fields"""
        minimal_data = {
            "id": "550e8400-e29b-41d4-a716-446655440000",  # Use valid UUID format
            "name": "Test Template", 
            "category": "CTO",
            "prompt_text": "Test prompt",
            "version": 1,
            "is_active": True,
            "created_at": "2025-08-17T20:00:00Z",
            "updated_at": "2025-08-17T21:00:00Z"
        }

        result = template_service._convert_db_to_model(minimal_data)

        assert str(result.id) == "550e8400-e29b-41d4-a716-446655440000"
        assert result.name == "Test Template"
        assert result.description is None  # Optional field
        assert result.metadata == {}  # Default empty dict

    def test_convert_db_to_model_invalid_data(self, template_service: TemplateService):
        """Test model conversion with invalid data raises exception"""
        invalid_data = {"invalid": "data"}

        with pytest.raises(Exception):
            template_service._convert_db_to_model(invalid_data)
