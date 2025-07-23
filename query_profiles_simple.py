#!/usr/bin/env python3
"""
Simple script to query recent LinkedIn profiles from Supabase
Bypasses the numpy dependency issue by using supabase client directly
"""

import os
from supabase import create_client
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def query_recent_profiles():
    """Query recent profiles directly from Supabase"""
    
    # Get Supabase credentials from environment
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_ANON_KEY')
    
    if not url or not key:
        print("❌ Missing Supabase credentials in environment variables")
        print("   Set SUPABASE_URL and SUPABASE_ANON_KEY")
        return
    
    try:
        # Create client
        supabase = create_client(url, key)
        
        print("🔍 Querying recent LinkedIn profiles from Supabase...")
        print("=" * 60)
        
        # Query recent profiles
        result = supabase.table("linkedin_profiles").select(
            "name, position, city, country_code, followers, connections, "
            "linkedin_id, created_at, experience, education"
        ).order("created_at", desc=True).limit(10).execute()
        
        profiles = result.data
        
        if not profiles:
            print("📭 No profiles found in database")
            return
        
        print(f"✅ Found {len(profiles)} recent profiles")
        print()
        
        # Display profile summaries
        for i, profile in enumerate(profiles, 1):
            print(f"Profile {i}:")
            print(f"  Name: {profile.get('name', 'N/A')}")
            print(f"  Position: {profile.get('position', 'N/A')}")
            print(f"  Location: {profile.get('city', 'N/A')}, {profile.get('country_code', 'N/A')}")
            
            # Format numbers with commas
            followers = profile.get('followers')
            connections = profile.get('connections')
            print(f"  Followers: {followers:,}" if followers else "  Followers: N/A")
            print(f"  Connections: {connections:,}" if connections else "  Connections: N/A")
            
            # Count experience and education items
            experience_count = len(profile.get('experience', []))
            education_count = len(profile.get('education', []))
            print(f"  Experience: {experience_count} items")
            print(f"  Education: {education_count} items")
            
            # Show creation date
            created_at = profile.get('created_at')
            if created_at:
                try:
                    # Parse ISO timestamp
                    dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    print(f"  Stored: {dt.strftime('%Y-%m-%d %H:%M:%S')} UTC")
                except:
                    print(f"  Stored: {created_at}")
            
            print()
        
        # Summary statistics
        print("=" * 60)
        print("📊 Summary Statistics:")
        print(f"  Total Profiles: {len(profiles)}")
        
        # Calculate averages where data exists
        followers_data = [p.get('followers') for p in profiles if p.get('followers')]
        connections_data = [p.get('connections') for p in profiles if p.get('connections')]
        
        if followers_data:
            avg_followers = sum(followers_data) / len(followers_data)
            print(f"  Average Followers: {avg_followers:,.0f}")
        
        if connections_data:
            avg_connections = sum(connections_data) / len(connections_data)
            print(f"  Average Connections: {avg_connections:,.0f}")
        
        # Count profiles by location
        cities = [p.get('city') for p in profiles if p.get('city')]
        if cities:
            from collections import Counter
            city_counts = Counter(cities)
            print(f"  Top Cities: {dict(city_counts.most_common(3))}")
        
        print()
        print("🎯 Data Quality Assessment:")
        complete_profiles = sum(1 for p in profiles if all([
            p.get('name'),
            p.get('position'),
            p.get('city'),
            len(p.get('experience', [])) > 0
        ]))
        print(f"  Complete Profiles: {complete_profiles}/{len(profiles)} ({complete_profiles/len(profiles)*100:.1f}%)")
        
    except Exception as e:
        print(f"❌ Error querying profiles: {e}")
        print(f"   Error type: {type(e).__name__}")

def query_companies():
    """Query companies from Supabase"""
    
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_ANON_KEY')
    
    if not url or not key:
        return
    
    try:
        supabase = create_client(url, key)
        
        print("🏢 Querying companies from Supabase...")
        print("=" * 60)
        
        result = supabase.table("companies").select(
            "company_name, description, employee_count, employee_range, "
            "year_founded, industries, hq_city, hq_country, created_at"
        ).order("created_at", desc=True).limit(5).execute()
        
        companies = result.data
        
        if not companies:
            print("📭 No companies found in database")
            return
        
        print(f"✅ Found {len(companies)} recent companies")
        print()
        
        for i, company in enumerate(companies, 1):
            print(f"Company {i}:")
            print(f"  Name: {company.get('company_name', 'N/A')}")
            print(f"  HQ: {company.get('hq_city', 'N/A')}, {company.get('hq_country', 'N/A')}")
            
            employee_count = company.get('employee_count')
            employee_range = company.get('employee_range')
            if employee_count:
                print(f"  Employees: {employee_count:,}")
            elif employee_range:
                print(f"  Employee Range: {employee_range}")
            
            founded = company.get('year_founded')
            if founded:
                print(f"  Founded: {founded}")
            
            industries = company.get('industries', [])
            if industries:
                print(f"  Industries: {', '.join(industries[:3])}")
            
            desc = company.get('description', '')
            if desc:
                preview = desc[:100] + "..." if len(desc) > 100 else desc
                print(f"  Description: {preview}")
            
            print()
        
    except Exception as e:
        print(f"❌ Error querying companies: {e}")

if __name__ == "__main__":
    print("🧪 LinkedIn Ingestion - Supabase Data Summary")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    query_recent_profiles()
    print()
    query_companies()
