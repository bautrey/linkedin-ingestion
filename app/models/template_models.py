"""
Pydantic models for prompt templates management system

Handles template data validation, serialization, and API request/response models
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict, field_validator


class PromptTemplate(BaseModel):
    """
    Complete prompt template model with all fields
    
    Used for database records and detailed API responses
    """
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        use_enum_values=True,
        from_attributes=True
    )
    
    id: UUID
    name: str = Field(..., min_length=1, max_length=255, description="Human-readable template name")
    category: str = Field(..., min_length=1, max_length=100, description="Template category (CTO, CIO, CISO, etc.)")
    prompt_text: str = Field(..., min_length=1, description="The actual evaluation prompt content")
    version: int = Field(default=1, ge=1, description="Version number for template iterations")
    is_active: bool = Field(default=True, description="Whether template is currently active")
    description: Optional[str] = Field(None, description="Optional description of template purpose")
    stage: Optional[str] = Field(None, description="Evaluation stage (stage_2_screening, stage_3_analysis) - determines which model to use")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional structured data")
    created_at: datetime = Field(..., description="Template creation timestamp")
    updated_at: datetime = Field(..., description="Last modification timestamp")
    
    @field_validator('name')
    @classmethod
    def validate_name_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Template name cannot be empty')
        return v.strip()
    
    @field_validator('category') 
    @classmethod
    def validate_category_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Template category cannot be empty')
        return v.strip().upper()  # Normalize to uppercase
    
    @field_validator('prompt_text')
    @classmethod
    def validate_prompt_text_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Prompt text cannot be empty')
        return v.strip()


class CreateTemplateRequest(BaseModel):
    """
    Request model for creating new templates
    
    Used in POST /api/v1/templates
    """
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    name: str = Field(..., min_length=1, max_length=255, description="Template name")
    category: str = Field(..., min_length=1, max_length=100, description="Template category")
    prompt_text: str = Field(..., min_length=1, description="Evaluation prompt content")
    description: Optional[str] = Field(None, description="Optional template description")
    stage: Optional[str] = Field(None, description="Evaluation stage (stage_2_screening, stage_3_analysis)")
    is_active: bool = Field(default=True, description="Whether template should be active")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional data")
    
    @field_validator('name')
    @classmethod
    def validate_name_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Template name is required')
        return v.strip()
    
    @field_validator('category')
    @classmethod
    def validate_category_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Template category is required')
        return v.strip().upper()
    
    @field_validator('prompt_text')
    @classmethod
    def validate_prompt_text_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Prompt text is required')
        return v.strip()


class UpdateTemplateRequest(BaseModel):
    """
    Request model for updating existing templates
    
    Used in PUT /api/v1/templates/{id}
    All fields are optional for partial updates
    """
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Updated template name")
    description: Optional[str] = Field(None, description="Updated template description")
    prompt_text: Optional[str] = Field(None, min_length=1, description="Updated prompt content")
    is_active: Optional[bool] = Field(None, description="Updated active status")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Updated metadata")
    
    # Note: category and version are not updatable for data integrity
    
    @field_validator('name')
    @classmethod
    def validate_name_if_provided(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and (not v or not v.strip()):
            raise ValueError('Template name cannot be empty if provided')
        return v.strip() if v else None
    
    @field_validator('prompt_text')
    @classmethod
    def validate_prompt_text_if_provided(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and (not v or not v.strip()):
            raise ValueError('Prompt text cannot be empty if provided')
        return v.strip() if v else None


class TemplateListResponse(BaseModel):
    """
    Response model for template list operations
    
    Used in GET /api/v1/templates
    """
    model_config = ConfigDict(use_enum_values=True)
    
    templates: List[PromptTemplate] = Field(..., description="List of templates")
    count: int = Field(..., ge=0, description="Total number of templates")


class TemplateSummary(BaseModel):
    """
    Lightweight template model without full prompt text
    
    Used in list operations where full prompt text isn't needed
    """
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    name: str
    category: str
    description: Optional[str]
    version: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TemplateListSummaryResponse(BaseModel):
    """
    Response model for template list operations with summaries
    
    Alternative to TemplateListResponse when full prompt text isn't needed
    """
    model_config = ConfigDict(use_enum_values=True)
    
    templates: List[TemplateSummary] = Field(..., description="List of template summaries")
    count: int = Field(..., ge=0, description="Total number of templates")


class EnhancedScoringRequest(BaseModel):
    """
    Enhanced scoring request supporting template_id, role-based lookup, or raw prompt
    
    Used in POST /api/v1/profiles/{id}/score
    Maintains backward compatibility while adding template support
    """
    model_config = ConfigDict(
        validate_assignment=True,
        str_strip_whitespace=True
    )
    
    template_id: Optional[UUID] = Field(None, description="ID of template to use for scoring")
    role: Optional[str] = Field(None, description="Role category to automatically select template (CTO, CIO, CISO)")
    prompt: Optional[str] = Field(None, min_length=1, description="Raw prompt text (backward compatibility)")
    
    @field_validator('template_id', 'prompt')
    @classmethod
    def validate_template_or_prompt_provided(cls, v, info):
        # This validator runs for each field individually
        # We'll handle the mutual exclusion in a model validator
        return v
    
    def model_post_init(self, __context) -> None:
        """Post-init validation to ensure exactly one of template_id, role, or prompt is provided"""
        provided_fields = sum([bool(self.template_id), bool(self.role), bool(self.prompt)])
        
        if provided_fields == 0:
            raise ValueError("One of 'template_id', 'role', or 'prompt' must be provided")
        if provided_fields > 1:
            raise ValueError("Only one of 'template_id', 'role', or 'prompt' can be provided")
        
        if self.role:
            # Validate role is one of the expected values
            valid_roles = {"CTO", "CIO", "CISO"}
            role_upper = self.role.upper()
            if role_upper not in valid_roles:
                raise ValueError(f"Role must be one of: {', '.join(valid_roles)}")
            # Normalize the role value
            self.role = role_upper


class ScoringJobResponse(BaseModel):
    """
    Response model for scoring job creation
    
    Enhanced to include template_id when template-based scoring is used
    """
    model_config = ConfigDict(use_enum_values=True)
    
    job_id: UUID = Field(..., description="Unique scoring job identifier")
    status: str = Field(..., description="Current job status")
    profile_id: UUID = Field(..., description="Profile being scored")
    template_id: Optional[UUID] = Field(None, description="Template used for scoring (if any)")
    created_at: datetime = Field(..., description="Job creation timestamp")


class TemplateErrorResponse(BaseModel):
    """
    Error response model for template-related operations
    """
    model_config = ConfigDict(use_enum_values=True)
    
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error context")


class DeleteTemplateResponse(BaseModel):
    """
    Response model for template deletion operations
    """
    model_config = ConfigDict(use_enum_values=True)
    
    message: str = Field(..., description="Deletion confirmation message")
    template_id: UUID = Field(..., description="ID of deleted template")
