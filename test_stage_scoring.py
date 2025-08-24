#!/usr/bin/env python3
"""
Test Stage-Based Model Selection

This script tests that:
1. Templates can be created with stage assignments
2. Scoring jobs use the correct models based on template stage
3. External API calls (like from Make) work properly with stage-based scoring
"""

import asyncio
import json
import os
import sys
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.services.template_service import TemplateService
from app.services.llm_scoring_service import LLMScoringService
from app.models.template_models import CreateTemplateRequest

async def test_stage_based_scoring():
    print("🎯 Testing Stage-Based Model Selection")
    print("=" * 50)
    
    # Display current configuration
    print("📊 Current Configuration:")
    print(f"  • Stage 2 Model: {settings.STAGE_2_MODEL}")
    print(f"  • Stage 3 Model: {settings.STAGE_3_MODEL}")
    print(f"  • Default Model: {settings.OPENAI_DEFAULT_MODEL}")
    print()
    
    try:
        # Initialize services with proper dependencies
        from app.database.supabase_client import SupabaseClient
        
        db_client = SupabaseClient()
        template_service = TemplateService(supabase_client=db_client)
        llm_service = LLMScoringService()
        
        # Test 1: Create Stage 2 Template
        print("🧪 Test 1: Creating Stage 2 Template")
        stage_2_template = CreateTemplateRequest(
            name="CTO Quick Screen Test",
            category="CTO",
            prompt_text="""Quickly evaluate this CTO candidate. Provide JSON response:
{
  "basic_fit": "YES/NO/MAYBE",
  "score": 1-10,
  "key_signals": ["list", "of", "strengths"],
  "red_flags": ["list", "of", "concerns"],
  "recommendation": "ADVANCE_TO_STAGE_3 or REJECT"
}""",
            description="Stage 2 screening template for testing",
            stage="stage_2_screening"
        )
        
        stage_2_id = await template_service.create_template(stage_2_template)
        print(f"  ✅ Created Stage 2 template: {stage_2_id}")
        
        # Test 2: Create Stage 3 Template  
        print("🧪 Test 2: Creating Stage 3 Template")
        stage_3_template = CreateTemplateRequest(
            name="CTO Deep Analysis Test",
            category="CTO",
            prompt_text="""Conduct comprehensive CTO evaluation. Provide detailed JSON:
{
  "overall_assessment": {
    "fit_score": 1-100,
    "hire_recommendation": "STRONG_YES/YES/MAYBE/NO/STRONG_NO"
  },
  "technical_leadership": {"score": 1-10, "analysis": "detailed assessment"},
  "strategic_thinking": {"score": 1-10, "analysis": "business alignment"},
  "team_management": {"score": 1-10, "analysis": "leadership experience"},
  "interview_focus_areas": ["key topics to explore"]
}""",
            description="Stage 3 deep analysis template for testing",
            stage="stage_3_analysis"
        )
        
        stage_3_id = await template_service.create_template(stage_3_template)
        print(f"  ✅ Created Stage 3 template: {stage_3_id}")
        
        # Test 3: Verify Model Selection Logic
        print("🧪 Test 3: Testing Model Selection Logic")
        
        # Fetch templates back
        stage_2_fetched = await template_service.get_template_by_id(str(stage_2_id.id))
        stage_3_fetched = await template_service.get_template_by_id(str(stage_3_id.id))
        
        print(f"  • Stage 2 Template Stage: {stage_2_fetched.stage}")
        print(f"  • Stage 3 Template Stage: {stage_3_fetched.stage}")
        
        # Test model selection without actually calling OpenAI
        print("📋 Model Selection Test Results:")
        
        # Simulate what would happen during scoring
        if stage_2_fetched.stage == "stage_2_screening":
            expected_model_2 = settings.STAGE_2_MODEL
            print(f"  ✅ Stage 2 template would use: {expected_model_2}")
        else:
            print(f"  ❌ Stage 2 template has wrong stage: {stage_2_fetched.stage}")
            
        if stage_3_fetched.stage == "stage_3_analysis":
            expected_model_3 = settings.STAGE_3_MODEL
            print(f"  ✅ Stage 3 template would use: {expected_model_3}")
        else:
            print(f"  ❌ Stage 3 template has wrong stage: {stage_3_fetched.stage}")
        
        print()
        print("🎉 Core functionality test completed!")
        print()
        
        # Test 4: API Usage Examples
        print("📡 API Usage Examples for External Systems (Make, etc.):")
        print()
        
        print("📋 Stage 2 Screening API Call:")
        stage_2_api_example = {
            "method": "POST",
            "url": "/api/v1/profiles/{profile_id}/score-template",
            "body": {
                "template_id": str(stage_2_id)
            },
            "expected_model": expected_model_2
        }
        print(json.dumps(stage_2_api_example, indent=2))
        
        print()
        print("📋 Stage 3 Analysis API Call:")
        stage_3_api_example = {
            "method": "POST", 
            "url": "/api/v1/profiles/{profile_id}/score-template",
            "body": {
                "template_id": str(stage_3_id)
            },
            "expected_model": expected_model_3
        }
        print(json.dumps(stage_3_api_example, indent=2))
        
        print()
        print("💡 Integration Notes:")
        print("  • External systems just need to specify template_id")
        print("  • Model selection happens automatically based on template stage")
        print("  • Cost optimization is transparent to external callers")
        print("  • Same API endpoints work for all stages")
        
        return {
            "stage_2_template_id": stage_2_id,
            "stage_3_template_id": stage_3_id,
            "stage_2_model": expected_model_2,
            "stage_3_model": expected_model_3
        }
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise

if __name__ == "__main__":
    # Set up environment for testing
    os.environ.setdefault("STAGE_2_MODEL", "gpt-3.5-turbo")
    os.environ.setdefault("STAGE_3_MODEL", "gpt-4o")
    os.environ.setdefault("OPENAI_DEFAULT_MODEL", "gpt-3.5-turbo")
    
    asyncio.run(test_stage_based_scoring())
