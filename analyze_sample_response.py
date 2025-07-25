#!/usr/bin/env python3
"""
Analyze the sample LinkedIn profile response to understand what fields we're getting
vs what we're expecting in our model
"""

import json
from typing import Dict, Any

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
        },
        {
            "activities": "",
            "date_range": "",
            "degree": "Bachelor's Degree",
            "end_month": "",
            "end_year": "",
            "field_of_study": "Electrical Engineering",
            "school": "Manipal Institute of Technology",
            "school_id": "577550",
            "school_linkedin_url": "https://www.linkedin.com/company/577550/",
            "school_logo_url": "https://media.licdn.com/dms/image/v2/C510BAQH66KkTTZFJ2A/company-logo_200_200/company-logo_200_200/0/1630615963889/manipal_institute_of_technology_logo?e=1756339200&v=beta&t=8tghnJhD_SBGqb4JQslULT3fU5i4WFmzqgbIWM1ChOA",
            "start_month": "",
            "start_year": ""
        },
        {
            "activities": "",
            "date_range": "",
            "degree": "Master's Degree",
            "end_month": "",
            "end_year": "",
            "field_of_study": "Computer Science",
            "school": "University of Wisconsin-Milwaukee",
            "school_id": "166690",
            "school_linkedin_url": "https://www.linkedin.com/company/166690/",
            "school_logo_url": "https://media.licdn.com/dms/image/v2/D4D0BAQE47QlO_LG8SQ/company-logo_200_200/company-logo_200_200/0/1729615751602/uwmilwaukee_logo?e=1756339200&v=beta&t=ZEG3YDFVIb_ZZLM1V3taRPVHyp_5KevgaVJ4az-dKSs",
            "start_month": "",
            "start_year": ""
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
        },
        {
            "company": "University of Chicago",
            "company_id": "3881",
            "company_linkedin_url": "https://www.linkedin.com/company/3881",
            "company_logo_url": "https://media.licdn.com/dms/image/v2/C4D0BAQHbp_dv8CAlpQ/company-logo_200_200/company-logo_200_200/0/1630577480920/uchicago_logo?e=1756339200&v=beta&t=pfw1KMPeWBtwza7Aqcx_0QKi7Nn6VwSAkNcZTiTg1YE",
            "date_range": "2018 - Present",
            "description": "",
            "duration": "7 yrs 7 mos",
            "end_month": "",
            "end_year": "",
            "is_current": True,
            "job_type": "",
            "location": "",
            "skills": "",
            "start_month": "",
            "start_year": 2018,
            "title": "Member Board Of Trustees"
        },
        {
            "company": "Starbucks",
            "company_id": "2271",
            "company_linkedin_url": "https://www.linkedin.com/company/2271",
            "company_logo_url": "https://media.licdn.com/dms/image/v2/C4D0BAQEQxk9y2rk7Hw/company-logo_200_200/company-logo_200_200/0/1631316692275?e=1756339200&v=beta&t=jHiQ-8SaqDWnGVQt1PuYWzYZXGz7ifpfUhVtIgCgp9s",
            "date_range": "2017 - 2024",
            "description": "",
            "duration": "7 yrs",
            "end_month": "",
            "end_year": 2024,
            "is_current": False,
            "job_type": "",
            "location": "",
            "skills": "",
            "start_month": "",
            "start_year": 2017,
            "title": "Board Member"
        },
        {
            "company": "The Business Council U.S.",
            "company_id": "5301945",
            "company_linkedin_url": "https://www.linkedin.com/company/5301945",
            "company_logo_url": "https://media.licdn.com/dms/image/v2/C4D0BAQGcnaZNpjMvrw/company-logo_200_200/company-logo_200_200/0/1630557702704/the_business_council_us_logo?e=1756339200&v=beta&t=Xn4n3SgYJYWJ1-LttTZR8_eXx48LOHUxk4HKv96x1dE",
            "date_range": "2021 - 2023",
            "description": "",
            "duration": "2 yrs",
            "end_month": "",
            "end_year": 2023,
            "is_current": False,
            "job_type": "",
            "location": "",
            "skills": "",
            "start_month": "",
            "start_year": 2021,
            "title": "Chairman"
        },
        {
            "company": "Fred Hutch",
            "company_id": "7158",
            "company_linkedin_url": "https://www.linkedin.com/company/7158",
            "company_logo_url": "https://media.licdn.com/dms/image/v2/D4D0BAQGF4eOou62nvQ/company-logo_200_200/company-logo_200_200/0/1664795263764/fredhutch_logo?e=1756339200&v=beta&t=bVrKW3Rae0HHYI7C7jbrRjHlx_uLIPZZzO4QMC8a24w",
            "date_range": "2016 - 2022",
            "description": "",
            "duration": "6 yrs",
            "end_month": "",
            "end_year": 2022,
            "is_current": False,
            "job_type": "",
            "location": "",
            "skills": "",
            "start_month": "",
            "start_year": 2016,
            "title": "Board Member"
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

def analyze_response():
    """Analyze the sample response structure"""
    print("=== LINKEDIN PROFILE RESPONSE ANALYSIS ===\n")
    
    # Count total fields
    total_fields = len(SAMPLE_RESPONSE)
    print(f"Total fields in response: {total_fields}")
    
    # Categorize fields
    non_empty_fields = []
    empty_string_fields = []
    empty_list_fields = []
    populated_fields = []
    
    for field, value in SAMPLE_RESPONSE.items():
        if value is None:
            continue
        elif isinstance(value, str):
            if value.strip():
                non_empty_fields.append(field)
                populated_fields.append(field)
            else:
                empty_string_fields.append(field)
        elif isinstance(value, list):
            if value:
                non_empty_fields.append(field)
                populated_fields.append(field)
            else:
                empty_list_fields.append(field)
        else:
            non_empty_fields.append(field)
            populated_fields.append(field)
    
    print(f"Fields with meaningful data: {len(populated_fields)} ({len(populated_fields)/total_fields*100:.1f}%)")
    print(f"Empty string fields: {len(empty_string_fields)}")
    print(f"Empty list fields: {len(empty_list_fields)}")
    
    print("\n=== FIELD CATEGORIES ===")
    
    print(f"\nPopulated fields ({len(populated_fields)}):")
    for field in sorted(populated_fields):
        value = SAMPLE_RESPONSE[field]
        if isinstance(value, str):
            preview = value[:50] + "..." if len(value) > 50 else value
            print(f"  {field}: '{preview}'")
        elif isinstance(value, list):
            print(f"  {field}: [{len(value)} items]")
        else:
            print(f"  {field}: {value}")
    
    print(f"\nEmpty string fields ({len(empty_string_fields)}):")
    for field in sorted(empty_string_fields):
        print(f"  {field}")
    
    print(f"\nEmpty list fields ({len(empty_list_fields)}):")
    for field in sorted(empty_list_fields):
        print(f"  {field}")
    
    # Check what's in our model vs what's in the response
    print("\n=== MODEL COMPARISON ===")
    
    # Fields we're expecting in our LinkedInProfile model
    model_fields = {
        'profile_id', 'full_name', 'linkedin_url', 'about', 'city', 'country', 
        'headline', 'location', 'state', 'company', 'job_title', 'company_description', 
        'company_domain', 'company_employee_count', 'company_employee_range', 
        'company_industry', 'company_linkedin_url', 'company_logo_url', 'company_website', 
        'company_year_founded', 'follower_count', 'connection_count', 
        'current_company_join_month', 'current_company_join_year', 'current_job_duration', 
        'is_creator', 'is_influencer', 'is_premium', 'is_verified', 'email', 'phone', 
        'first_name', 'last_name', 'profile_image_url', 'public_id', 'urn', 'hq_city', 
        'hq_country', 'hq_region', 'school', 'educations', 'experiences', 'languages'
    }
    
    response_fields = set(SAMPLE_RESPONSE.keys())
    
    in_model_and_response = model_fields.intersection(response_fields)
    in_response_not_model = response_fields - model_fields
    in_model_not_response = model_fields - response_fields
    
    print(f"\nFields in both model and response: {len(in_model_and_response)}")
    print(f"Fields in response but not in model: {len(in_response_not_model)}")
    if in_response_not_model:
        for field in sorted(in_response_not_model):
            print(f"  MISSING FROM MODEL: {field}")
    
    print(f"Fields in model but not in response: {len(in_model_not_response)}")
    if in_model_not_response:
        for field in sorted(in_model_not_response):
            print(f"  NOT IN RESPONSE: {field}")
    
    # Analyze experience and education structures
    print("\n=== EXPERIENCE STRUCTURE ===")
    if SAMPLE_RESPONSE.get('experiences'):
        exp = SAMPLE_RESPONSE['experiences'][0]
        print("First experience entry fields:")
        for field, value in exp.items():
            print(f"  {field}: {type(value).__name__} = {repr(value)}")
    
    print("\n=== EDUCATION STRUCTURE ===")
    if SAMPLE_RESPONSE.get('educations'):
        edu = SAMPLE_RESPONSE['educations'][0]
        print("First education entry fields:")
        for field, value in edu.items():
            print(f"  {field}: {type(value).__name__} = {repr(value)}")
    
    # Calculate what would be our "completeness" metric
    meaningful_data_count = len(populated_fields)
    api_provided_count = total_fields  # All fields are provided by API
    completeness = (meaningful_data_count / api_provided_count * 100) if api_provided_count > 0 else 0
    
    print(f"\n=== DATA QUALITY METRICS ===")
    print(f"Fields API provided: {api_provided_count}")
    print(f"Fields with meaningful data: {meaningful_data_count}")
    print(f"Data completeness: {completeness:.1f}%")
    
    # Identity data check
    identity_fields = ['profile_id', 'full_name', 'linkedin_url', 'public_id', 'first_name', 'last_name']
    has_identity = any(SAMPLE_RESPONSE.get(field, '').strip() for field in identity_fields if field in SAMPLE_RESPONSE)
    print(f"Has identity data: {has_identity}")
    
    return {
        'total_fields': total_fields,
        'populated_fields': meaningful_data_count,
        'completeness_percent': completeness,
        'has_identity': has_identity,
        'missing_from_model': list(in_response_not_model),
        'not_in_response': list(in_model_not_response)
    }

if __name__ == "__main__":
    analysis = analyze_response()
