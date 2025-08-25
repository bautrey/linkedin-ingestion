#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.template_service import TemplateService

def test_datetime_parsing():
    """Test the new datetime parsing functionality"""
    
    # Create a dummy template service (we won't use the client)
    service = TemplateService(supabase_client=None)
    
    test_cases = [
        "2025-08-24T14:07:11.9449+00:00",  # 4 digit microseconds (the problem case)
        "2025-08-24T14:07:11.944900+00:00",  # 6 digit microseconds (standard)
        "2025-08-24T14:07:11.94+00:00",  # 2 digit microseconds
        "2025-08-24T14:07:11.9+00:00",   # 1 digit microseconds
        "2025-08-24T14:07:11+00:00",     # No microseconds
        "2025-08-24T14:07:11.123456789+00:00",  # 9 digit microseconds (too many)
        "2025-08-24T14:07:11Z",          # Z timezone
        "2025-08-24T14:07:11.9449Z",     # Z timezone with microseconds
    ]
    
    print("Testing datetime parsing...")
    
    for i, test_str in enumerate(test_cases):
        try:
            parsed = service._parse_datetime(test_str)
            print(f"✅ Test {i+1}: '{test_str}' -> {parsed}")
        except Exception as e:
            print(f"❌ Test {i+1}: '{test_str}' -> ERROR: {e}")
    
    print("\nAll datetime parsing tests completed!")

if __name__ == "__main__":
    test_datetime_parsing()
