# 4-Template 3-Stage Workflow Design

## Stage 1: Profile Verification (Cassidy Call)
This endpoint calls the Cassidy model to fetch and verify the LinkedIn profile exists and has valid data.

**Endpoint**: `POST /api/v1/profiles/verify`  
**Purpose**: Verify LinkedIn URL returns valid profile data from Cassidy  
**Cassidy Model**: Profile workflow (no company ingestion)

```json
{
  "linkedin_url": "https://linkedin.com/in/sample-profile"
}
```

**Response on Success**:
```json
{
  "verified": true,
  "profile_data": {
    "name": "John Doe",
    "headline": "CTO at TechCorp",
    "about": "...",
    "experience_count": 5,
    "education_count": 2
  },
  "data_completeness": "COMPLETE",
  "executive_indicators": true,
  "proceed_to_sanity_check": true,
  "cassidy_response_time": 4.2
}
```

**Response on Failure**:
```json
{
  "verified": false,
  "error": "Profile not found or invalid LinkedIn URL",
  "cassidy_error": "Cassidy workflow failed: The provided URL is not valid...",
  "proceed_to_sanity_check": false
}
```

## Template 1: Universal Sanity Check (Stage 2)
**Stage**: `stage_2_screening` → **Model**: `gpt-3.5-turbo` (~$0.002/eval)

```json
{
  "name": "Universal Executive Sanity Check",
  "category": "EXECUTIVE", 
  "stage": "stage_2_screening",
  "prompt_text": "You are an expert executive recruiter. Evaluate this LinkedIn profile for executive leadership potential across CTO, CIO, and CISO roles.\n\nPROFILE:\n{{profile_data}}\n\nSUGGESTED_ROLE: {{suggested_role}}\n\nTASK: Perform a sanity check to determine if this candidate should proceed to deep analysis.\n\n1. First evaluate for the SUGGESTED_ROLE\n2. If suggested role scores poorly (< 6/10), evaluate for the other two executive roles\n3. Make a continuation recommendation\n\nRESPOND IN JSON:\n{\n  \"continue\": true/false,\n  \"suggested_role_score\": 1-10,\n  \"suggested_role_fit\": \"STRONG/MODERATE/WEAK\",\n  \"alternative_roles\": {\n    \"CTO\": {\"score\": 1-10, \"reasoning\": \"brief assessment\"},\n    \"CIO\": {\"score\": 1-10, \"reasoning\": \"brief assessment\"},\n    \"CISO\": {\"score\": 1-10, \"reasoning\": \"brief assessment\"}\n  },\n  \"recommended_role\": \"CTO/CIO/CISO or NONE\",\n  \"reasoning\": \"Why continue or stop, which role is best fit\",\n  \"key_strengths\": [\"list\", \"of\", \"strengths\"],\n  \"red_flags\": [\"list\", \"of\", \"concerns\"]\n}"
}
```

## Template 2: CTO Deep Analysis (Stage 3)
**Stage**: `stage_3_analysis` → **Model**: `gpt-4o` (~$0.02/eval)

```json
{
  "name": "CTO Comprehensive Evaluation",
  "category": "CTO",
  "stage": "stage_3_analysis", 
  "prompt_text": "Conduct a comprehensive CTO evaluation for this candidate who passed sanity check.\n\nPROFILE:\n{{profile_data}}\n\nProvide detailed analysis in JSON:\n{\n  \"overall_assessment\": {\n    \"fit_score\": 1-100,\n    \"confidence_level\": \"HIGH/MEDIUM/LOW\",\n    \"hire_recommendation\": \"STRONG_YES/YES/MAYBE/NO/STRONG_NO\"\n  },\n  \"technical_leadership\": {\n    \"score\": 1-10,\n    \"depth_analysis\": \"detailed assessment of technical depth\",\n    \"architecture_experience\": \"system design and scaling experience\",\n    \"technology_breadth\": \"range of technologies and domains\"\n  },\n  \"organizational_leadership\": {\n    \"score\": 1-10,\n    \"team_scale\": \"largest team managed and growth trajectory\",\n    \"hiring_experience\": \"talent acquisition and retention track record\",\n    \"cross_functional\": \"collaboration with product, sales, marketing\"\n  },\n  \"strategic_thinking\": {\n    \"score\": 1-10,\n    \"business_alignment\": \"technology strategy alignment with business\",\n    \"scaling_experience\": \"experience with company growth stages\",\n    \"innovation_track_record\": \"examples of technical innovation leadership\"\n  },\n  \"risk_assessment\": {\n    \"potential_concerns\": [\"detailed list of risks\"],\n    \"mitigation_strategies\": [\"ways to address concerns\"],\n    \"culture_fit_indicators\": [\"alignment with company values\"]\n  },\n  \"interview_focus_areas\": [\"specific topics to explore in interviews\"],\n  \"reference_check_questions\": [\"key questions for past colleagues\"]\n}"
}
```

## Template 3: CIO Deep Analysis (Stage 3)
**Stage**: `stage_3_analysis` → **Model**: `gpt-4o` (~$0.02/eval)

```json
{
  "name": "CIO Comprehensive Evaluation",
  "category": "CIO",
  "stage": "stage_3_analysis",
  "prompt_text": "Comprehensive CIO evaluation focusing on IT strategy and business partnership.\n\nPROFILE:\n{{profile_data}}\n\nProvide detailed CIO analysis in JSON:\n{\n  \"overall_assessment\": {\n    \"fit_score\": 1-100,\n    \"hire_recommendation\": \"STRONG_YES/YES/MAYBE/NO/STRONG_NO\"\n  },\n  \"it_strategy_governance\": {\n    \"score\": 1-10,\n    \"strategy_experience\": \"IT strategy development and execution\",\n    \"governance_frameworks\": \"experience with IT governance\"\n  },\n  \"digital_transformation\": {\n    \"score\": 1-10, \n    \"transformation_leadership\": \"leading digital transformation initiatives\",\n    \"change_management\": \"managing organizational change\"\n  },\n  \"business_partnership\": {\n    \"score\": 1-10,\n    \"stakeholder_engagement\": \"working with business stakeholders\",\n    \"value_delivery\": \"demonstrating IT business value\"\n  },\n  \"operational_excellence\": {\n    \"score\": 1-10,\n    \"budget_management\": \"IT budget and resource management\",\n    \"vendor_relationships\": \"managing technology vendors and partnerships\"\n  }\n}"
}
```

## Template 4: CISO Deep Analysis (Stage 3)  
**Stage**: `stage_3_analysis` → **Model**: `gpt-4o` (~$0.02/eval)

```json
{
  "name": "CISO Comprehensive Evaluation", 
  "category": "CISO",
  "stage": "stage_3_analysis",
  "prompt_text": "Comprehensive CISO evaluation focusing on security leadership and risk management.\n\nPROFILE:\n{{profile_data}}\n\nProvide detailed security leadership analysis in JSON:\n{\n  \"overall_assessment\": {\n    \"fit_score\": 1-100,\n    \"hire_recommendation\": \"STRONG_YES/YES/MAYBE/NO/STRONG_NO\"\n  },\n  \"security_expertise\": {\n    \"score\": 1-10,\n    \"technical_depth\": \"hands-on security skills and threat landscape knowledge\",\n    \"compliance_experience\": \"regulatory compliance and framework experience\"\n  },\n  \"risk_management\": {\n    \"score\": 1-10,\n    \"risk_assessment\": \"enterprise risk assessment capabilities\", \n    \"incident_response\": \"crisis management and response leadership\"\n  },\n  \"executive_presence\": {\n    \"score\": 1-10,\n    \"board_communication\": \"ability to communicate with executives and board\",\n    \"business_partnership\": \"collaboration with business stakeholders\"\n  },\n  \"program_leadership\": {\n    \"score\": 1-10,\n    \"security_culture\": \"building security-conscious organizational culture\",\n    \"team_development\": \"growing and retaining security talent\"\n  }\n}"
}
```

## Workflow Summary

1. **Stage 1**: Cassidy profile verification → validates LinkedIn URL returns usable profile data  
2. **Stage 2**: Universal sanity check (OpenAI LLM) → decides continue/stop + role recommendation
3. **Stage 3**: Role-specific deep analysis (OpenAI LLM) → detailed hire assessment
4. **Cost**: Cassidy cost for verification, ~$0.002 for screening, ~$0.02 for deep analysis
5. **Templates**: Only 4 LLM templates needed (1 screening + 3 role-specific)
6. **API Endpoints**: `/verify` → `/score` (stage 2) → `/profiles` (stage 3 + full ingestion)
