"""
AI Role Compatibility Check Service

This service provides Stage 3 of the Quality Gates pipeline by performing
lightweight AI-powered role compatibility checks before expensive detailed scoring.

Purpose:
- Quick sanity check: "Does this profile make sense as a [ROLE] candidate?"
- Auto-role detection: If submitted role fails, try other roles (CTO->CIO->CISO)
- Prevent mismatched scoring (e.g., CIO profile scored against CISO prompt)
- Save costs by avoiding detailed scoring on obviously wrong role matches
"""

import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
import uuid
from enum import Enum

from app.core.logging import get_logger
from app.core.config import settings
from app.services.llm_scoring_service import LLMScoringService
from app.models.canonical.profile import CanonicalProfile
from pydantic import BaseModel


class ExecutiveRole(str, Enum):
    """Executive roles we can validate against"""
    CTO = "CTO"
    CIO = "CIO" 
    CISO = "CISO"


class RoleCompatibilityResult(BaseModel):
    """Result of role compatibility check"""
    is_valid: bool  # Passes the gate for at least one role
    suggested_role: ExecutiveRole  # Best matching role
    original_role: ExecutiveRole  # Role that was originally suggested
    role_changed: bool  # Whether we're suggesting a different role
    compatibility_scores: Dict[ExecutiveRole, float]  # 0.0-1.0 scores for each checked role
    confidence: float  # Overall confidence in suggestion (0.0-1.0)
    reasoning: str  # Explanation of decision
    processing_time_ms: float
    tokens_used: int
    validation_errors: List[str] = []
    detailed_role_data: Dict[str, Dict[str, Any]] = {}  # Raw role data from AI response


class AIRoleCompatibilityService:
    """
    Service for AI-powered role compatibility checking
    
    This performs quick "sanity checks" using lightweight prompts to determine
    if a profile makes sense for a given executive role before expensive scoring.
    
    Features:
    - Quick role compatibility assessment (CTO/CIO/CISO)
    - Auto-role suggestion if submitted role doesn't fit
    - Lightweight prompts designed for speed over detail
    - Cost optimization before full scoring pipeline
    """
    
    def __init__(self):
        self.llm_service = LLMScoringService()
        self.logger = get_logger(__name__)
        
        # Compatibility thresholds
        self.minimum_compatibility_score = 0.4  # Minimum score to pass quick check
        self.good_compatibility_score = 0.65  # Score considered a good match
    
    
    async def check_role_compatibility(
        self,
        profile: CanonicalProfile,
        suggested_role: ExecutiveRole
    ) -> RoleCompatibilityResult:
        """
        Check role compatibility using unified template approach
        
        This performs a single AI call that evaluates all roles at once using the
        configurable template from settings.ROLE_COMPATIBILITY_TEMPLATE.
        
        Args:
            profile: Profile data from Cassidy validation (Stage 2)
            suggested_role: Role submitted by user
            
        Returns:
            RoleCompatibilityResult with gate result and recommended role
        """
        start_time = datetime.now()
        compatibility_id = str(uuid.uuid4())[:8]
        
        self.logger.info(
            f"🎯 ROLE_COMPATIBILITY_START: Starting unified role compatibility check",
            compatibility_id=compatibility_id,
            profile_name=profile.full_name,
            suggested_role=suggested_role.value,
            stage="STAGE_3_AI_ROLE_COMPATIBILITY"
        )
        
        validation_errors = []
        
        # Check if LLM service is properly initialized
        if not self.llm_service or not self.llm_service.client:
            error_msg = f"LLM service not properly initialized: client={bool(self.llm_service.client) if self.llm_service else 'no_service'}"
            self.logger.error(
                f"❌ LLM_SERVICE_ERROR: {error_msg}",
                compatibility_id=compatibility_id,
                has_llm_service=bool(self.llm_service),
                has_client=bool(self.llm_service.client) if self.llm_service else False,
                api_key_configured=bool(settings.OPENAI_API_KEY)
            )
            return RoleCompatibilityResult(
                is_valid=False,
                suggested_role=suggested_role,
                original_role=suggested_role,
                role_changed=False,
                compatibility_scores={suggested_role: 0.0},
                confidence=0.0,
                reasoning=error_msg,
                processing_time_ms=0.0,
                tokens_used=0,
                validation_errors=[error_msg],
                detailed_role_data={}
            )
        
        try:
            # Build profile data string for the user message
            profile_data = f"""
Name: {profile.full_name}
Current Role: {profile.job_title}
Company: {profile.company}
LinkedIn: {profile.linkedin_url}

About:
{profile.about[:1000] if profile.about else "Not provided"}

Experience:
{self._format_experience(profile.experience[:5])}

Education:
{self._format_education(profile.education[:3])}
"""
            
            # Replace placeholder in user message template
            user_message = settings.ROLE_COMPATIBILITY_USER_MESSAGE.replace(
                "{{profile_data}}", profile_data
            )
            
            # Use proper system/user message structure
            raw_response, parsed_response = await self._call_ai_with_messages(
                system_message=settings.ROLE_COMPATIBILITY_SYSTEM_MESSAGE,
                user_message=user_message,
                model=settings.STAGE_3_MODEL,
                max_tokens=800,  # Increased for more detailed response
                temperature=0.2   # ChatGPT recommended 0.2 for determinism
            )
            
            # Extract results from AI response (new format)
            recommended_role_str = parsed_response.get("recommended_primary_role", "NONE")
            proceed_with_scoring = parsed_response.get("proceed_with_scoring", False)
            compatible_roles_data = parsed_response.get("compatible_roles", [])
            overall_assessment = parsed_response.get("overall_assessment", "No assessment provided")
            
            # Extract compatibility scores and find highest scoring role
            compatibility_scores = {}
            best_score = 0.0
            best_role = None
            
            for role_data in compatible_roles_data:
                role_str = role_data.get("role", "")
                confidence = role_data.get("confidence", 0.0)
                
                try:
                    role_enum = ExecutiveRole(role_str)
                    compatibility_scores[role_enum] = min(1.0, max(0.0, float(confidence)))
                    
                    if confidence > best_score:
                        best_score = confidence
                        best_role = role_enum
                        
                except (ValueError, TypeError) as e:
                    self.logger.warning(
                        f"Invalid role or score in AI response",
                        compatibility_id=compatibility_id,
                        role=role_str,
                        score=confidence,
                        error=str(e)
                    )
            
            # Determine recommended role
            recommended_role = None
            if recommended_role_str and recommended_role_str != "NONE":
                try:
                    recommended_role = ExecutiveRole(recommended_role_str)
                except ValueError:
                    self.logger.warning(
                        f"Invalid recommended role from AI: {recommended_role_str}",
                        compatibility_id=compatibility_id
                    )
                    recommended_role = None
            
            # If no valid recommended role, use the best scoring role
            if not recommended_role:
                recommended_role = best_role if best_role else suggested_role
            
            # Fallback if everything failed
            if not compatibility_scores:
                recommended_role = suggested_role  # Fall back to original
                proceed_with_scoring = False
                compatibility_scores = {suggested_role: 0.0}
                best_score = 0.0
                overall_assessment = "Failed to determine role compatibility"
                validation_errors.append("AI response did not contain valid role data")
            
            # Calculate processing metrics
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            tokens_used = len(str(raw_response)) // 4  # Rough token estimate
            
            # Determine if role changed
            role_changed = recommended_role != suggested_role
            
            # Store detailed role information from AI response
            detailed_role_data = {}
            for role_data in compatible_roles_data:
                role_str = role_data.get("role", "")
                if role_str in ["CTO", "CIO", "CISO"]:
                    detailed_role_data[role_str] = {
                        "key_qualifications": role_data.get("key_qualifications", []),
                        "missing_qualifications": role_data.get("missing_qualifications", []),
                        "reasoning": role_data.get("reasoning", ""),
                        "compatible": role_data.get("compatible", False),
                        "confidence": role_data.get("confidence", 0.0)
                    }
            
            # Log result
            if proceed_with_scoring:
                if role_changed:
                    self.logger.info(
                        f"🔄 ROLE_CHANGED: Profile passed gate with different role",
                        compatibility_id=compatibility_id,
                        original_role=suggested_role.value,
                        recommended_role=recommended_role.value,
                        confidence=best_score,
                        stage="STAGE_3_AI_ROLE_COMPATIBILITY",
                        status="PASSED_WITH_CHANGE"
                    )
                else:
                    self.logger.info(
                        f"✅ ORIGINAL_ROLE_CONFIRMED: Profile passed gate with original role",
                        compatibility_id=compatibility_id,
                        role=suggested_role.value,
                        confidence=best_score,
                        stage="STAGE_3_AI_ROLE_COMPATIBILITY",
                        status="PASSED_ORIGINAL"
                    )
            else:
                self.logger.info(
                    f"❌ GATE_FAILED: Profile failed compatibility gate",
                    compatibility_id=compatibility_id,
                    recommended_role=recommended_role.value if recommended_role else "NONE",
                    confidence=best_score,
                    threshold=self.minimum_compatibility_score,
                    stage="STAGE_3_AI_ROLE_COMPATIBILITY",
                    status="FAILED"
                )
            
            return RoleCompatibilityResult(
                is_valid=proceed_with_scoring,
                suggested_role=recommended_role,
                original_role=suggested_role,
                role_changed=role_changed,
                compatibility_scores=compatibility_scores,
                confidence=best_score,
                reasoning=overall_assessment,
                processing_time_ms=processing_time,
                tokens_used=tokens_used,
                validation_errors=validation_errors,
                detailed_role_data=detailed_role_data
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Get full traceback for debugging
            import traceback
            full_traceback = traceback.format_exc()
            
            self.logger.error(
                f"❌ ROLE_COMPATIBILITY_ERROR: Unexpected error during unified role compatibility check",
                compatibility_id=compatibility_id,
                error=str(e),
                error_type=type(e).__name__,
                stage="STAGE_3_AI_ROLE_COMPATIBILITY",
                full_traceback=full_traceback,
                profile_name=profile.full_name if profile else "unknown",
                suggested_role=suggested_role.value if suggested_role else "unknown"
            )
            
            # Return fallback result
            return RoleCompatibilityResult(
                is_valid=False,
                suggested_role=suggested_role,  # Fall back to original
                original_role=suggested_role,
                role_changed=False,
                compatibility_scores={suggested_role: 0.0},
                confidence=0.0,
                reasoning=f"Role compatibility check failed: {str(e)}",
                processing_time_ms=processing_time,
                tokens_used=0,
                validation_errors=[f"Compatibility check error: {str(e)}"],
                detailed_role_data={}
            )
    
    async def _call_ai_with_messages(
        self,
        system_message: str,
        user_message: str,
        model: str,
        max_tokens: int,
        temperature: float
    ) -> Tuple[str, Dict[str, Any]]:
        """Call AI service with proper system/user message structure"""
        try:
            response = await self.llm_service.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            raw_response = response.choices[0].message.content
            
            # Log raw response for debugging
            self.logger.info(f"Raw AI response length: {len(raw_response) if raw_response else 0}")
            if raw_response:
                self.logger.info(f"Raw AI response preview: {raw_response[:200]}...")
            else:
                self.logger.warning("AI returned empty response")
            
            # Try to parse JSON response
            import json
            try:
                # Strip markdown code blocks if present (common with GPT-4o)
                json_content = raw_response.strip()
                if json_content.startswith('```json'):
                    # Remove ```json from start and ``` from end
                    json_content = json_content[7:]  # Remove ```json
                    if json_content.endswith('```'):
                        json_content = json_content[:-3]  # Remove ```
                elif json_content.startswith('```'):
                    # Remove ``` from start and end
                    json_content = json_content[3:]  # Remove ```
                    if json_content.endswith('```'):
                        json_content = json_content[:-3]  # Remove ```
                
                json_content = json_content.strip()
                parsed_response = json.loads(json_content)
                return raw_response, parsed_response
            except json.JSONDecodeError as e:
                self.logger.warning(f"Failed to parse AI response as JSON: {str(e)}")
                self.logger.warning(f"Full raw response: {repr(raw_response)}")
                return raw_response, {}
                
        except Exception as e:
            self.logger.error(f"AI service call failed: {str(e)}")
            raise
    
    def _format_experience(self, experiences: List[Dict]) -> str:
        """Format experience list for AI prompt"""
        if not experiences:
            return "Not provided"
        
        formatted = []
        for i, exp in enumerate(experiences, 1):
            title = exp.get("title", "Unknown Title")
            company = exp.get("company", "Unknown Company")
            duration = exp.get("duration", "")
            description = exp.get("description", "")[:200]  # Limit description
            
            formatted.append(f"{i}. {title} at {company} ({duration})")
            if description:
                formatted.append(f"   {description}...")
        
        return "\n".join(formatted)
    
    def _format_education(self, education: List[Dict]) -> str:
        """Format education list for AI prompt"""
        if not education:
            return "Not provided"
        
        formatted = []
        for edu in education:
            degree = edu.get("degree", "")
            school = edu.get("school", "")
            field = edu.get("field", "")
            
            if degree and school:
                formatted.append(f"- {degree} from {school}")
                if field:
                    formatted.append(f"  Field: {field}")
        
        return "\n".join(formatted) if formatted else "Not provided"
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of AI role compatibility service"""
        try:
            # Test with minimal profile data
            test_profile = CanonicalProfile(
                profile_id="test",
                full_name="Test User",
                job_title="Software Engineer",
                company="Test Company"
            )
            
            # Quick test with unified compatibility check
            result = await self.check_role_compatibility(
                test_profile, ExecutiveRole.CTO
            )
            
            return {
                "service": "ai_role_compatibility",
                "status": "healthy",
                "llm_service_available": bool(self.llm_service.client),
                "test_check_successful": True,
                "compatibility_threshold": self.minimum_compatibility_score,
                "system_message_configured": bool(settings.ROLE_COMPATIBILITY_SYSTEM_MESSAGE),
                "user_message_configured": bool(settings.ROLE_COMPATIBILITY_USER_MESSAGE),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            return {
                "service": "ai_role_compatibility",
                "status": "unhealthy", 
                "error": str(e),
                "llm_service_available": bool(self.llm_service.client),
                "system_message_configured": bool(settings.ROLE_COMPATIBILITY_SYSTEM_MESSAGE),
                "user_message_configured": bool(settings.ROLE_COMPATIBILITY_USER_MESSAGE),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
