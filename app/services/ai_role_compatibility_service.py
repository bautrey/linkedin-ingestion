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
        
        try:
            # Use unified template for single AI call that evaluates all roles
            raw_response, parsed_response = await self.llm_service.score_profile(
                profile=profile,
                prompt=settings.ROLE_COMPATIBILITY_TEMPLATE,
                model=settings.STAGE_3_MODEL,  # Use configured model for Stage 3
                max_tokens=300,  # Allow more tokens for comprehensive evaluation
                temperature=0.1   # Low temperature for consistent results
            )
            
            # Extract results from AI response
            recommended_role_str = parsed_response.get("recommended_role", "NONE")
            passes_gate = parsed_response.get("passes_gate", False)
            compatibility_scores_raw = parsed_response.get("compatibility_scores", {})
            confidence = min(1.0, max(0.0, float(parsed_response.get("confidence", 0.0))))
            key_factors = parsed_response.get("key_factors", [])
            reasoning = parsed_response.get("reasoning", "No reasoning provided")
            
            # Convert compatibility scores to proper format
            compatibility_scores = {}
            for role_str, score in compatibility_scores_raw.items():
                try:
                    role_enum = ExecutiveRole(role_str)
                    compatibility_scores[role_enum] = min(1.0, max(0.0, float(score)))
                except (ValueError, TypeError) as e:
                    self.logger.warning(
                        f"Invalid role or score in AI response",
                        compatibility_id=compatibility_id,
                        role=role_str,
                        score=score,
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
            
            # If no valid recommended role, find the best scoring role
            if not recommended_role and compatibility_scores:
                recommended_role = max(compatibility_scores, key=compatibility_scores.get)
                passes_gate = compatibility_scores[recommended_role] >= self.minimum_compatibility_score
            
            # Fallback if everything failed
            if not recommended_role:
                recommended_role = suggested_role  # Fall back to original
                passes_gate = False
                compatibility_scores = {suggested_role: 0.0}
                confidence = 0.0
                reasoning = "Failed to determine role compatibility"
                validation_errors.append("AI response did not contain valid role recommendation")
            
            # Calculate processing metrics
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            tokens_used = len(str(raw_response)) // 4  # Rough token estimate
            
            # Determine if role changed
            role_changed = recommended_role != suggested_role
            
            # Log result
            if passes_gate:
                if role_changed:
                    self.logger.info(
                        f"🔄 ROLE_CHANGED: Profile passed gate with different role",
                        compatibility_id=compatibility_id,
                        original_role=suggested_role.value,
                        recommended_role=recommended_role.value,
                        confidence=confidence,
                        stage="STAGE_3_AI_ROLE_COMPATIBILITY",
                        status="PASSED_WITH_CHANGE"
                    )
                else:
                    self.logger.info(
                        f"✅ ORIGINAL_ROLE_CONFIRMED: Profile passed gate with original role",
                        compatibility_id=compatibility_id,
                        role=suggested_role.value,
                        confidence=confidence,
                        stage="STAGE_3_AI_ROLE_COMPATIBILITY",
                        status="PASSED_ORIGINAL"
                    )
            else:
                self.logger.info(
                    f"❌ GATE_FAILED: Profile failed compatibility gate",
                    compatibility_id=compatibility_id,
                    recommended_role=recommended_role.value if recommended_role else "NONE",
                    confidence=confidence,
                    threshold=self.minimum_compatibility_score,
                    stage="STAGE_3_AI_ROLE_COMPATIBILITY",
                    status="FAILED"
                )
            
            return RoleCompatibilityResult(
                is_valid=passes_gate,
                suggested_role=recommended_role,
                original_role=suggested_role,
                role_changed=role_changed,
                compatibility_scores=compatibility_scores,
                confidence=confidence,
                reasoning=reasoning,
                processing_time_ms=processing_time,
                tokens_used=tokens_used,
                validation_errors=validation_errors
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            self.logger.error(
                f"❌ ROLE_COMPATIBILITY_ERROR: Unexpected error during unified role compatibility check",
                compatibility_id=compatibility_id,
                error=str(e),
                error_type=type(e).__name__,
                stage="STAGE_3_AI_ROLE_COMPATIBILITY"
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
                validation_errors=[f"Compatibility check error: {str(e)}"]
            )
    
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
                "template_configured": bool(settings.ROLE_COMPATIBILITY_TEMPLATE),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            return {
                "service": "ai_role_compatibility",
                "status": "unhealthy", 
                "error": str(e),
                "llm_service_available": bool(self.llm_service.client),
                "template_configured": bool(settings.ROLE_COMPATIBILITY_TEMPLATE),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
