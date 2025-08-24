#!/usr/bin/env python3
"""
Quality Gates Validation Pipeline Demo

This demo script shows how the URL validation service (Stage 1) and 
Quick validation service (Stage 2) work together as quality gates
before the full ingestion pipeline.

Usage:
    python3 -m app.services.validation_pipeline_demo "https://linkedin.com/in/someone"
"""

import asyncio
import sys
from typing import Dict, Any, Optional
from datetime import datetime

# Import validation services
from app.services.url_validation_service import URLValidationService
from app.services.quick_validation_service import CassidyQuickValidationService
from app.services.ai_role_compatibility_service import AIRoleCompatibilityService, ExecutiveRole


class ValidationPipelineDemo:
    """
    Demonstration of the complete validation pipeline quality gates
    
    This shows how to combine:
    - Stage 1: URL Sanitization & Validation
    - Stage 2: Cassidy Quick Validation
    - (Future) Stage 3: AI Role Compatibility Check
    """
    
    def __init__(self):
        self.url_validator = URLValidationService()
        self.quick_validator = CassidyQuickValidationService()
        self.role_validator = AIRoleCompatibilityService()
        print("🚀 Quality Gates Validation Pipeline Demo")
        print("=" * 60)
    
    async def run_validation_pipeline(self, raw_url: str, suggested_role: str = "CTO") -> Dict[str, Any]:
        """
        Run complete validation pipeline with quality gates
        
        Args:
            raw_url: Raw LinkedIn URL input (potentially dirty)
            
        Returns:
            Complete validation results with timing
        """
        start_time = datetime.now()
        pipeline_id = f"demo_{int(start_time.timestamp())}"
        
        print(f"\n📊 PIPELINE START: {pipeline_id}")
        print(f"Input URL: {raw_url}")
        print("-" * 60)
        
        results = {
            "pipeline_id": pipeline_id,
            "input_url": raw_url,
            "suggested_role": suggested_role,
            "stage_1_url_validation": None,
            "stage_2_quick_validation": None,
            "stage_3_role_compatibility": None,
            "overall_result": None,
            "timing": {},
            "pipeline_passed": False
        }
        
        # ===== STAGE 1: URL SANITIZATION & VALIDATION =====
        print("\n🔧 STAGE 1: URL Sanitization & Validation")
        print("Cleaning marketing parameters, normalizing URL format...")
        
        stage_1_start = datetime.now()
        url_result = self.url_validator.validate_and_sanitize_url(raw_url)
        stage_1_time = (datetime.now() - stage_1_start).total_seconds() * 1000
        
        results["stage_1_url_validation"] = url_result.model_dump()
        results["timing"]["stage_1_ms"] = stage_1_time
        
        if url_result.is_valid:
            print(f"✅ STAGE 1 PASSED: URL validation successful")
            print(f"   Original: {raw_url}")
            print(f"   Sanitized: {url_result.sanitized_url}")
            print(f"   Processing time: {stage_1_time:.1f}ms")
        else:
            print(f"❌ STAGE 1 FAILED: URL validation failed")
            for error in url_result.validation_errors:
                print(f"   Error: {error}")
            print(f"   Processing time: {stage_1_time:.1f}ms")
            
            # Early exit - no point in continuing pipeline
            results["overall_result"] = "FAILED_STAGE_1_URL_VALIDATION"
            results["timing"]["total_pipeline_ms"] = (datetime.now() - start_time).total_seconds() * 1000
            return results
        
        # ===== STAGE 2: CASSIDY QUICK VALIDATION =====
        print("\n🔍 STAGE 2: Cassidy Quick Validation")  
        print("Checking profile accessibility and basic data completeness...")  
        
        stage_2_start = datetime.now()
        try:
            quick_result = await self.quick_validator.quick_validate_profile(url_result.sanitized_url)
            stage_2_time = (datetime.now() - stage_2_start).total_seconds() * 1000
            
            results["stage_2_quick_validation"] = quick_result.model_dump()
            results["timing"]["stage_2_ms"] = stage_2_time
            
            if quick_result.is_valid:
                print(f"✅ STAGE 2 PASSED: Profile accessibility validated")
                if quick_result.profile_summary:
                    profile = quick_result.profile_summary
                    print(f"   Profile: {profile.get('full_name', 'Unknown')}")
                    print(f"   Headline: {profile.get('headline', 'Not specified')}")
                    print(f"   Experience: {profile.get('experience_count', 0)} positions")
                print(f"   Processing time: {stage_2_time:.1f}ms")
                
            else:
                print(f"❌ STAGE 2 FAILED: Profile validation failed")
                if not quick_result.profile_accessible:
                    print("   Issue: Profile is not accessible via LinkedIn")
                if not quick_result.basic_data_valid:
                    print("   Issue: Profile data is incomplete")
                for error in quick_result.validation_errors:
                    print(f"   Error: {error}")
                for warning in quick_result.warnings[:3]:  # Limit warnings shown
                    print(f"   Warning: {warning}")
                print(f"   Processing time: {stage_2_time:.1f}ms")
                
                # Early exit - profile not accessible
                results["overall_result"] = "FAILED_STAGE_2_PROFILE_VALIDATION"
                results["timing"]["total_pipeline_ms"] = (datetime.now() - start_time).total_seconds() * 1000
                return results
                
        except Exception as e:
            stage_2_time = (datetime.now() - stage_2_start).total_seconds() * 1000
            results["timing"]["stage_2_ms"] = stage_2_time
            results["stage_2_quick_validation"] = {"error": str(e)}
            results["overall_result"] = "ERROR_STAGE_2_EXCEPTION"
            results["timing"]["total_pipeline_ms"] = (datetime.now() - start_time).total_seconds() * 1000
            
            print(f"❌ STAGE 2 ERROR: Unexpected error during validation")
            print(f"   Error: {str(e)}")
            print(f"   Processing time: {stage_2_time:.1f}ms")
            return results
        
        # ===== STAGE 3: AI ROLE COMPATIBILITY CHECK =====
        print("\n🎯 STAGE 3: AI Role Compatibility Check")
        print(f"Checking if profile is compatible with {suggested_role} role...")
        
        stage_3_start = datetime.now()
        try:
            # Convert suggested role to enum
            suggested_role_enum = ExecutiveRole(suggested_role.upper())
            
            # Get profile from stage 2 for role checking - we need the full profile
            # For demo purposes, we'll create a mock profile from the summary
            from app.models.canonical.profile import CanonicalProfile
            if quick_result.profile_summary:
                summary = quick_result.profile_summary
                mock_profile = CanonicalProfile(
                    profile_id="demo-profile",
                    full_name=summary.get('full_name', 'Demo User'),
                    job_title=summary.get('headline', 'Professional'),
                    company=summary.get('company', 'Company'),
                    experiences=[]  # In real implementation, this would come from full profile
                )
            else:
                # Fallback if no profile summary available
                mock_profile = CanonicalProfile(
                    profile_id="demo-profile",
                    full_name="Demo User",
                    job_title="Professional",
                    company="Company"
                )
            
            # Check role compatibility
            role_result = await self.role_validator.check_role_compatibility(
                profile=mock_profile,
                suggested_role=suggested_role_enum
            )
            
            stage_3_time = (datetime.now() - stage_3_start).total_seconds() * 1000
            
            results["stage_3_role_compatibility"] = role_result.model_dump()
            results["timing"]["stage_3_ms"] = stage_3_time
            
            if role_result.is_valid:
                if role_result.role_changed:
                    print(f"🔄 STAGE 3 PASSED: Role changed to {role_result.suggested_role.value}")
                    print(f"   Original: {role_result.original_role.value} (score: {role_result.compatibility_scores.get(role_result.original_role, 0.0):.2f})")
                    print(f"   Suggested: {role_result.suggested_role.value} (score: {role_result.compatibility_scores.get(role_result.suggested_role, 0.0):.2f})")
                else:
                    print(f"✅ STAGE 3 PASSED: Role {role_result.suggested_role.value} confirmed")
                    print(f"   Compatibility score: {role_result.compatibility_scores.get(role_result.suggested_role, 0.0):.2f}")
                
                print(f"   Confidence: {role_result.confidence:.2f}")
                print(f"   Processing time: {stage_3_time:.1f}ms")
                print(f"   Tokens used: {role_result.tokens_used}")
                
                results["overall_result"] = "PASSED_ALL_QUALITY_GATES"
                results["pipeline_passed"] = True
                
            else:
                print(f"❌ STAGE 3 FAILED: Profile not compatible with any executive role")
                print(f"   Best match: {role_result.suggested_role.value} (score: {role_result.compatibility_scores.get(role_result.suggested_role, 0.0):.2f})")
                print(f"   Minimum threshold: 0.4")
                print(f"   Reasoning: {role_result.reasoning}")
                print(f"   Processing time: {stage_3_time:.1f}ms")
                
                results["overall_result"] = "FAILED_STAGE_3_ROLE_COMPATIBILITY"
                
        except Exception as e:
            stage_3_time = (datetime.now() - stage_3_start).total_seconds() * 1000
            results["timing"]["stage_3_ms"] = stage_3_time
            results["stage_3_role_compatibility"] = {"error": str(e)}
            results["overall_result"] = "ERROR_STAGE_3_EXCEPTION"
            
            print(f"❌ STAGE 3 ERROR: Unexpected error during role compatibility check")
            print(f"   Error: {str(e)}")
            print(f"   Processing time: {stage_3_time:.1f}ms")
        
        # ===== PIPELINE SUMMARY =====
        total_time = (datetime.now() - start_time).total_seconds() * 1000
        results["timing"]["total_pipeline_ms"] = total_time
        
        print("\n" + "=" * 60)
        print(f"🏁 PIPELINE COMPLETE: {results['overall_result']}")
        print(f"Total processing time: {total_time:.1f}ms")
        
        if results["pipeline_passed"]:
            print("🎉 All quality gates PASSED - ready for full ingestion!")
        else:
            print("🚫 Quality gates FAILED - ingestion blocked")
            
        return results
    
    def print_next_steps(self, results: Dict[str, Any]) -> None:
        """Print what would happen next in the full pipeline"""
        print("\n" + "=" * 60)
        print("📋 NEXT STEPS IN FULL PIPELINE:")
        
        if results["pipeline_passed"]:
            print("✅ Quality gates passed - would proceed to:")
            if results.get("stage_3_role_compatibility", {}).get("role_changed"):
                final_role = results["stage_3_role_compatibility"].get("suggested_role")
                print(f"   • Stage 4: Full LinkedIn profile scoring using {final_role} template")
            else:
                print(f"   • Stage 4: Full LinkedIn profile scoring using {suggested_role} template")
            print("   • Stage 5: Company data processing") 
            print("   • Stage 6: Database storage & indexing")
        else:
            failure_reason = results["overall_result"]
            if "STAGE_1" in failure_reason:
                print("❌ Failed at URL validation - would:")
                print("   • Log validation failure")
                print("   • Return error to user immediately")
                print("   • No further processing")
            elif "STAGE_2" in failure_reason:
                print("❌ Failed at profile validation - would:")
                print("   • Log inaccessible profile")
                print("   • Potentially retry with different approach")
                print("   • Return error to user")
            elif "STAGE_3" in failure_reason:
                print("❌ Failed at role compatibility check - would:")
                print("   • Log role mismatch")
                print("   • Suggest manual role review")
                print("   • Block expensive detailed scoring")


async def main():
    """Main demo function"""
    demo = ValidationPipelineDemo()
    
    # Get URL from command line or use default examples
    if len(sys.argv) > 1:
        url = sys.argv[1]
        role = sys.argv[2] if len(sys.argv) > 2 else "CTO"
        test_urls = [(url, role)]
    else:
        print("📝 No URL provided - using demo examples")
        test_urls = [
            ("https://linkedin.com/in/someone", "CTO"),  # Need to add https
            ("https://www.linkedin.com/in/test-profile/?utm_source=share&utm_medium=member", "CIO"), # Marketing params
            ("https://linkedin.com/in/nonexistent-profile-12345", "CISO"),  # Non-existent profile
            ("https://www.linkedin.com/company/google/", "CTO"),  # Company URL (invalid)
            ("not-a-linkedin-url-at-all", "CIO"),  # Completely invalid
        ]
    
    for i, (url, role) in enumerate(test_urls, 1):
        if len(test_urls) > 1:
            print(f"\n{'='*80}")
            print(f"TEST {i}/{len(test_urls)}: {role} Role")
        
        try:
            results = await demo.run_validation_pipeline(url, role)
            demo.print_next_steps(results)
            
        except KeyboardInterrupt:
            print("\n⏹️  Demo interrupted by user")
            break
        except Exception as e:
            print(f"\n❌ Demo error: {str(e)}")
        
        if len(test_urls) > 1 and i < len(test_urls):
            print(f"\n⏳ Continuing to next test in 2 seconds...")
            await asyncio.sleep(2)


if __name__ == "__main__":
    asyncio.run(main())
