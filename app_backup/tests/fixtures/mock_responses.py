"""
Mock response data for testing Cassidy integration

Based on the actual Cassidy blueprint structure and ronlinkedin_pretty.json data
"""

from typing import Dict, Any


# Mock Cassidy workflow response structure
MOCK_CASSIDY_PROFILE_RESPONSE: Dict[str, Any] = {
    "workflowRun": {
        "id": "test-workflow-run-id",
        "status": "completed",
        "actionResults": [
            {
                "id": "action-1",
                "status": "success",
                "output": {
                    "value": """{
                        "id": "ronald-sorozan-mba-cism-pmp-8325652",
                        "name": "Ronald Sorozan (MBA, CISM, PMP)",
                        "city": "Greater Houston",
                        "country_code": "US",
                        "position": "Chief Information Officer | Chief Security Officer | Chief Technology Officer",
                        "about": "Chief Information Officer Chief Technology Officer Chief Security Officer CISM and PMP Certified",
                        "current_company": {
                            "name": "JAM+",
                            "company_id": "jambnc",
                            "title": "Global Chief Information Officer and Chief Operating Officer (TZP Private Equity)",
                            "location": "Northvale, New Jersey and Houston, Texas"
                        },
                        "experience": [
                            {
                                "title": "Global Chief Information Officer and Chief Operating Officer (TZP Private Equity)",
                                "location": "Northvale, New Jersey and Houston, Texas",
                                "description": "MANUFACTURING, DISTRIBUTION, RETAIL, DIGITAL/E-COMMERCE, EDI/API, PRIVATE EQUITY SECTORS",
                                "start_date": "2021",
                                "end_date": "Present",
                                "company": "JAM+",
                                "company_id": "jambnc",
                                "url": "https://www.linkedin.com/company/jambnc",
                                "company_logo_url": "https://media.licdn.com/dms/image/v2/D4E0BAQGkFJ5c-Ht1Tg/company-logo_100_100/company-logo_100_100/0/1716332314357/jambnc_logo"
                            }
                        ],
                        "education": [
                            {
                                "title": "Drexel University's LeBow College of Business",
                                "degree": "Master of Business Administration - MBA",
                                "field": "Management Information Systems",
                                "url": "https://www.linkedin.com/school/drexel-university's-lebow-college-of-business/",
                                "institute_logo_url": "https://media.licdn.com/dms/image/v2/C560BAQHTIRilFGnKKg/company-logo_100_100/company-logo_100_100/0/1657106559252/drexel_universitys_lebow_college_of_business_logo"
                            }
                        ],
                        "certifications": [
                            {
                                "subtitle": "ISACA",
                                "title": "Certified Information Security Management (CISM)"
                            },
                            {
                                "subtitle": "Project Management Institute",
                                "title": "Project Management Professional (PMP)"
                            }
                        ],
                        "url": "https://www.linkedin.com/in/ronald-sorozan-mba-cism-pmp-8325652/",
                        "followers": 1503,
                        "connections": 500,
                        "timestamp": "2025-06-13T21:35:26.380Z"
                    }"""
                }
            }
        ]
    }
}


MOCK_CASSIDY_COMPANY_RESPONSE: Dict[str, Any] = {
    "workflowRun": {
        "id": "test-company-workflow-run-id", 
        "status": "completed",
        "actionResults": [
            {
                "id": "company-action-1",
                "status": "success",
                "output": {
                    "value": """{
                        "company_id": "jambnc",
                        "company_name": "JAM+",
                        "description": "JAM+ is a leading provider of printing and promotional products.",
                        "website": "https://www.jamplus.com",
                        "linkedin_url": "https://www.linkedin.com/company/jambnc",
                        "employee_count": 250,
                        "employee_range": "201-500",
                        "year_founded": 2018,
                        "industries": ["Printing", "Marketing", "Promotional Products"],
                        "hq_city": "Northvale",
                        "hq_region": "New Jersey",
                        "hq_country": "US",
                        "locations": [
                            {
                                "city": "Northvale",
                                "region": "New Jersey", 
                                "country": "US",
                                "is_headquarter": true
                            }
                        ],
                        "funding_info": {
                            "crunchbase_url": null,
                            "num_funding_rounds": "0",
                            "last_funding_round_type": null
                        }
                    }"""
                }
            }
        ]
    }
}


# Error response examples
MOCK_CASSIDY_ERROR_RESPONSE: Dict[str, Any] = {
    "error": "WorkflowExecutionError",
    "message": "Failed to extract LinkedIn profile data",
    "details": {
        "workflow_id": "test-workflow-id",
        "error_code": "EXTRACTION_FAILED"
    }
}


MOCK_CASSIDY_TIMEOUT_RESPONSE: Dict[str, Any] = {
    "workflowRun": {
        "id": "test-timeout-workflow-run-id",
        "status": "timeout",
        "actionResults": []
    }
}


# Test LinkedIn URLs
TEST_LINKEDIN_PROFILE_URL = "https://www.linkedin.com/in/ronald-sorozan-mba-cism-pmp-8325652/"
TEST_LINKEDIN_COMPANY_URL = "https://www.linkedin.com/company/jambnc/"

# Additional test profiles for different scenarios
MOCK_PROFILE_MINIMAL_DATA: Dict[str, Any] = {
    "workflowRun": {
        "id": "minimal-profile-workflow",
        "status": "completed",
        "actionResults": [
            {
                "id": "minimal-action",
                "status": "success", 
                "output": {
                    "value": """{
                        "id": "test-minimal-profile",
                        "name": "Jane Smith",
                        "position": "Software Engineer",
                        "url": "https://www.linkedin.com/in/jane-smith/",
                        "experience": [],
                        "education": [],
                        "certifications": []
                    }"""
                }
            }
        ]
    }
}


MOCK_PROFILE_WITH_MULTIPLE_COMPANIES: Dict[str, Any] = {
    "workflowRun": {
        "id": "multi-company-workflow",
        "status": "completed",
        "actionResults": [
            {
                "id": "multi-company-action",
                "status": "success",
                "output": {
                    "value": """{
                        "id": "test-multi-company-profile",
                        "name": "John Doe",
                        "position": "Senior Developer",
                        "url": "https://www.linkedin.com/in/john-doe/",
                        "experience": [
                            {
                                "title": "Senior Developer",
                                "company": "Tech Corp",
                                "company_id": "tech-corp",
                                "url": "https://www.linkedin.com/company/tech-corp/",
                                "start_date": "2022",
                                "end_date": "Present"
                            },
                            {
                                "title": "Junior Developer", 
                                "company": "StartupXYZ",
                                "company_id": "startup-xyz",
                                "url": "https://www.linkedin.com/company/startup-xyz/",
                                "start_date": "2020",
                                "end_date": "2022"
                            }
                        ],
                        "education": [],
                        "certifications": []
                    }"""
                }
            }
        ]
    }
}
