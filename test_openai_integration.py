#!/usr/bin/env python3
"""
Quick local test for OpenAI integration
Tests the V1.85 LLM scoring functionality locally before production deployment
"""

import asyncio
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to Python path
sys.path.append('.')

from app.services.llm_scoring_service import LLMScoringService
from app.models.canonical.profile import CanonicalProfile, CanonicalExperienceEntry, CanonicalEducationEntry
from datetime import datetime


def create_test_profile():
    """Create a sample profile for testing"""
    return CanonicalProfile(
        profile_id="test-profile-123",
        full_name="John Doe",
        job_title="Senior Software Engineer", 
        company="TechCorp Inc",
        city="San Francisco",
        country="United States",
        about="Experienced software engineer with 8+ years in full-stack development. Led multiple teams and delivered scalable applications serving millions of users.",
        experiences=[
            CanonicalExperienceEntry(
                title="Senior Software Engineer",
                company="TechCorp Inc",
                date_range="2021-Present",
                description="Lead development of microservices architecture, mentor junior developers, reduced system latency by 40%"
            ),
            CanonicalExperienceEntry(
                title="Software Engineer",
                company="StartupXYZ",
                date_range="2018-2021",
                description="Built web applications with React/Node.js, implemented CI/CD pipelines, grew user base from 10K to 500K"
            )
        ],
        educations=[
            CanonicalEducationEntry(
                degree="Bachelor of Science",
                field_of_study="Computer Science",
                school="University of California, Berkeley",
                date_range="2014-2018"
            )
        ],
        connection_count=1250,
        follower_count=890,
        linkedin_url="https://linkedin.com/in/johndoe",
        timestamp=datetime.now()
    )


async def test_openai_integration():
    """Test OpenAI integration locally"""
    print("🧪 Testing V1.85 OpenAI Integration Locally")
    print("=" * 50)
    
    # Initialize the service
    print("1. Initializing LLM Scoring Service...")
    service = LLMScoringService()
    
    if not service.client:
        print("❌ OpenAI client not initialized - check OPENAI_API_KEY")
        return False
    
    print("✅ OpenAI client initialized successfully")
    
    # Create test profile
    print("\n2. Creating test profile...")
    profile = create_test_profile()
    print(f"✅ Test profile created: {profile.full_name} - {profile.job_title}")
    
    # Test profile to text conversion
    print("\n3. Converting profile to text...")
    profile_text = service.profile_to_text(profile)
    print(f"✅ Profile text generated ({len(profile_text)} characters)")
    print(f"   Preview: {profile_text[:200]}...")
    
    # Test token counting
    print("\n4. Testing token counting...")
    token_count = service.count_tokens(profile_text)
    print(f"✅ Profile tokens: {token_count}")
    
    # Test prompt formatting
    print("\n5. Testing prompt formatting...")
    test_prompt = "Rate this person as a potential CTO on a scale of 1-10 with detailed reasoning about their technical leadership experience."
    formatted_prompt = service.format_prompt(profile_text, test_prompt)
    total_tokens = service.count_tokens(formatted_prompt)
    print(f"✅ Complete prompt formatted ({total_tokens} total tokens)")
    
    # Test actual API call
    print("\n6. Testing OpenAI API call...")
    print("   Making request to OpenAI...")
    
    try:
        raw_response, parsed_score = await service.score_profile(
            profile=profile,
            prompt=test_prompt,
            model="gpt-3.5-turbo",
            max_tokens=500,
            temperature=0.1
        )
        
        print("✅ OpenAI API call successful!")
        print(f"   Model used: {raw_response.get('model', 'unknown')}")
        print(f"   Tokens used: {raw_response.get('usage', {}).get('total_tokens', 'unknown')}")
        print(f"   Response keys: {list(parsed_score.keys())}")
        
        # Display the actual score
        print("\n🎯 SCORING RESULT:")
        print("-" * 30)
        if 'score' in parsed_score:
            print(f"Score: {parsed_score['score']}")
        if 'rating' in parsed_score:
            print(f"Rating: {parsed_score['rating']}")
        if 'assessment' in parsed_score:
            print(f"Assessment: {parsed_score['assessment']}")
        if 'reasoning' in parsed_score:
            print(f"Reasoning: {parsed_score['reasoning']}")
            
        return True
        
    except Exception as e:
        print(f"❌ OpenAI API call failed: {e}")
        print(f"   Error type: {type(e).__name__}")
        return False


if __name__ == "__main__":
    print("Starting local OpenAI integration test...")
    print(f"OpenAI API Key configured: {'Yes' if os.getenv('OPENAI_API_KEY') else 'No'}")
    print()
    
    # Run the async test
    success = asyncio.run(test_openai_integration())
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 LOCAL TEST PASSED! OpenAI integration working correctly.")
        print("   Production deployment should work with this configuration.")
    else:
        print("❌ LOCAL TEST FAILED! Fix issues before production deployment.")
    
    print("=" * 50)
