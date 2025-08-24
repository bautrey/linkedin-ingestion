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
from app.database.supabase_client import SupabaseClient
from app.services.llm_scoring_service import LLMScoringService
from app.models.canonical.profile import RoleType

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
    """Service class for role compatibility screening logic"""
    
    def __init__(self):
        self.db_client = SupabaseClient()
        # Use fast model for screening
        self.llm_service = LLMScoringService()
        # Override with fast model settings for screening
        self.screening_model = "gpt-4o-mini"  # Fast, cheaper model
        self.screening_max_tokens = 1000  # Shorter responses
    
    async def check_role_compatibility(self, profile_id: str, request: RoleCompatibilityRequest) -> RoleCompatibilityResponse:
        """
        Check role compatibility for a profile using fast AI screening
        
        Args:
            profile_id: Profile ID to evaluate
            request: Role compatibility request parameters
            
        Returns:
            RoleCompatibilityResponse with compatibility results
        """
        start_time = datetime.now()
        
        self.logger.info("Starting role compatibility check", profile_id=profile_id)
        
        # Get profile from database
        profile = await self.db_client.get_profile_by_id(profile_id)
        if not profile:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "PROFILE_NOT_FOUND",
                    "message": f"Profile with ID {profile_id} not found",
                    "profile_id": profile_id
                }
            )
        
        # Determine which roles to check
        target_roles = request.target_roles or [RoleType.CTO, RoleType.CIO, RoleType.CISO]
        
        # Build screening prompt
        screening_prompt = self._build_screening_prompt(profile, target_roles)
        
        try:
            # Use fast model for screening
            ai_response = await self._call_screening_ai(screening_prompt, request.fast_screening)
            
            # Parse AI response into structured results
            compatibility_results = self._parse_ai_response(ai_response, target_roles)
            
            # Determine if we should proceed with detailed scoring
            proceed_with_scoring = any(result.compatible for result in compatibility_results)
            
            # Find recommended primary role (highest confidence compatible role)
            recommended_role = None
            if proceed_with_scoring:
                compatible = [r for r in compatibility_results if r.compatible]
                if compatible:
                    recommended_role = max(compatible, key=lambda x: x.confidence).role
            
            # Calculate response time
            response_time = (datetime.now() - start_time).total_seconds()
            
            # Generate overall assessment
            overall_assessment = self._generate_overall_assessment(compatibility_results, proceed_with_scoring)
            
            self.logger.info(
                "Role compatibility check completed",
                profile_id=profile_id,
                proceed_with_scoring=proceed_with_scoring,
                compatible_roles=[r.role for r in compatibility_results if r.compatible],
                recommended_primary_role=recommended_role,
                response_time=response_time
            )
            
            return RoleCompatibilityResponse(
                profile_id=profile_id,
                linkedin_url=profile.get("url", ""),
                proceed_with_scoring=proceed_with_scoring,
                compatible_roles=compatibility_results,
                recommended_primary_role=recommended_role,
                overall_assessment=overall_assessment,
                ai_response_time=response_time,
                model_used=self.screening_model if request.fast_screening else self.llm_service.default_model
            )
            
        except Exception as e:
            self.logger.error(
                "Role compatibility check failed",
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
                linkedin_url=profile.get("url", ""),
                proceed_with_scoring=False,
                compatible_roles=negative_results,
                recommended_primary_role=None,
                overall_assessment=f"Compatibility check failed: {str(e)}",
                ai_response_time=response_time,
                model_used="error"
            )
    
    def _build_screening_prompt(self, profile: Dict[str, Any], target_roles: List[RoleType]) -> str:
        """Build AI prompt for role compatibility screening"""
        
        # Extract key profile information
        name = profile.get("name", "Unknown")
        headline = profile.get("position") or profile.get("headline", "")
        about = profile.get("about", "")[:500]  # Limit for screening
        experience = profile.get("experience", [])[:3]  # Top 3 experiences for speed
        education = profile.get("education", [])[:2]  # Top 2 education entries
        
        # Build concise profile summary for screening
        profile_summary = f"""
CANDIDATE: {name}
HEADLINE: {headline}
ABOUT: {about}

RECENT EXPERIENCE:
"""
        
        for i, exp in enumerate(experience, 1):
            title = exp.get("title", "Unknown")
            company = exp.get("company", "Unknown")
            duration = exp.get("duration", "")
            profile_summary += f"{i}. {title} at {company} ({duration})\n"
        
        if education:
            profile_summary += "\nEDUCATION:\n"
            for edu in education:
                degree = edu.get("degree", "")
                school = edu.get("school", "")
                profile_summary += f"- {degree} from {school}\n"
        
        # Role requirements (simplified for fast screening)
        role_requirements = {
            RoleType.CTO: "Technical leadership, software architecture, engineering management, technology strategy",
            RoleType.CIO: "IT strategy, digital transformation, enterprise systems, technology governance", 
            RoleType.CISO: "Information security, risk management, compliance, cybersecurity strategy"
        }
        
        roles_to_check = ", ".join([role.value for role in target_roles])
        requirements_text = "\n".join([
            f"{role.value}: {role_requirements[role]}" 
            for role in target_roles if role in role_requirements
        ])
        
        prompt = f"""
You are a technical recruiter conducting a FAST SCREENING of a candidate for executive technology roles.

CANDIDATE PROFILE:
{profile_summary}

ROLES TO EVALUATE: {roles_to_check}

ROLE REQUIREMENTS:
{requirements_text}

Provide a QUICK assessment for each role. For each role, respond with:
- COMPATIBLE: true/false
- CONFIDENCE: 0.0-1.0 (how confident are you?)
- REASONING: Brief explanation (1-2 sentences max)
- KEY_QUALIFICATIONS: 2-3 key strengths for this role
- MISSING_QUALIFICATIONS: 1-2 major gaps (if any)

Be FAST and DECISIVE. This is initial screening, not detailed evaluation.
Focus on obvious matches/mismatches based on titles, experience, and industry.

Format as JSON:
{{
  "roles": [
    {{
      "role": "CTO",
      "compatible": true/false,
      "confidence": 0.0-1.0,
      "reasoning": "brief explanation",
      "key_qualifications": ["qual1", "qual2"],
      "missing_qualifications": ["gap1", "gap2"]
    }}
  ]
}}
"""
        return prompt
    
    async def _call_screening_ai(self, prompt: str, use_fast_model: bool = True) -> str:
        """Call AI service for screening with appropriate model"""
        
        if use_fast_model:
            # Use fast, cheaper model for screening
            response = await self.llm_service.client.chat.completions.create(
                model=self.screening_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=self.screening_max_tokens,
                temperature=0.3  # Lower temperature for consistent screening
            )
            return response.choices[0].message.content
        else:
            # Use standard model
            return await self.llm_service.generate_completion(prompt)
    
    def _parse_ai_response(self, ai_response: str, target_roles: List[RoleType]) -> List[RoleCompatibilityResult]:
        """Parse AI response into structured compatibility results"""
        
        import json
        
        try:
            # Try to parse JSON response
            response_data = json.loads(ai_response)
            roles_data = response_data.get("roles", [])
            
            results = []
            for role_data in roles_data:
                role_str = role_data.get("role", "").upper()
                try:
                    role_type = RoleType(role_str)
                except ValueError:
                    continue
                
                result = RoleCompatibilityResult(
                    role=role_type,
                    compatible=bool(role_data.get("compatible", False)),
                    confidence=float(role_data.get("confidence", 0.0)),
                    reasoning=str(role_data.get("reasoning", "No reasoning provided")),
                    key_qualifications=role_data.get("key_qualifications", []),
                    missing_qualifications=role_data.get("missing_qualifications", [])
                )
                results.append(result)
            
            return results
            
        except Exception as e:
            self.logger.warning(
                "Failed to parse AI response as JSON, creating fallback results",
                error=str(e),
                ai_response=ai_response[:200]
            )
            
            # Fallback: create negative results for all target roles
            return [
                RoleCompatibilityResult(
                    role=role,
                    compatible=False,
                    confidence=0.0,
                    reasoning=f"Failed to parse AI response: {str(e)}",
                    key_qualifications=[],
                    missing_qualifications=[]
                )
                for role in target_roles
            ]
    
    def _generate_overall_assessment(self, results: List[RoleCompatibilityResult], proceed: bool) -> str:
        """Generate overall assessment summary"""
        
        if not proceed:
            return "Candidate does not meet the minimum requirements for executive technology roles."
        
        compatible_roles = [r.role.value for r in results if r.compatible]
        if not compatible_roles:
            return "No compatible roles identified during screening."
        
        if len(compatible_roles) == 1:
            return f"Candidate shows strong potential for the {compatible_roles[0]} role."
        else:
            roles_str = ", ".join(compatible_roles[:-1]) + f" and {compatible_roles[-1]}"
            return f"Candidate shows potential for multiple roles: {roles_str}. Detailed evaluation recommended."


# Initialize the service
role_compatibility_service = RoleCompatibilityService()


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
