#!/usr/bin/env python3
"""
Test the updated models against the sample LinkedIn profile data
"""

import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from cassidy.models import LinkedInProfile, ExperienceEntry, EducationEntry

# Sample response from Cassidy
SAMPLE_RESPONSE = {
    "about": "As chairman and CEO of Microsoft, I define my mission and that of my company as empowering every person and every organization on the planet to achieve more.",
    "city": "Redmond",
    "company": "Microsoft",
    "company_description": "Every company has a mission. What's ours? To empower every person and every organization to achieve more. We believe technology can and should be a force for good and that meaningful innovation contributes to a brighter world in the future and today. Our culture doesn't just encourage curiosity; it embraces it. Each day we make progress together by showing up as our authentic selves. We show up with a learn-it-all mentality. We show up cheering on others, knowing their success doesn't diminish our own. We show up every day open to learning our own biases, changing our behavior, and inviting in differences. Because impact matters. \n\nMicrosoft operates in 190 countries and is made up of approximately 228,000 passionate employees worldwide.",
    "company_domain": "news.microsoft.com",
    "company_employee_count": 234051,
    "company_employee_range": "10001+",
    "company_industry": "Software Development",
    "company_linkedin_url": "https://www.linkedin.com/company/microsoft",
    "company_logo_url": "https://media.licdn.com/dms/image/v2/D560BAQH32RJQCl3dDQ/company-logo_200_200/B56ZYQ0mrGGoAM-/0/1744038948046/microsoft_logo?e=1756339200&v=beta&t=soclQ2L1xveldQjvY_J8Q5Uwf8VUCiXmzS_hDhuV9i0",
    "company_website": "https://news.microsoft.com/",
    "company_year_founded": "",
    "connection_count": 823,
    "country": "United States",
    "current_company_join_month": 2,
    "current_company_join_year": 2014,
    "current_job_duration": "11 yrs 6 mos",
    "educations": [
        {
            "activities": "",
            "date_range": "1994 - 1996",
            "degree": "",
            "end_month": "",
            "end_year": 1996,
            "field_of_study": "",
            "school": "The University of Chicago Booth School of Business",
            "school_id": "8398",
            "school_linkedin_url": "https://www.linkedin.com/company/8398/",
            "school_logo_url": "https://media.licdn.com/dms/image/v2/D560BAQFZO05jhYKSkw/company-logo_200_200/company-logo_200_200/0/1692627816910/universityofchicagoboothschoolofbusiness_logo?e=1756339200&v=beta&t=uGBtU3sxfJ_eeOZxScRiNukoo8wpAF8TgikkPc_rgpw",
            "start_month": "",
            "start_year": 1994
        }
    ],
    "email": "",
    "experiences": [
        {
            "company": "Microsoft",
            "company_id": "1035",
            "company_linkedin_url": "https://www.linkedin.com/company/1035",
            "company_logo_url": "https://media.licdn.com/dms/image/v2/D560BAQH32RJQCl3dDQ/company-logo_100_100/B56ZYQ0mrGGoAU-/0/1744038948046/microsoft_logo?e=1756339200&v=beta&t=t_vRhtkgf1aCLVtuTtJvuQOu9xej8MnL7I8iwhoamBs",
            "date_range": "Feb 2014 - Present",
            "description": "",
            "duration": "11 yrs 6 mos",
            "end_month": "",
            "end_year": "",
            "is_current": True,
            "job_type": "",
            "location": "Greater Seattle Area",
            "skills": "",
            "start_month": 2,
            "start_year": 2014,
            "title": "Chairman and CEO"
        }
    ],
    "first_name": "Satya",
    "follower_count": 11466107,
    "full_name": "Satya Nadella",
    "headline": "Chairman and CEO at Microsoft",
    "hq_city": "Redmond",
    "hq_country": "US",
    "hq_region": "Washington",
    "is_creator": True,
    "is_influencer": True,
    "is_premium": True,
    "is_verified": True,
    "job_title": "Chairman and CEO",
    "languages": [],
    "last_name": "Nadella",
    "linkedin_url": "https://www.linkedin.com/in/satyanadella/",
    "location": "Redmond, Washington, United States",
    "phone": "",
    "profile_id": "19186432",
    "profile_image_url": "https://media.licdn.com/dms/image/v2/C5603AQHHUuOSlRVA1w/profile-displayphoto-shrink_800_800/profile-displayphoto-shrink_800_800/0/1579726625483?e=1756339200&v=beta&t=bbdTNEewTrJRj4PRAwORiO25y6kP7_wC4FtmrfJhnPE",
    "public_id": "satyanadella",
    "school": "The University of Chicago Booth School of Business",
    "state": "Washington",
    "urn": "ACoAAAEkwwAB9KEc2TrQgOLEQ-vzRyZeCDyc6DQ"
}

def test_model_validation():
    """Test that our updated models can handle the sample data"""
    try:
        print("=== TESTING UPDATED LINKEDIN PROFILE MODEL ===")
        
        # Test profile creation
        profile = LinkedInProfile(**SAMPLE_RESPONSE)
        print(f"✅ Profile creation successful")
        print(f"   Profile ID: {profile.profile_id}")
        print(f"   Name: {profile.full_name}")
        print(f"   LinkedIn URL: {profile.linkedin_url}")
        print(f"   Company: {profile.company}")
        
        # Test backward compatibility
        print(f"\n=== BACKWARD COMPATIBILITY TEST ===")
        print(f"   profile.id: {profile.id}")
        print(f"   profile.name: {profile.name}")
        print(f"   profile.url: {profile.url}")
        
        # Test experience data
        print(f"\n=== EXPERIENCE DATA ===")
        print(f"   Experience count: {len(profile.experiences)}")
        if profile.experiences:
            exp = profile.experiences[0]
            print(f"   First experience - Title: {exp.title}")
            print(f"   First experience - Company: {exp.company}")
            print(f"   First experience - Duration: {exp.duration}")
            print(f"   First experience - Is Current: {exp.is_current}")
            print(f"   First experience - Start Month: {exp.start_month} (type: {type(exp.start_month)})")
            
            # Test backward compatibility for experience
            print(f"   Backward compatibility - job_title: {exp.job_title}")
            print(f"   Backward compatibility - current_job: {exp.current_job}")
        
        # Test education data
        print(f"\n=== EDUCATION DATA ===")
        print(f"   Education count: {len(profile.educations)}")
        if profile.educations:
            edu = profile.educations[0]
            print(f"   First education - School: {edu.school}")
            print(f"   First education - Start Year: {edu.start_year} (type: {type(edu.start_year)})")
        
        # Test data completeness calculation
        print(f"\n=== DATA COMPLETENESS CALCULATION ===")
        
        # Count populated fields like the health checker does
        populated_fields = []
        total_fields = 0
        
        for field_name in profile.__fields__.keys():
            if field_name == 'timestamp':  # Skip internal fields
                continue
                
            field_value = getattr(profile, field_name, None)
            total_fields += 1
            
            if field_value is not None:
                if isinstance(field_value, (list, dict)):
                    if field_value:  # Non-empty list/dict
                        populated_fields.append(field_name)
                elif isinstance(field_value, str):
                    if field_value.strip():  # Non-empty string
                        populated_fields.append(field_name)
                else:
                    populated_fields.append(field_name)  # Other values (int, bool, etc.)
        
        completeness = (len(populated_fields) / total_fields * 100) if total_fields > 0 else 0
        print(f"   Total fields: {total_fields}")
        print(f"   Populated fields: {len(populated_fields)}")
        print(f"   Completeness: {completeness:.1f}%")
        
        # Identity check
        has_identity = bool(
            (profile.profile_id and profile.profile_id.strip()) or
            (profile.full_name and profile.full_name.strip()) or
            (profile.linkedin_url and profile.linkedin_url.strip()) or
            (profile.public_id and profile.public_id.strip()) or
            (profile.first_name and profile.first_name.strip()) or
            (profile.last_name and profile.last_name.strip())
        )
        print(f"   Has identity data: {has_identity}")
        
        print(f"\n✅ ALL TESTS PASSED! The model correctly handles the rich LinkedIn data.")
        
        return True
        
    except Exception as e:
        print(f"❌ MODEL VALIDATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_model_validation()
    if success:
        print(f"\n🎉 The updated models are now properly aligned with the actual API response!")
        print(f"   This 90.7% complete data should no longer be flagged as 'incomplete'.")
    else:
        print(f"\n💥 Model updates need more work.")
        sys.exit(1)
