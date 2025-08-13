"""
Unit tests for prompt template Pydantic models

Tests validation, serialization, and error handling for all template models
"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4, UUID
from pydantic import ValidationError
from app.models.template_models import (
    PromptTemplate,
    CreateTemplateRequest,
    UpdateTemplateRequest,
    TemplateListResponse,
    TemplateSummary,
    TemplateListSummaryResponse,
    EnhancedScoringRequest,
    ScoringJobResponse,
    TemplateErrorResponse,
    DeleteTemplateResponse
)


class TestPromptTemplateModel:
    """Test the main PromptTemplate model"""

    def test_valid_template_creation(self):
        """Test creating a valid template model"""
        now = datetime.now(timezone.utc)
        template = PromptTemplate(
            id=uuid4(),
            name="Test CTO Template",
            category="CTO",
            prompt_text="Test prompt content for evaluation",
            version=1,
            is_active=True,
            description="Test template description",
            metadata={"tags": ["test", "cto"]},
            created_at=now,
            updated_at=now
        )
        
        assert template.name == "Test CTO Template"
        assert template.category == "CTO"  # Should be normalized to uppercase
        assert template.prompt_text == "Test prompt content for evaluation"
        assert template.version == 1
        assert template.is_active is True
        assert template.metadata == {"tags": ["test", "cto"]}

    def test_template_category_normalization(self):
        """Test that category is normalized to uppercase"""
        now = datetime.now(timezone.utc)
        template = PromptTemplate(
            id=uuid4(),
            name="Test Template",
            category="cto",  # lowercase
            prompt_text="Test prompt",
            created_at=now,
            updated_at=now
        )
        
        assert template.category == "CTO"  # Should be uppercase

    def test_template_field_validation_empty_name(self):
        """Test that empty name raises validation error"""
        now = datetime.now(timezone.utc)
        
        with pytest.raises(ValidationError) as exc_info:
            PromptTemplate(
                id=uuid4(),
                name="",  # Empty name
                category="CTO",
                prompt_text="Test prompt",
                created_at=now,
                updated_at=now
            )
        
        assert "String should have at least 1 character" in str(exc_info.value)

    def test_template_field_validation_empty_category(self):
        """Test that empty category raises validation error"""
        now = datetime.now(timezone.utc)
        
        with pytest.raises(ValidationError) as exc_info:
            PromptTemplate(
                id=uuid4(),
                name="Test Template",
                category="",  # Empty category
                prompt_text="Test prompt",
                created_at=now,
                updated_at=now
            )
        
        assert "String should have at least 1 character" in str(exc_info.value)

    def test_template_field_validation_empty_prompt_text(self):
        """Test that empty prompt text raises validation error"""
        now = datetime.now(timezone.utc)
        
        with pytest.raises(ValidationError) as exc_info:
            PromptTemplate(
                id=uuid4(),
                name="Test Template",
                category="CTO",
                prompt_text="",  # Empty prompt
                created_at=now,
                updated_at=now
            )
        
        assert "String should have at least 1 character" in str(exc_info.value)

    def test_template_serialization(self):
        """Test template model serialization"""
        template_id = uuid4()
        now = datetime.now(timezone.utc)
        
        template = PromptTemplate(
            id=template_id,
            name="Test Template",
            category="CTO",
            prompt_text="Test prompt content",
            version=1,
            is_active=True,
            description="Test description",
            metadata={"tags": ["test"]},
            created_at=now,
            updated_at=now
        )
        
        serialized = template.model_dump()
        
        assert serialized["id"] == template_id
        assert serialized["name"] == "Test Template"
        assert serialized["category"] == "CTO"
        assert serialized["prompt_text"] == "Test prompt content"
        assert serialized["version"] == 1
        assert serialized["is_active"] is True
        assert serialized["metadata"] == {"tags": ["test"]}

    def test_template_whitespace_stripping(self):
        """Test that whitespace is properly stripped from string fields"""
        now = datetime.now(timezone.utc)
        
        template = PromptTemplate(
            id=uuid4(),
            name="  Test Template  ",  # Whitespace padding
            category="  cto  ",
            prompt_text="  Test prompt content  ",
            created_at=now,
            updated_at=now
        )
        
        assert template.name == "Test Template"
        assert template.category == "CTO"
        assert template.prompt_text == "Test prompt content"


class TestCreateTemplateRequest:
    """Test the CreateTemplateRequest model"""

    def test_valid_create_request(self):
        """Test creating a valid template creation request"""
        request = CreateTemplateRequest(
            name="New CTO Template",
            category="CTO",
            prompt_text="Evaluate this candidate for CTO position...",
            description="Custom CTO evaluation template",
            is_active=True,
            metadata={"created_by": "admin", "version": "1.0"}
        )
        
        assert request.name == "New CTO Template"
        assert request.category == "CTO"
        assert request.prompt_text == "Evaluate this candidate for CTO position..."
        assert request.description == "Custom CTO evaluation template"
        assert request.is_active is True
        assert request.metadata == {"created_by": "admin", "version": "1.0"}

    def test_create_request_required_fields(self):
        """Test that required fields are enforced"""
        with pytest.raises(ValidationError) as exc_info:
            CreateTemplateRequest(
                # Missing required fields
                description="Missing required fields"
            )
        
        error_str = str(exc_info.value)
        assert "Field required" in error_str

    def test_create_request_empty_validation(self):
        """Test validation of empty required fields"""
        with pytest.raises(ValidationError) as exc_info:
            CreateTemplateRequest(
                name="",  # Empty name
                category="CTO",
                prompt_text="Test prompt"
            )
        
        assert "String should have at least 1 character" in str(exc_info.value)

    def test_create_request_category_normalization(self):
        """Test that category is normalized to uppercase in create requests"""
        request = CreateTemplateRequest(
            name="Test Template",
            category="cio",  # lowercase
            prompt_text="Test prompt"
        )
        
        assert request.category == "CIO"

    def test_create_request_defaults(self):
        """Test default values in create requests"""
        request = CreateTemplateRequest(
            name="Test Template",
            category="CTO",
            prompt_text="Test prompt"
            # Not providing optional fields
        )
        
        assert request.is_active is True  # Default
        assert request.metadata == {}  # Default empty dict
        assert request.description is None  # Default None


class TestUpdateTemplateRequest:
    """Test the UpdateTemplateRequest model"""

    def test_valid_update_request(self):
        """Test creating a valid template update request"""
        request = UpdateTemplateRequest(
            name="Updated Template Name",
            description="Updated description",
            prompt_text="Updated prompt content",
            is_active=False,
            metadata={"updated_by": "admin"}
        )
        
        assert request.name == "Updated Template Name"
        assert request.description == "Updated description"
        assert request.prompt_text == "Updated prompt content"
        assert request.is_active is False
        assert request.metadata == {"updated_by": "admin"}

    def test_update_request_all_optional(self):
        """Test that all fields are optional in update requests"""
        request = UpdateTemplateRequest()
        
        assert request.name is None
        assert request.description is None
        assert request.prompt_text is None
        assert request.is_active is None
        assert request.metadata is None

    def test_update_request_partial_update(self):
        """Test partial update with only some fields provided"""
        request = UpdateTemplateRequest(
            name="New Name",
            is_active=False
            # Other fields not provided
        )
        
        assert request.name == "New Name"
        assert request.is_active is False
        assert request.description is None
        assert request.prompt_text is None

    def test_update_request_empty_field_validation(self):
        """Test that empty fields are rejected if provided"""
        with pytest.raises(ValidationError) as exc_info:
            UpdateTemplateRequest(
                name="",  # Empty name provided
                prompt_text="Valid prompt"
            )
        
        assert "String should have at least 1 character" in str(exc_info.value)

    def test_update_request_whitespace_handling(self):
        """Test whitespace handling in update requests"""
        request = UpdateTemplateRequest(
            name="  Updated Name  ",
            prompt_text="  Updated prompt  "
        )
        
        assert request.name == "Updated Name"
        assert request.prompt_text == "Updated prompt"


class TestEnhancedScoringRequest:
    """Test the EnhancedScoringRequest model"""

    def test_scoring_request_with_template_id(self):
        """Test scoring request using template_id"""
        template_id = uuid4()
        request = EnhancedScoringRequest(template_id=template_id)
        
        assert request.template_id == template_id
        assert request.prompt is None

    def test_scoring_request_with_prompt(self):
        """Test scoring request using raw prompt"""
        request = EnhancedScoringRequest(prompt="Custom evaluation prompt")
        
        assert request.prompt == "Custom evaluation prompt"
        assert request.template_id is None

    def test_scoring_request_requires_one_field(self):
        """Test that either template_id or prompt is required"""
        with pytest.raises(ValidationError) as exc_info:
            EnhancedScoringRequest()  # Neither field provided
        
        assert "Either 'template_id' or 'prompt' must be provided" in str(exc_info.value)

    def test_scoring_request_mutual_exclusion(self):
        """Test that template_id and prompt are mutually exclusive"""
        with pytest.raises(ValidationError) as exc_info:
            EnhancedScoringRequest(
                template_id=uuid4(),
                prompt="Custom prompt"  # Both provided
            )
        
        assert "Cannot provide both 'template_id' and 'prompt'" in str(exc_info.value)


class TestResponseModels:
    """Test response models"""

    def test_template_list_response(self):
        """Test TemplateListResponse model"""
        now = datetime.now(timezone.utc)
        template = PromptTemplate(
            id=uuid4(),
            name="Test Template",
            category="CTO",
            prompt_text="Test prompt",
            created_at=now,
            updated_at=now
        )
        
        response = TemplateListResponse(
            templates=[template],
            count=1
        )
        
        assert len(response.templates) == 1
        assert response.count == 1
        assert response.templates[0].name == "Test Template"

    def test_template_summary(self):
        """Test TemplateSummary model"""
        now = datetime.now(timezone.utc)
        summary = TemplateSummary(
            id=uuid4(),
            name="Test Template",
            category="CTO",
            description="Test description",
            version=1,
            is_active=True,
            created_at=now,
            updated_at=now,
            metadata={"test": True}
        )
        
        assert summary.name == "Test Template"
        assert summary.category == "CTO"
        # Note: TemplateSummary doesn't include prompt_text

    def test_scoring_job_response(self):
        """Test ScoringJobResponse model"""
        job_id = uuid4()
        profile_id = uuid4()
        template_id = uuid4()
        now = datetime.now(timezone.utc)
        
        response = ScoringJobResponse(
            job_id=job_id,
            status="processing",
            profile_id=profile_id,
            template_id=template_id,
            created_at=now
        )
        
        assert response.job_id == job_id
        assert response.status == "processing"
        assert response.profile_id == profile_id
        assert response.template_id == template_id

    def test_scoring_job_response_without_template(self):
        """Test ScoringJobResponse without template_id (backward compatibility)"""
        job_id = uuid4()
        profile_id = uuid4()
        now = datetime.now(timezone.utc)
        
        response = ScoringJobResponse(
            job_id=job_id,
            status="processing",
            profile_id=profile_id,
            created_at=now
            # No template_id provided
        )
        
        assert response.job_id == job_id
        assert response.template_id is None

    def test_delete_template_response(self):
        """Test DeleteTemplateResponse model"""
        template_id = uuid4()
        response = DeleteTemplateResponse(
            message="Template successfully deleted",
            template_id=template_id
        )
        
        assert response.message == "Template successfully deleted"
        assert response.template_id == template_id

    def test_template_error_response(self):
        """Test TemplateErrorResponse model"""
        response = TemplateErrorResponse(
            error="ValidationError",
            message="Template name is required",
            details={"field": "name", "code": "required"}
        )
        
        assert response.error == "ValidationError"
        assert response.message == "Template name is required"
        assert response.details == {"field": "name", "code": "required"}


class TestModelIntegration:
    """Integration tests between models"""

    def test_create_to_template_conversion(self):
        """Test converting CreateTemplateRequest data to PromptTemplate"""
        # This would typically happen in the service layer
        create_request = CreateTemplateRequest(
            name="Integration Test Template",
            category="cio",  # lowercase
            prompt_text="Integration test prompt",
            description="Integration test description",
            metadata={"test": "integration"}
        )
        
        # Simulate service layer creating template from request
        now = datetime.now(timezone.utc)
        template = PromptTemplate(
            id=uuid4(),
            name=create_request.name,
            category=create_request.category,  # Should be normalized
            prompt_text=create_request.prompt_text,
            description=create_request.description,
            is_active=create_request.is_active,
            metadata=create_request.metadata,
            created_at=now,
            updated_at=now
        )
        
        assert template.name == create_request.name
        assert template.category == "CIO"  # Normalized
        assert template.prompt_text == create_request.prompt_text
        assert template.is_active == create_request.is_active

    def test_update_request_validation_edge_cases(self):
        """Test edge cases in update request validation"""
        # Valid: Only whitespace in optional field that becomes None
        request = UpdateTemplateRequest(description="   ")
        assert request.description == ""  # Whitespace is stripped
        
        # Valid: Metadata can be empty dict
        request = UpdateTemplateRequest(metadata={})
        assert request.metadata == {}
        
        # Valid: All None values
        request = UpdateTemplateRequest()
        assert all(getattr(request, field) is None for field in ["name", "description", "prompt_text", "is_active", "metadata"])
