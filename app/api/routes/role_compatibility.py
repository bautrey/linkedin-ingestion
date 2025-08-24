"""
Stage 3: Role Compatibility Check Endpoint

Fast AI screening to determine which roles (CTO, CIO, CISO) a candidate 
should be evaluated for, if any. Uses a lightweight AI model for quick screening.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio

from app.core.logging import LoggerMixin
from app.core.config import settings
from app.database.supabase_client import SupabaseClient
from app.services.ai_role_compatibility_service import AIRoleCompatibilityService, ExecutiveRole, RoleCompatibilityResult as ServiceResult
from app.models.canonical.profile import RoleType, CanonicalProfile

router = APIRouter(prefix="/api/v1/profiles", tags=["Role Compatibility"])


class RoleCompatibilityRequest(BaseModel):
    """Request model for role compatibility check"""
    target_roles: Optional[List[RoleType]] = Field(
        default=None, 
        description="Specific roles to check compatibility for (if not provided, checks all roles)"
    )
    fast_screening: bool = Field(
        default=True, 
        description="Use fast/cheaper AI model for screening (vs detailed model)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "target_roles": ["CTO", "CIO"],
                "fast_screening": True
            }
        }


class RoleCompatibilityResult(BaseModel):
    """Individual role compatibility result"""
    role: RoleType = Field(..., description="Role type (CTO, CIO, CISO)")
    compatible: bool = Field(..., description="Whether candidate is compatible with this role")
    confidence: float = Field(..., description="Confidence score (0.0-1.0)")
    reasoning: str = Field(..., description="Brief explanation for the compatibility assessment")
    key_qualifications: List[str] = Field(default_factory=list, description="Key qualifications found for this role")
    missing_qualifications: List[str] = Field(default_factory=list, description="Important qualifications missing for this role")


class RoleCompatibilityResponse(BaseModel):
    """Response model for role compatibility check"""
    profile_id: str = Field(..., description="Profile ID that was evaluated")
    linkedin_url: str = Field(..., description="LinkedIn URL of the profile")
    proceed_with_scoring: bool = Field(..., description="Whether to proceed with detailed scoring")
    compatible_roles: List[RoleCompatibilityResult] = Field(..., description="Role compatibility results")
    recommended_primary_role: Optional[RoleType] = Field(None, description="Best-fit role recommendation")
    overall_assessment: str = Field(..., description="Overall candidate assessment summary")
    ai_response_time: float = Field(..., description="AI processing time in seconds")
    model_used: str = Field(..., description="AI model used for screening")
    
    class Config:
        json_schema_extra = {
            "example": {
                "profile_id": "uuid-12345",
                "linkedin_url": "https://www.linkedin.com/in/sample-cto/",
                "proceed_with_scoring": True,
                "compatible_roles": [
                    {
                        "role": "CTO",
                        "compatible": True,
                        "confidence": 0.85,
                        "reasoning": "Strong technical leadership experience with enterprise architecture",
                        "key_qualifications": ["VP Engineering", "System Architecture", "Team Leadership"],
                        "missing_qualifications": ["Public Cloud Migration"]
                    }
                ],
                "recommended_primary_role": "CTO",
                "overall_assessment": "Strong technical leader with relevant experience",
                "ai_response_time": 2.3,
                "model_used": "gpt-4o-mini"
            }
        }


class RoleCompatibilityService(LoggerMixin):
    """Service class for role compatibility screening using unified AI service"""
    
    def __init__(self):
        self.db_client = SupabaseClient()
        self.ai_service = AIRoleCompatibilityService()
    
    async def check_role_compatibility(self, profile_id: str, request: RoleCompatibilityRequest) -> RoleCompatibilityResponse:
        """
        Check role compatibility using unified AI service
        
        Args:
            profile_id: Profile ID to evaluate  
            request: Role compatibility request parameters
            
        Returns:
            RoleCompatibilityResponse with compatibility results
        """
        start_time = datetime.now()
        
        self.logger.info("Starting unified role compatibility check", profile_id=profile_id)
        
        # Get profile from database
        db_profile = await self.db_client.get_profile_by_id(profile_id)
        if not db_profile:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "PROFILE_NOT_FOUND",
                    "message": f"Profile with ID {profile_id} not found",
                    "profile_id": profile_id
                }
            )
        
        # Convert database profile to CanonicalProfile for AI service
        canonical_profile = CanonicalProfile(
            profile_id=profile_id,
            full_name=db_profile.get("name", ""),
            job_title=db_profile.get("position", ""),
            company=db_profile.get("company", ""),
            linkedin_url=db_profile.get("url", ""),
            about=db_profile.get("about", ""),
            experience=db_profile.get("experience", []),
            education=db_profile.get("education", []),
            certifications=db_profile.get("certifications", [])
        )
        
        # Use first role as suggested role (for compatibility with unified service)
        target_roles = request.target_roles or [RoleType.CTO, RoleType.CIO, RoleType.CISO]
        suggested_role = ExecutiveRole(target_roles[0].value)
        
        try:
            # Call unified AI service
            result = await self.ai_service.check_role_compatibility(
                profile=canonical_profile,
                suggested_role=suggested_role
            )
            
            # Convert service result to API response format
            compatibility_results = []
            
            # Create results for each target role based on compatibility scores
            for target_role in target_roles:
                exec_role = ExecutiveRole(target_role.value)
                score = result.compatibility_scores.get(exec_role, 0.0)
                is_compatible = exec_role == result.suggested_role and result.is_valid
                
                compatibility_results.append(RoleCompatibilityResult(
                    role=target_role,
                    compatible=is_compatible,
                    confidence=score,
                    reasoning=result.reasoning if is_compatible else f"Lower compatibility score: {score:.2f}",
                    key_qualifications=[],  # Not provided by unified service
                    missing_qualifications=[]  # Not provided by unified service
                ))
            
            # Determine recommended primary role
            recommended_role = None
            if result.is_valid:
                try:
                    recommended_role = RoleType(result.suggested_role.value)
                except ValueError:
                    pass
            
            # Calculate response time
            response_time = result.processing_time_ms / 1000.0
            
            self.logger.info(
                "Unified role compatibility check completed",
                profile_id=profile_id,
                proceed_with_scoring=result.is_valid,
                recommended_role=result.suggested_role.value if result.suggested_role else None,
                confidence=result.confidence,
                response_time=response_time
            )
            
            return RoleCompatibilityResponse(
                profile_id=profile_id,
                linkedin_url=db_profile.get("url", ""),
                proceed_with_scoring=result.is_valid,
                compatible_roles=compatibility_results,
                recommended_primary_role=recommended_role,
                overall_assessment=result.reasoning,
                ai_response_time=response_time,
                model_used=settings.STAGE_3_MODEL
            )
            
        except Exception as e:
            self.logger.error(
                "Unified role compatibility check failed",
                profile_id=profile_id,
                error=str(e),
                error_type=type(e).__name__
            )
            
            # Return negative result on error
            negative_results = [
                RoleCompatibilityResult(
                    role=role,
                    compatible=False,
                    confidence=0.0,
                    reasoning=f"Screening failed: {str(e)}",
                    key_qualifications=[],
                    missing_qualifications=[]
                )
                for role in target_roles
            ]
            
            response_time = (datetime.now() - start_time).total_seconds()
            
            return RoleCompatibilityResponse(
                profile_id=profile_id,
                linkedin_url=db_profile.get("url", ""),
                proceed_with_scoring=False,
                compatible_roles=negative_results,
                recommended_primary_role=None,
                overall_assessment=f"Compatibility check failed: {str(e)}",
                ai_response_time=response_time,
                model_used="error"
            )


# Initialize the service
role_compatibility_service = RoleCompatibilityService()


class TemplateViewResponse(BaseModel):
    """Response model for viewing role compatibility template"""
    system_message: str = Field(..., description="System message for AI role compatibility")
    user_message_template: str = Field(..., description="User message template with placeholder")
    model: str = Field(..., description="AI model used for role compatibility")
    minimum_threshold: float = Field(..., description="Minimum compatibility score to pass gate")
    template_source: str = Field(..., description="Source of the template (config/environment)")
    last_updated: Optional[str] = Field(None, description="Last updated timestamp if available")


@router.get("/role-compatibility/template", response_model=TemplateViewResponse, summary="View Role Compatibility Template")
async def get_role_compatibility_template() -> TemplateViewResponse:
    """
    **View Current Role Compatibility Template**
    
    Returns the current system and user message templates used for Stage 3 role compatibility checks.
    This allows you to see exactly what criteria and format the AI is using
    to evaluate candidates.
    
    - **System Message**: The system instructions defining the AI's role and behavior
    - **User Message Template**: The user message template with {{profile_data}} placeholder
    - **Model**: AI model used for evaluation  
    - **Threshold**: Minimum score required to pass the compatibility gate
    - **Source**: Whether template comes from config file or environment variable
    """
    service = AIRoleCompatibilityService()
    
    return TemplateViewResponse(
        system_message=settings.ROLE_COMPATIBILITY_SYSTEM_MESSAGE,
        user_message_template=settings.ROLE_COMPATIBILITY_USER_MESSAGE,
        model=settings.STAGE_3_MODEL,
        minimum_threshold=service.minimum_compatibility_score,
        template_source="configuration",
        last_updated=None
    )


@router.post("/{profile_id}/role-compatibility", response_model=RoleCompatibilityResponse, summary="Check Role Compatibility")
async def check_role_compatibility(
    profile_id: str,
    request: RoleCompatibilityRequest = RoleCompatibilityRequest()
) -> RoleCompatibilityResponse:
    """
    **Stage 3: Role Compatibility Check**
    
    Fast AI screening to determine which executive technology roles (CTO, CIO, CISO) 
    a candidate should be evaluated for, if any.
    
    - **Fast Screening**: Uses lightweight AI model for quick assessment
    - **Role-Specific**: Evaluates compatibility with each target role
    - **Gateway Decision**: Determines if candidate should proceed to detailed scoring
    - **Cost Efficient**: Cheaper than detailed scoring, filters out unqualified candidates
    
    **Next Steps**:
    - If `proceed_with_scoring` is `true`, call Stage 4 detailed scoring
    - Use `recommended_primary_role` for the detailed scoring role parameter
    - If `false`, candidate should not proceed further in the evaluation process
    """
    return await role_compatibility_service.check_role_compatibility(profile_id, request)
