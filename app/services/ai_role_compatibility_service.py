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
        
        # Lightweight prompts for quick role compatibility checking
        self._compatibility_prompts = {
            ExecutiveRole.CTO: self._get_cto_compatibility_prompt(),
            ExecutiveRole.CIO: self._get_cio_compatibility_prompt(), 
            ExecutiveRole.CISO: self._get_ciso_compatibility_prompt()
        }
    
    def _get_cto_compatibility_prompt(self) -> str:
        """Lightweight prompt for CTO role compatibility"""
        return """
Perform a QUICK high-level assessment of whether this profile is compatible with a Chief Technology Officer (CTO) role.

A CTO typically:
- Has significant technical leadership experience
- Led engineering teams or technical organizations
- Has hands-on software/technology development background
- Makes technology strategy decisions
- Often has titles like: VP Engineering, Head of Engineering, Technical Director, Lead Architect

Rate compatibility on scale 0.0-1.0 and provide brief reasoning.

Respond in JSON format:
{
  "compatibility_score": 0.0-1.0,
  "key_indicators": ["list of 2-3 key factors that support or hurt the match"],
  "reasoning": "brief 1-2 sentence explanation of why this profile fits/doesn't fit CTO role"
}
"""
    
    def _get_cio_compatibility_prompt(self) -> str:
        """Lightweight prompt for CIO role compatibility"""
        return """
Perform a QUICK high-level assessment of whether this profile is compatible with a Chief Information Officer (CIO) role.

A CIO typically:
- Has enterprise IT leadership experience
- Led IT operations, infrastructure, or information systems
- Focuses on business technology alignment and IT strategy
- Manages IT budgets, vendors, and enterprise systems
- Often has titles like: VP Information Technology, IT Director, Head of IT Operations

Rate compatibility on scale 0.0-1.0 and provide brief reasoning.

Respond in JSON format:
{
  "compatibility_score": 0.0-1.0,
  "key_indicators": ["list of 2-3 key factors that support or hurt the match"],
  "reasoning": "brief 1-2 sentence explanation of why this profile fits/doesn't fit CIO role"
}
"""
    
    def _get_ciso_compatibility_prompt(self) -> str:
        """Lightweight prompt for CISO role compatibility"""
        return """
Perform a QUICK high-level assessment of whether this profile is compatible with a Chief Information Security Officer (CISO) role.

A CISO typically:
- Has cybersecurity and information security leadership experience
- Led security teams, risk management, or compliance programs
- Has background in security architecture, incident response, or governance
- Manages security strategy, policies, and regulatory compliance
- Often has titles like: VP Security, Security Director, Head of Information Security

Rate compatibility on scale 0.0-1.0 and provide brief reasoning.

Respond in JSON format:
{
  "compatibility_score": 0.0-1.0,
  "key_indicators": ["list of 2-3 key factors that support or hurt the match"],
  "reasoning": "brief 1-2 sentence explanation of why this profile fits/doesn't fit CISO role"
}
"""
    
    async def check_role_compatibility(
        self,
        profile: CanonicalProfile,
        suggested_role: ExecutiveRole
    ) -> RoleCompatibilityResult:
        """
        Check if profile is compatible with suggested role, and find best role if not
        
        This is the main Stage 3 quality gate that:
        1. First checks compatibility with the suggested role
        2. If suggested role scores below threshold, checks other roles
        3. Returns pass/fail gate result and best matching role
        
        Args:
            profile: Profile data from Cassidy validation (Stage 2)
            suggested_role: Role submitted by user
            
        Returns:
            RoleCompatibilityResult with gate result and recommended role
        """
        start_time = datetime.now()
        compatibility_id = str(uuid.uuid4())[:8]
        
        self.logger.info(
            f"🎯 ROLE_COMPATIBILITY_START: Starting role compatibility check",
            compatibility_id=compatibility_id,
            profile_name=profile.full_name,
            suggested_role=suggested_role.value,
            stage="STAGE_3_AI_ROLE_COMPATIBILITY"
        )
        
        validation_errors = []
        total_tokens = 0
        compatibility_scores = {}
        
        try:
            # First, check compatibility with the suggested role
            self.logger.info(
                f"Checking compatibility with suggested {suggested_role.value} role",
                compatibility_id=compatibility_id,
                role=suggested_role.value
            )
            
            suggested_compatible, suggested_score, suggested_reasoning = await self.quick_role_check(
                profile=profile,
                role=suggested_role
            )
            
            # Store result for suggested role
            compatibility_scores[suggested_role] = suggested_score
            total_tokens += 200  # Approximate tokens for quick check
            
            # If suggested role is compatible, we're done - no need to check other roles
            if suggested_compatible:
                self.logger.info(
                    f"✅ SUGGESTED_ROLE_COMPATIBLE: Profile passes gate for {suggested_role.value}",
                    compatibility_id=compatibility_id,
                    role=suggested_role.value,
                    score=suggested_score,
                    stage="STAGE_3_AI_ROLE_COMPATIBILITY"
                )
                
                processing_time = (datetime.now() - start_time).total_seconds() * 1000
                
                return RoleCompatibilityResult(
                    is_valid=True,
                    suggested_role=suggested_role,
                    original_role=suggested_role,
                    role_changed=False,
                    compatibility_scores=compatibility_scores,
                    confidence=suggested_score,
                    reasoning=f"Profile is compatible with suggested {suggested_role.value} role. Score: {suggested_score:.2f}",
                    processing_time_ms=processing_time,
                    tokens_used=total_tokens
                )
            
            # If suggested role is not compatible, check other roles
            self.logger.info(
                f"⚠️ SUGGESTED_ROLE_INCOMPATIBLE: Profile doesn't pass gate for {suggested_role.value}, checking others",
                compatibility_id=compatibility_id,
                role=suggested_role.value,
                score=suggested_score,
                stage="STAGE_3_AI_ROLE_COMPATIBILITY"
            )
            
            # Check remaining roles
            for role in [r for r in ExecutiveRole if r != suggested_role]:
                self.logger.info(
                    f"Checking alternative role: {role.value}",
                    compatibility_id=compatibility_id,
                    alternative_role=role.value
                )
                
                try:
                    is_compatible, score, reasoning = await self.quick_role_check(
                        profile=profile,
                        role=role
                    )
                    
                    compatibility_scores[role] = score
                    total_tokens += 200  # Approximate tokens for quick check
                    
                    if is_compatible:
                        self.logger.info(
                            f"✅ ALTERNATIVE_ROLE_COMPATIBLE: Profile passes gate for {role.value}",
                            compatibility_id=compatibility_id,
                            alternative_role=role.value,
                            score=score,
                            stage="STAGE_3_AI_ROLE_COMPATIBILITY"
                        )
                    else:
                        self.logger.info(
                            f"❌ ALTERNATIVE_ROLE_INCOMPATIBLE: Profile doesn't pass gate for {role.value}",
                            compatibility_id=compatibility_id,
                            alternative_role=role.value,
                            score=score,
                            stage="STAGE_3_AI_ROLE_COMPATIBILITY"
                        )
                        
                except Exception as e:
                    self.logger.error(
                        f"❌ ALTERNATIVE_ROLE_CHECK_ERROR: Failed to check {role.value} compatibility",
                        compatibility_id=compatibility_id,
                        role=role.value,
                        error=str(e)
                    )
                    compatibility_scores[role] = 0.0
                    validation_errors.append(f"Failed to check {role.value} compatibility: {str(e)}")
            
            # Find best matching role from all checked
            if not compatibility_scores:
                raise ValueError("All role compatibility checks failed")
            
            best_role = max(compatibility_scores, key=compatibility_scores.get)
            best_score = compatibility_scores[best_role]
            
            # Determine overall validation result
            is_valid = best_score >= self.minimum_compatibility_score
            role_changed = best_role != suggested_role
            
            # Calculate confidence
            scores_list = sorted(compatibility_scores.values(), reverse=True)
            score_gap = scores_list[0] - (scores_list[1] if len(scores_list) > 1 else 0.0)
            confidence = min(1.0, best_score + (score_gap * 0.3))  # Bonus for clear winner
            
            # Generate reasoning
            if is_valid:
                if role_changed:
                    reasoning = f"Profile doesn't match suggested {suggested_role.value} role (score: {suggested_score:.2f}), " \
                              f"but shows compatibility with {best_role.value} role (score: {best_score:.2f})."
                else:
                    reasoning = f"Profile shows best compatibility with original {suggested_role.value} role " \
                              f"despite low score ({best_score:.2f})."
            else:
                reasoning = f"Profile doesn't show sufficient compatibility with any executive role. " \
                          f"Best match is {best_role.value} with score {best_score:.2f}, " \
                          f"below minimum threshold of {self.minimum_compatibility_score}."
            
            # Add score context
            all_scores = ", ".join([f"{role.value}: {score:.2f}" for role, score in compatibility_scores.items()])
            reasoning += f" All scores: {all_scores}"
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Log result
            if is_valid:
                if role_changed:
                    self.logger.info(
                        f"🔄 ROLE_CHANGED: Profile passed gate with different role",
                        compatibility_id=compatibility_id,
                        original_role=suggested_role.value,
                        best_role=best_role.value,
                        original_score=suggested_score,
                        best_score=best_score,
                        stage="STAGE_3_AI_ROLE_COMPATIBILITY",
                        status="PASSED_WITH_CHANGE"
                    )
                else:
                    self.logger.info(
                        f"✅ ORIGINAL_ROLE_BEST: Profile passed gate with original role",
                        compatibility_id=compatibility_id,
                        role=suggested_role.value,
                        score=best_score,
                        stage="STAGE_3_AI_ROLE_COMPATIBILITY",
                        status="PASSED_ORIGINAL"
                    )
            else:
                self.logger.info(
                    f"❌ ALL_ROLES_FAILED: Profile failed gate for all roles",
                    compatibility_id=compatibility_id,
                    best_role=best_role.value,
                    best_score=best_score,
                    threshold=self.minimum_compatibility_score,
                    stage="STAGE_3_AI_ROLE_COMPATIBILITY",
                    status="FAILED"
                )
            
            return RoleCompatibilityResult(
                is_valid=is_valid,
                suggested_role=best_role,
                original_role=suggested_role,
                role_changed=role_changed,
                compatibility_scores=compatibility_scores,
                confidence=confidence,
                reasoning=reasoning,
                processing_time_ms=processing_time,
                tokens_used=total_tokens,
                validation_errors=validation_errors
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            self.logger.error(
                f"❌ ROLE_COMPATIBILITY_ERROR: Unexpected error during role compatibility check",
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
                tokens_used=total_tokens,
                validation_errors=[f"Compatibility check error: {str(e)}"]
            )
    
    async def quick_role_check(
        self,
        profile: CanonicalProfile,
        role: ExecutiveRole
    ) -> Tuple[bool, float, str]:
        """
        Quick single-role compatibility check
        
        Args:
            profile: Profile to check
            role: Single role to validate against
            
        Returns:
            Tuple of (is_compatible, score, reasoning)
        """
        try:
            raw_response, parsed_response = await self.llm_service.score_profile(
                profile=profile,
                prompt=self._compatibility_prompts[role],
                model="gpt-3.5-turbo",  # Use faster model for quick checks
                max_tokens=150,  # Keep responses short
                temperature=0.1   # Low temperature for consistent results
            )
            
            score = parsed_response.get("compatibility_score", 0.0)
            # Ensure score is a float between 0 and 1
            score = max(0.0, min(1.0, float(score)))
            
            reasoning = parsed_response.get("reasoning", "No reasoning provided")
            key_indicators = parsed_response.get("key_indicators", [])
            
            is_compatible = score >= self.minimum_compatibility_score
            
            self.logger.info(
                f"ROLE_CHECK_RESULT: {role.value} compatibility check",
                role=role.value,
                score=score,
                is_compatible=is_compatible,
                threshold=self.minimum_compatibility_score,
                key_indicators=key_indicators
            )
            
            return is_compatible, score, reasoning
            
        except Exception as e:
            self.logger.error(
                f"ROLE_CHECK_ERROR: {role.value} compatibility check failed",
                role=role.value,
                error=str(e)
            )
            return False, 0.0, f"Compatibility check failed: {str(e)}"
    
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
            
            # Quick test with one role
            is_compatible, score, reasoning = await self.quick_role_check(
                test_profile, ExecutiveRole.CTO
            )
            
            return {
                "service": "ai_role_compatibility",
                "status": "healthy",
                "llm_service_available": bool(self.llm_service.client),
                "test_check_successful": True,
                "compatibility_threshold": self.minimum_compatibility_score,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            return {
                "service": "ai_role_compatibility",
                "status": "unhealthy", 
                "error": str(e),
                "llm_service_available": bool(self.llm_service.client),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
