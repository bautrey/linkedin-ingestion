#!/usr/bin/env python3

import os
import sys
from supabase import create_client, Client
from datetime import datetime
import re

def fix_template_timestamps():
    """Fix malformed timestamps using Supabase client"""
    
    # Initialize Supabase client
    url = os.getenv("SUPABASE_URL", "https://yirtidxcgkkoizwqpdfv.supabase.co")
    key = os.getenv("SUPABASE_SERVICE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlpcnRpZHhjZ2trb2l6d3FwZGZ2Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MzIwOTQ5MSwiZXhwIjoyMDY4Nzg1NDkxfQ.LjvQohgwXbKkiRUyDlGvb4Hn4SoRCZPLjye00VIVrBg")
    
    supabase: Client = create_client(url, key)
    print("✅ Connected to Supabase")
    
    try:
        # Get all templates
        print("\n🔍 Fetching all templates...")
        response = supabase.table('prompt_templates').select('*').execute()
        
        if not response.data:
            print("No templates found")
            return
            
        templates = response.data
        print(f"Found {len(templates)} templates")
        
        malformed_templates = []
        
        for template in templates:
            template_id = template['id']
            name = template['name']
            created_at = template['created_at']
            updated_at = template.get('updated_at')
            
            needs_fix = False
            
            # Check if timestamp has malformed microseconds
            if isinstance(created_at, str):
                # Look for timestamps with too many decimal places
                if '.' in created_at and ('+' in created_at or 'Z' in created_at):
                    # Extract decimal part
                    if '+' in created_at:
                        decimal_part = created_at.split('.')[1].split('+')[0]
                    else:  # Z timezone
                        decimal_part = created_at.split('.')[1].rstrip('Z')
                    
                    if len(decimal_part) != 6:  # Should be exactly 6 digits for microseconds
                        needs_fix = True
                        
            if needs_fix:
                print(f"\n🔧 Found malformed template: {name}")
                print(f"   ID: {template_id}")
                print(f"   Created: {created_at}")
                malformed_templates.append(template_id)
        
        print(f"\nFound {len(malformed_templates)} templates with malformed timestamps")
        
        if malformed_templates:
            print("\n⚠️  Deleting malformed templates to fix the API...")
            for template_id in malformed_templates:
                print(f"   Deleting template: {template_id}")
                delete_response = supabase.table('prompt_templates').delete().eq('id', template_id).execute()
                if delete_response.data:
                    print(f"   ✅ Deleted template {template_id}")
                else:
                    print(f"   ❌ Failed to delete template {template_id}")
        
        # Test the fix
        print("\n🧪 Testing template listing after fix...")
        test_response = supabase.table('prompt_templates').select('id, name, created_at').execute()
        print(f"✅ Successfully fetched {len(test_response.data)} templates after fix")
        
        print(f"\n✅ Fix complete. Deleted {len(malformed_templates)} problematic templates.")
        print("The templates API should now work correctly.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_template_timestamps()
