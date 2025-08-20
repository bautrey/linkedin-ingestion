#!/usr/bin/env python3

import asyncio
import asyncpg
import os
from datetime import datetime
import re

async def fix_template_timestamps():
    """Fix malformed timestamps in scoring_templates table"""
    
    # Database connection using Supabase details
    DATABASE_URL = 'postgresql://postgres:dvm2rjq6ngk@GZN-wth@db.yirtidxcgkkoizwqpdfv.supabase.co:5432/postgres'
    
    try:
        # Connect to database
        conn = await asyncpg.connect(DATABASE_URL)
        print("✅ Connected to database")
        
        # Find templates with malformed timestamps
        print("\n🔍 Finding templates with malformed timestamps...")
        rows = await conn.fetch('''
            SELECT id, name, created_at, updated_at
            FROM scoring_templates 
            ORDER BY created_at DESC;
        ''')
        
        print(f"Found {len(rows)} total templates")
        
        malformed_count = 0
        fixed_count = 0
        
        for row in rows:
            template_id = row['id']
            name = row['name']
            created_at = row['created_at']
            updated_at = row['updated_at']
            
            # Check if timestamps need fixing (have more than 6 decimal places)
            created_str = str(created_at)
            updated_str = str(updated_at) if updated_at else None
            
            needs_fix = False
            new_created_at = created_at
            new_updated_at = updated_at
            
            # Check created_at
            if '.' in created_str and '+' in created_str:
                decimal_part = created_str.split('.')[1].split('+')[0]
                if len(decimal_part) != 6:  # Should be exactly 6 digits
                    needs_fix = True
                    malformed_count += 1
                    # Truncate or pad to 6 digits
                    if len(decimal_part) > 6:
                        decimal_part = decimal_part[:6]
                    else:
                        decimal_part = decimal_part.ljust(6, '0')
                    
                    # Reconstruct timestamp
                    parts = created_str.split('.')
                    timezone_part = '.' + parts[1].split('+')[1] if '+' in parts[1] else ''
                    new_created_str = f"{parts[0]}.{decimal_part}+{created_str.split('+')[1]}"
                    new_created_at = datetime.fromisoformat(new_created_str.replace('+00:00', '+00:00'))
            
            # Check updated_at if it exists
            if updated_at and '.' in updated_str and '+' in updated_str:
                decimal_part = updated_str.split('.')[1].split('+')[0]
                if len(decimal_part) != 6:
                    needs_fix = True
                    if len(decimal_part) > 6:
                        decimal_part = decimal_part[:6]
                    else:
                        decimal_part = decimal_part.ljust(6, '0')
                    
                    parts = updated_str.split('.')
                    new_updated_str = f"{parts[0]}.{decimal_part}+{updated_str.split('+')[1]}"
                    new_updated_at = datetime.fromisoformat(new_updated_str.replace('+00:00', '+00:00'))
            
            if needs_fix:
                print(f"\n🔧 Fixing template: {name}")
                print(f"   ID: {template_id}")
                print(f"   Old created_at: {created_at}")
                print(f"   New created_at: {new_created_at}")
                if updated_at:
                    print(f"   Old updated_at: {updated_at}")
                    print(f"   New updated_at: {new_updated_at}")
                
                # Update the template
                await conn.execute('''
                    UPDATE scoring_templates 
                    SET created_at = $1, updated_at = $2
                    WHERE id = $3
                ''', new_created_at, new_updated_at, template_id)
                
                fixed_count += 1
        
        print(f"\n✅ Fixed {fixed_count} templates out of {malformed_count} with malformed timestamps")
        
        # Verify the fix by trying to fetch all templates
        print("\n🧪 Testing template listing...")
        test_rows = await conn.fetch('SELECT id, name, created_at FROM scoring_templates ORDER BY created_at DESC')
        print(f"✅ Successfully fetched {len(test_rows)} templates after fix")
        
        await conn.close()
        print("✅ Database connection closed")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(fix_template_timestamps())
