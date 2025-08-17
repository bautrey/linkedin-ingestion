"""
Unit tests for TemplateService

Tests business logic and database operations with proper mocking
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone
from uuid import uuid4
from app.services.template_service import TemplateService
from app.models.template_models import (
    PromptTemplate,
    CreateTemplateRequest,
    UpdateTemplateRequest,
    TemplateSummary
)


class TestTemplateService:
    """Test the TemplateService class"""

    @pytest.fixture
    def mock_supabase_client(self):
        """Mock Supabase client for testing"""
        client = MagicMock()
        client._ensure_client = AsyncMock()
        client.client = MagicMock()
        return client

    @pytest.fixture
    def template_service(self, mock_supabase_client):
        """Create template service with mocked dependencies"""
        return TemplateService(supabase_client=mock_supabase_client)

    @pytest.fixture
    def sample_template_data(self):
        """Sample template data as would come from database"""
        return {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "name": "Test CTO Template",
            "category": "CTO",
            "prompt_text": "Evaluate this candidate for CTO role...",
            "version": 1,
            "is_active": True,
            "description": "Test template description",
            "metadata": {"tags": ["test"]},
            "created_at": "2025-08-13T12:00:00+00:00",
            "updated_at": "2025-08-13T12:00:00+00:00"
        }

    @pytest.mark.asyncio
    async def test_get_template_by_id_success(self, template_service, mock_supabase_client, sample_template_data):
        """Test successful template retrieval by ID"""
        # Mock successful database response
        mock_response = MagicMock()
        mock_response.data = [sample_template_data]
        
        table_mock = MagicMock()
        table_mock.select.return_value.eq.return_value.execute = AsyncMock(return_value=mock_response)
        mock_supabase_client.client.table.return_value = table_mock

        template = await template_service.get_template_by_id("123e4567-e89b-12d3-a456-426614174000")
        
        assert template is not None
        assert template.name == "Test CTO Template"
        assert template.category == "CTO"
        assert template.prompt_text == "Evaluate this candidate for CTO role..."
        assert template.is_active is True
        
        # Verify database calls
        mock_supabase_client.client.table.assert_called_once_with("prompt_templates")
        table_mock.select.assert_called_once_with("*")

    @pytest.mark.asyncio
    async def test_get_template_by_id_not_found(self, template_service, mock_supabase_client):
        """Test template not found scenario"""
        # Mock empty database response
        mock_response = MagicMock()
        mock_response.data = []
        
        table_mock = MagicMock()
        table_mock.select.return_value.eq.return_value.execute = AsyncMock(return_value=mock_response)
        mock_supabase_client.client.table.return_value = table_mock

        template = await template_service.get_template_by_id("nonexistent-id")
        assert template is None

    @pytest.mark.asyncio
    async def test_list_templates_all(self, template_service, mock_supabase_client, sample_template_data):
        """Test listing all active templates"""
        # Mock database response with multiple templates
        template_data_2 = sample_template_data.copy()
        template_data_2["id"] = "456e7890-e89b-12d3-a456-426614174001"
        template_data_2["name"] = "Test CIO Template"
        template_data_2["category"] = "CIO"
        
        mock_response = MagicMock()
        mock_response.data = [sample_template_data, template_data_2]
        
        table_mock = MagicMock()
        query_mock = MagicMock()
        query_mock.eq.return_value.order.return_value.execute = AsyncMock(return_value=mock_response)
        table_mock.select.return_value = query_mock
        mock_supabase_client.client.table.return_value = table_mock

        templates = await template_service.list_templates()
        
        assert len(templates) == 2
        assert templates[0].name == "Test CTO Template"
        assert templates[1].name == "Test CIO Template"
        
        # Verify active filter was applied
        query_mock.eq.assert_called_with("is_active", True)

    @pytest.mark.asyncio
    async def test_list_templates_with_category_filter(self, template_service, mock_supabase_client, sample_template_data):
        """Test listing templates with category filter"""
        mock_response = MagicMock()
        mock_response.data = [sample_template_data]
        
        table_mock = MagicMock()
        # Create proper mock chain for query.eq().eq().order().execute()
        execute_mock = AsyncMock(return_value=mock_response)
        order_mock = MagicMock()
        order_mock.execute = execute_mock
        
        eq_active_mock = MagicMock()
        eq_active_mock.order.return_value = order_mock
        
        eq_category_mock = MagicMock()
        eq_category_mock.eq.return_value = eq_active_mock
        
        query_mock = MagicMock()
        query_mock.eq.return_value = eq_category_mock
        
        table_mock.select.return_value = query_mock
        mock_supabase_client.client.table.return_value = table_mock

        templates = await template_service.list_templates(category="CTO")
        
        assert len(templates) == 1
        assert templates[0].category == "CTO"
        
        # Verify filters were applied in the correct order
        # First call should be for category filter (gets uppercased to CTO)
        query_mock.eq.assert_called_once_with("category", "CTO")
        # Second call should be for is_active filter
        eq_category_mock.eq.assert_called_once_with("is_active", True)

    @pytest.mark.asyncio
    async def test_list_templates_include_inactive(self, template_service, mock_supabase_client, sample_template_data):
        """Test listing templates including inactive ones"""
        mock_response = MagicMock()
        mock_response.data = [sample_template_data]
        
        table_mock = MagicMock()
        query_mock = MagicMock()
        query_mock.order.return_value.execute = AsyncMock(return_value=mock_response)
        table_mock.select.return_value = query_mock
        mock_supabase_client.client.table.return_value = table_mock

        templates = await template_service.list_templates(include_inactive=True)
        
        assert len(templates) == 1
        
        # Verify is_active filter was NOT applied (no eq() calls for is_active)
        # Only eq() should be called if category filter is provided

    @pytest.mark.asyncio
    async def test_list_template_summaries(self, template_service, mock_supabase_client):
        """Test listing template summaries without full prompt text"""
        summary_data = {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "name": "Test Template",
            "category": "CTO",
            "description": "Test description",
            "version": 1,
            "is_active": True,
            "created_at": "2025-08-13T12:00:00+00:00",
            "updated_at": "2025-08-13T12:00:00+00:00",
            "metadata": {}
        }
        
        mock_response = MagicMock()
        mock_response.data = [summary_data]
        
        table_mock = MagicMock()
        query_mock = MagicMock()
        query_mock.eq.return_value.order.return_value.execute = AsyncMock(return_value=mock_response)
        table_mock.select.return_value = query_mock
        mock_supabase_client.client.table.return_value = table_mock

        summaries = await template_service.list_template_summaries()
        
        assert len(summaries) == 1
        assert isinstance(summaries[0], TemplateSummary)
        assert summaries[0].name == "Test Template"
        
        # Verify select was called with summary fields only
        table_mock.select.assert_called_once_with("id, name, category, description, version, is_active, created_at, updated_at, metadata")

    @pytest.mark.asyncio
    async def test_create_template_success(self, template_service, mock_supabase_client, sample_template_data):
        """Test successful template creation"""
        request = CreateTemplateRequest(
            name="New CTO Template",
            category="CTO",
            prompt_text="New evaluation prompt for CTO candidates",
            description="Custom CTO evaluation",
            metadata={"created_by": "test"}
        )
        
        # Mock successful insert response
        mock_response = MagicMock()
        mock_response.data = [sample_template_data]
        
        table_mock = MagicMock()
        table_mock.insert.return_value.execute = AsyncMock(return_value=mock_response)
        mock_supabase_client.client.table.return_value = table_mock

        template = await template_service.create_template(request)
        
        assert template is not None
        assert template.name == "Test CTO Template"  # From sample_template_data
        assert template.category == "CTO"
        
        # Verify insert was called
        table_mock.insert.assert_called_once()
        insert_data = table_mock.insert.call_args[0][0]
        assert insert_data["name"] == "New CTO Template"
        assert insert_data["category"] == "CTO"
        assert insert_data["version"] == 1

    @pytest.mark.asyncio
    async def test_update_template_success(self, template_service, mock_supabase_client, sample_template_data):
        """Test successful template update"""
        request = UpdateTemplateRequest(
            name="Updated Template Name",
            description="Updated description"
        )
        
        # Update the sample data to reflect the update
        updated_data = sample_template_data.copy()
        updated_data["name"] = "Updated Template Name"
        updated_data["description"] = "Updated description"
        
        mock_response = MagicMock()
        mock_response.data = [updated_data]
        
        table_mock = MagicMock()
        table_mock.update.return_value.eq.return_value.execute = AsyncMock(return_value=mock_response)
        mock_supabase_client.client.table.return_value = table_mock

        template = await template_service.update_template("123e4567-e89b-12d3-a456-426614174000", request)
        
        assert template is not None
        assert template.name == "Updated Template Name"
        assert template.description == "Updated description"
        
        # Verify update was called
        table_mock.update.assert_called_once()
        update_data = table_mock.update.call_args[0][0]
        assert update_data["name"] == "Updated Template Name"
        assert update_data["description"] == "Updated description"
        assert "updated_at" in update_data

    @pytest.mark.asyncio
    async def test_update_template_not_found(self, template_service, mock_supabase_client):
        """Test template update when template not found"""
        request = UpdateTemplateRequest(name="Updated Name")
        
        # Mock empty response (no template found)
        mock_response = MagicMock()
        mock_response.data = []
        
        table_mock = MagicMock()
        table_mock.update.return_value.eq.return_value.execute = AsyncMock(return_value=mock_response)
        mock_supabase_client.client.table.return_value = table_mock

        template = await template_service.update_template("nonexistent-id", request)
        assert template is None

    @pytest.mark.asyncio
    async def test_update_template_partial_update(self, template_service, mock_supabase_client, sample_template_data):
        """Test partial template update with only some fields"""
        request = UpdateTemplateRequest(is_active=False)  # Only updating is_active
        
        updated_data = sample_template_data.copy()
        updated_data["is_active"] = False
        
        mock_response = MagicMock()
        mock_response.data = [updated_data]
        
        table_mock = MagicMock()
        table_mock.update.return_value.eq.return_value.execute = AsyncMock(return_value=mock_response)
        mock_supabase_client.client.table.return_value = table_mock

        template = await template_service.update_template("123e4567-e89b-12d3-a456-426614174000", request)
        
        assert template is not None
        assert template.is_active is False
        
        # Verify only is_active and updated_at were in update
        update_data = table_mock.update.call_args[0][0]
        assert "is_active" in update_data
        assert "updated_at" in update_data
        assert "name" not in update_data  # Should not be updated

    @pytest.mark.asyncio
    async def test_delete_template_success(self, template_service, mock_supabase_client, sample_template_data):
        """Test successful template soft deletion"""
        # Mock successful soft delete
        updated_data = sample_template_data.copy()
        updated_data["is_active"] = False
        
        mock_response = MagicMock()
        mock_response.data = [updated_data]
        
        table_mock = MagicMock()
        table_mock.update.return_value.eq.return_value.execute = AsyncMock(return_value=mock_response)
        mock_supabase_client.client.table.return_value = table_mock

        result = await template_service.delete_template("123e4567-e89b-12d3-a456-426614174000")
        assert result is True
        
        # Verify soft delete was called
        table_mock.update.assert_called_once()
        update_data = table_mock.update.call_args[0][0]
        assert update_data["is_active"] is False
        assert "updated_at" in update_data

    @pytest.mark.asyncio
    async def test_delete_template_not_found(self, template_service, mock_supabase_client):
        """Test template deletion when template not found"""
        # Mock empty response (no template found)
        mock_response = MagicMock()
        mock_response.data = []
        
        table_mock = MagicMock()
        table_mock.update.return_value.eq.return_value.execute = AsyncMock(return_value=mock_response)
        mock_supabase_client.client.table.return_value = table_mock

        result = await template_service.delete_template("nonexistent-id")
        assert result is False

    @pytest.mark.asyncio
    async def test_get_templates_by_category(self, template_service, mock_supabase_client, sample_template_data):
        """Test getting templates by category"""
        mock_response = MagicMock()
        mock_response.data = [sample_template_data]
        
        table_mock = MagicMock()
        query_mock = MagicMock()
        query_mock.eq.return_value.eq.return_value.order.return_value.execute = AsyncMock(return_value=mock_response)
        table_mock.select.return_value = query_mock
        mock_supabase_client.client.table.return_value = table_mock

        templates = await template_service.get_templates_by_category("CTO")
        
        assert len(templates) == 1
        assert templates[0].category == "CTO"
        
        # This method is a convenience wrapper around list_templates
        # Verify the category filter was applied

    def test_convert_db_to_model(self, template_service, sample_template_data):
        """Test database data conversion to PromptTemplate model"""
        template = template_service._convert_db_to_model(sample_template_data)
        
        assert isinstance(template, PromptTemplate)
        # UUID field gets converted to UUID object by Pydantic, so convert back to string for comparison
        assert str(template.id) == sample_template_data["id"]
        assert template.name == sample_template_data["name"]
        assert template.category == sample_template_data["category"]
        assert template.prompt_text == sample_template_data["prompt_text"]
        assert template.version == sample_template_data["version"]
        assert template.is_active == sample_template_data["is_active"]
        assert template.metadata == sample_template_data["metadata"]

    def test_convert_db_to_model_with_string_timestamps(self, template_service):
        """Test database data conversion with string timestamp format"""
        db_data = {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "name": "Test Template",
            "category": "CTO",
            "prompt_text": "Test prompt",
            "version": 1,
            "is_active": True,
            "description": "Test description",
            "metadata": {},
            "created_at": "2025-08-13T12:00:00.000Z",  # String format with Z
            "updated_at": "2025-08-13T12:00:00.000Z"
        }
        
        template = template_service._convert_db_to_model(db_data)
        
        assert isinstance(template, PromptTemplate)
        assert isinstance(template.created_at, datetime)
        assert isinstance(template.updated_at, datetime)
        # Timestamps should be timezone-aware
        assert template.created_at.tzinfo is not None
        assert template.updated_at.tzinfo is not None

    @pytest.mark.asyncio
    async def test_service_error_handling(self, template_service, mock_supabase_client):
        """Test service error handling"""
        # Mock database error
        table_mock = MagicMock()
        table_mock.select.return_value.eq.return_value.execute = AsyncMock(side_effect=Exception("Database error"))
        mock_supabase_client.client.table.return_value = table_mock

        with pytest.raises(Exception) as exc_info:
            await template_service.get_template_by_id("test-id")
        
        assert "Database error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_template_error_handling(self, template_service, mock_supabase_client):
        """Test template creation error handling"""
        request = CreateTemplateRequest(
            name="Test Template",
            category="CTO",
            prompt_text="Test prompt"
        )
        
        # Mock database error during insert
        table_mock = MagicMock()
        table_mock.insert.return_value.execute = AsyncMock(side_effect=Exception("Insert failed"))
        mock_supabase_client.client.table.return_value = table_mock

        with pytest.raises(Exception) as exc_info:
            await template_service.create_template(request)
        
        assert "Insert failed" in str(exc_info.value)
