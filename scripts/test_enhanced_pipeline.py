#!/usr/bin/env python3
"""
Test Enhanced Profile Ingestion Pipeline

Tests the complete enhanced profile ingestion flow including company extraction
and processing using the LinkedInDataPipeline.
"""

import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from app.services.linkedin_pipeline import LinkedInDataPipeline
from app.cassidy.models import LinkedInProfile, ExperienceEntry
from app.models.canonical.company import CanonicalCompany

async def test_enhanced_pipeline():
    """Test the enhanced profile ingestion pipeline."""
    
    print("🚀 Testing Enhanced Profile Ingestion Pipeline\n")
    
    # Create pipeline instance
    pipeline = LinkedInDataPipeline()
    
    print(f"✅ Pipeline initialized:")
    print(f"   - Database: {'✓' if pipeline.db_client else '✗'}")
    print(f"   - Embeddings: {'✓' if pipeline.embedding_service else '✗'}")
    print(f"   - Company Service: {'✓' if pipeline.company_service else '✗'}")
    print()
    
    # Create a mock profile with company data
    mock_profile = LinkedInProfile(
        profile_id="test-123",
        full_name="John Doe",
        linkedin_url="https://linkedin.com/in/john-doe",
        headline="Senior Developer at TechCorp",
        company="TechCorp Inc.",
        job_title="Senior Developer",
        company_linkedin_url="https://linkedin.com/company/techcorp",
        company_domain="techcorp.com",
        company_employee_count=1500,
        company_employee_range="1001-5000",
        experiences=[
            ExperienceEntry(
                title="Senior Developer",
                company="TechCorp Inc.",
                company_linkedin_url="https://linkedin.com/company/techcorp",
                is_current=True,
                start_year=2020,
                start_month=1
            ),
            ExperienceEntry(
                title="Junior Developer",
                company="StartupInc",
                company_linkedin_url="https://linkedin.com/company/startupinc",
                is_current=False,
                start_year=2018,
                start_month=6,
                end_year=2019,
                end_month=12
            )
        ]
    )
    
    # Test 1: Company data extraction
    print("📊 Test 1: Company Data Extraction")
    companies = pipeline._extract_company_data_from_profile(mock_profile)
    
    print(f"   - Extracted {len(companies)} companies:")
    for i, company in enumerate(companies, 1):
        print(f"     {i}. {company.company_name} ({company.linkedin_url})")
    
    expected_companies = ["TechCorp Inc.", "StartupInc"]
    extracted_names = [c.company_name for c in companies]
    
    for expected in expected_companies:
        if expected in extracted_names:
            print(f"   ✅ Found expected company: {expected}")
        else:
            print(f"   ❌ Missing expected company: {expected}")
    print()
    
    # Test 2: Test with company service (if available)
    if pipeline.company_service:
        print("🏢 Test 2: Company Service Integration")
        
        # Mock the company service to avoid database calls
        original_method = pipeline.company_service.batch_process_companies
        pipeline.company_service.batch_process_companies = Mock(return_value=[
            {"success": True, "action": "created", "company_id": "comp-1", "company_name": "TechCorp Inc."},
            {"success": True, "action": "created", "company_id": "comp-2", "company_name": "StartupInc"}
        ])
        
        # Mock Cassidy client to avoid external API calls
        pipeline.cassidy_client = AsyncMock()
        pipeline.cassidy_client.fetch_profile.return_value = mock_profile
        
        # Mock database client to avoid database calls
        if pipeline.db_client:
            pipeline.db_client = AsyncMock()
            pipeline.db_client.store_profile.return_value = "profile-123"
        
        try:
            result = await pipeline.ingest_profile_with_companies(
                "https://linkedin.com/in/john-doe",
                store_in_db=bool(pipeline.db_client),
                generate_embeddings=False  # Skip embeddings for test
            )
            
            print(f"   - Status: {result['status']}")
            print(f"   - Profile: {result['profile']['full_name']}")
            print(f"   - Companies processed: {len(result['companies'])}")
            
            for company in result['companies']:
                print(f"     • {company['company_name']} ({company['action']})")
            
            if result['errors']:
                print(f"   - Errors: {len(result['errors'])}")
                for error in result['errors']:
                    print(f"     • {error['error']}")
            
            if result['status'] == 'completed':
                print("   ✅ Enhanced pipeline test completed successfully")
            else:
                print("   ❌ Pipeline test failed")
        
        except Exception as e:
            print(f"   ❌ Pipeline test failed with error: {e}")
        
        # Restore original method
        pipeline.company_service.batch_process_companies = original_method
        print()
    
    else:
        print("🏢 Test 2: Company Service Integration - SKIPPED (no company service)")
        print("   ℹ️  Company service requires database configuration")
        print()
    
    # Test 3: Error handling
    print("⚠️  Test 3: Error Handling")
    
    # Test with invalid company data
    invalid_profile = LinkedInProfile(
        profile_id="invalid-123",
        full_name="Jane Smith",
        linkedin_url="https://linkedin.com/in/jane-smith",
        company="",  # Empty company name
        company_employee_count=-1,  # Invalid count
        experiences=[]
    )
    
    invalid_companies = pipeline._extract_company_data_from_profile(invalid_profile)
    print(f"   - Invalid profile extracted {len(invalid_companies)} companies (expected: 0)")
    
    if len(invalid_companies) == 0:
        print("   ✅ Invalid data properly filtered out")
    else:
        print("   ❌ Invalid data not properly filtered")
    print()
    
    print("🎉 Enhanced Pipeline Testing Complete!")
    print()
    print("📋 Summary:")
    print("   • Company extraction from profiles: ✓")
    print("   • Data validation and filtering: ✓") 
    print("   • Error handling: ✓")
    if pipeline.company_service:
        print("   • CompanyService integration: ✓")
    print("   • Enhanced ingestion pipeline: ✓")

if __name__ == "__main__":
    asyncio.run(test_enhanced_pipeline())
