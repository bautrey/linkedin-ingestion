"""
Tests for URL normalization in ProfileIngestionRequest model
"""

import pytest
from app.cassidy.models import ProfileIngestionRequest


class TestURLNormalization:
    """Test URL normalization in ProfileIngestionRequest"""

    def test_urls_without_protocol_are_normalized(self):
        """Test that URLs without protocol are normalized with https://"""
        
        test_cases = [
            ("www.linkedin.com/in/reginaldacloque", "https://www.linkedin.com/in/reginaldacloque"),
            ("linkedin.com/in/testuser", "https://linkedin.com/in/testuser"),
            ("www.linkedin.com/in/john-doe", "https://www.linkedin.com/in/john-doe"),
            ("linkedin.com/company/test-company", "https://linkedin.com/company/test-company")
        ]
        
        for input_url, expected_url in test_cases:
            request = ProfileIngestionRequest(linkedin_url=input_url)
            assert str(request.linkedin_url) == expected_url
    
    def test_urls_with_protocol_unchanged(self):
        """Test that URLs with protocol are not modified"""
        
        test_cases = [
            "https://www.linkedin.com/in/reginaldacloque",
            "http://linkedin.com/in/testuser",
            "https://linkedin.com/in/john-doe"
        ]
        
        for url in test_cases:
            request = ProfileIngestionRequest(linkedin_url=url)
            assert str(request.linkedin_url) == url
    
    def test_whitespace_is_trimmed(self):
        """Test that whitespace is trimmed during normalization"""
        
        test_cases = [
            ("  www.linkedin.com/in/test  ", "https://www.linkedin.com/in/test"),
            ("\tlinkedin.com/in/user\n", "https://linkedin.com/in/user")
        ]
        
        for input_url, expected_url in test_cases:
            request = ProfileIngestionRequest(linkedin_url=input_url)
            assert str(request.linkedin_url) == expected_url
    
    def test_non_linkedin_urls_unchanged(self):
        """Test that non-LinkedIn URLs without protocol are not normalized"""
        
        # URLs that don't contain 'linkedin.com' should not be auto-prefixed
        # (though they may still fail HttpUrl validation for other reasons)
        test_url = "https://example.com/profile"
        request = ProfileIngestionRequest(linkedin_url=test_url)
        assert str(request.linkedin_url) == test_url
