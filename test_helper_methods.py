#!/usr/bin/env python3
"""
Test script to validate the helper methods integration in ProfileController
"""

import asyncio
import sys
from unittest.mock import Mock, AsyncMock
from typing import List

# Add the app to the path
sys.path.insert(0, '.')

def test_helper_methods_exist():
    """Test that helper methods exist in ProfileController"""
    try:
        from main import ProfileController
        
        # Create mock dependencies
        mock_db_client = Mock()
        mock_cassidy_client = Mock()
        mock_linkedin_workflow = Mock()
        
        # Initialize controller
        controller = ProfileController(
            db_client=mock_db_client,
            cassidy_client=mock_cassidy_client,
            linkedin_workflow=mock_linkedin_workflow
        )
        
        # Check methods exist
        assert hasattr(controller, '_extract_company_urls_from_profile'), "Missing _extract_company_urls_from_profile method"
        assert hasattr(controller, '_fetch_companies_from_cassidy'), "Missing _fetch_companies_from_cassidy method"
        
        print("✓ Helper methods exist in ProfileController")
        return True
        
    except Exception as e:
        print(f"✗ Error testing helper methods: {str(e)}")
        return False

def test_extract_company_urls_from_profile():
    """Test _extract_company_urls_from_profile method with mock profile"""
    try:
        from main import ProfileController
        
        # Create mock dependencies
        mock_db_client = Mock()
        mock_cassidy_client = Mock()
        mock_linkedin_workflow = Mock()
        
        # Initialize controller
        controller = ProfileController(
            db_client=mock_db_client,
            cassidy_client=mock_cassidy_client,
            linkedin_workflow=mock_linkedin_workflow
        )
        
        # Create mock profile with experience
        mock_experience = Mock()
        mock_experience.company_linkedin_url = "https://www.linkedin.com/company/test-company"
        
        mock_profile = Mock()
        mock_profile.experience = [mock_experience]
        mock_profile.current_company = None
        
        # Test the method
        result = controller._extract_company_urls_from_profile(mock_profile)
        
        assert isinstance(result, list), "Method should return a list"
        assert len(result) == 1, "Should find one company URL"
        assert result[0] == "https://www.linkedin.com/company/test-company", "Should return the correct URL"
        
        print("✓ _extract_company_urls_from_profile works correctly")
        return True
        
    except Exception as e:
        print(f"✗ Error testing _extract_company_urls_from_profile: {str(e)}")
        return False

async def test_fetch_companies_from_cassidy():
    """Test _fetch_companies_from_cassidy method with mock cassidy client"""
    try:
        from main import ProfileController
        
        # Create mock dependencies
        mock_db_client = Mock()
        mock_cassidy_client = AsyncMock()
        mock_linkedin_workflow = Mock()
        
        # Mock company response
        mock_company = Mock()
        mock_company.company_name = "Test Company"
        mock_cassidy_client.fetch_company.return_value = mock_company
        
        # Initialize controller
        controller = ProfileController(
            db_client=mock_db_client,
            cassidy_client=mock_cassidy_client,
            linkedin_workflow=mock_linkedin_workflow
        )
        
        # Test the method
        company_urls = ["https://www.linkedin.com/company/test-company"]
        result = await controller._fetch_companies_from_cassidy(company_urls)
        
        assert isinstance(result, list), "Method should return a list"
        assert len(result) == 1, "Should return one company"
        assert result[0].company_name == "Test Company", "Should return the correct company"
        
        print("✓ _fetch_companies_from_cassidy works correctly")
        return True
        
    except Exception as e:
        print(f"✗ Error testing _fetch_companies_from_cassidy: {str(e)}")
        return False

def test_create_profile_calls_helper_methods():
    """Test that create_profile method references the helper methods"""
    try:
        # Read main.py to check method calls
        with open('main.py', 'r') as f:
            content = f.read()
        
        # Check that create_profile method calls our helper methods
        create_profile_section = None
        lines = content.split('\n')
        in_create_profile = False
        create_profile_lines = []
        
        for line in lines:
            if 'async def create_profile(' in line:
                in_create_profile = True
                continue
            elif in_create_profile and line.strip().startswith('async def ') or line.strip().startswith('def '):
                break
            elif in_create_profile:
                create_profile_lines.append(line)
        
        create_profile_section = '\n'.join(create_profile_lines)
        
        assert 'self._extract_company_urls_from_profile(' in create_profile_section, "create_profile should call _extract_company_urls_from_profile"
        assert 'await self._fetch_companies_from_cassidy(' in create_profile_section, "create_profile should call _fetch_companies_from_cassidy"
        
        print("✓ create_profile method correctly calls helper methods")
        return True
        
    except Exception as e:
        print(f"✗ Error testing create_profile integration: {str(e)}")
        return False

async def main():
    """Run all tests"""
    print("Testing ProfileController helper methods integration...\n")
    
    tests = [
        test_helper_methods_exist(),
        test_extract_company_urls_from_profile(),
        await test_fetch_companies_from_cassidy(),
        test_create_profile_calls_helper_methods()
    ]
    
    passed = sum(tests)
    total = len(tests)
    
    print(f"\nTest Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Helper methods are properly integrated.")
        return True
    else:
        print(f"❌ {total - passed} tests failed.")
        return False

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
