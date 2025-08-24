-- Stage-Based Scoring Templates with Model Configuration
-- Use this to set up templates optimized for different evaluation stages

-- Stage 2: Sanity Check Templates (use gpt-3.5-turbo for cost efficiency)
INSERT INTO prompt_templates (
    id,
    name, 
    category,
    prompt_text,
    preferred_model,
    description,
    is_active,
    version,
    created_at,
    updated_at,
    metadata
) VALUES 
(
    gen_random_uuid(),
    'CTO Sanity Check - Quick Filter',
    'CTO',
    'Evaluate this LinkedIn profile for basic CTO qualifications. Provide a quick assessment in JSON format with:
    
    {
        "basic_fit": "YES/NO/MAYBE",
        "score": 1-10,
        "key_signals": ["list", "of", "positive", "signals"],
        "red_flags": ["list", "of", "concerns"],
        "reasoning": "Brief 2-3 sentence rationale",
        "stage_2_recommendation": "ADVANCE_TO_DEEP_ANALYSIS or REJECT"
    }
    
    Focus on obvious disqualifiers or strong positive signals:
    - Years of technical leadership experience (5+ years preferred)
    - Technology stack depth and breadth
    - Team/organization size managed
    - Company stage and scale experience
    - Education relevance
    
    Keep analysis concise - this is a filtering stage.',
    'gpt-3.5-turbo',
    'Quick sanity check for CTO candidates using cost-effective model',
    true,
    1,
    NOW(),
    NOW(),
    '{"stage": "sanity_check", "cost_optimized": true, "target_role": "CTO"}'
),
(
    gen_random_uuid(),
    'CISO Sanity Check - Security Focus',
    'CISO', 
    'Quick security leadership assessment. Return JSON with:
    
    {
        "security_fit": "STRONG/MODERATE/WEAK",
        "score": 1-10,
        "security_signals": ["cybersecurity", "compliance", "risk management"],
        "leadership_indicators": ["team size", "budget responsibility"],
        "missing_elements": ["gaps or concerns"],
        "stage_2_recommendation": "ADVANCE_TO_DEEP_ANALYSIS or REJECT"
    }
    
    Key filters:
    - Security/cybersecurity experience (3+ years)
    - Compliance frameworks (SOC2, ISO27001, etc.)
    - Incident response experience
    - Security team leadership
    - Risk management background',
    'gpt-3.5-turbo',
    'Cost-effective CISO screening for basic security leadership qualifications',
    true,
    1,
    NOW(),
    NOW(),
    '{"stage": "sanity_check", "cost_optimized": true, "target_role": "CISO"}'
),

-- Stage 3: Deep Analysis Templates (use gpt-4o for quality insights)
(
    gen_random_uuid(),
    'CTO Deep Analysis - Comprehensive Evaluation',
    'CTO',
    'Conduct a comprehensive evaluation of this CTO candidate. Provide detailed JSON analysis:
    
    {
        "overall_assessment": {
            "fit_score": 1-100,
            "confidence_level": "HIGH/MEDIUM/LOW",
            "hire_recommendation": "STRONG_YES/YES/MAYBE/NO/STRONG_NO"
        },
        "technical_leadership": {
            "score": 1-10,
            "depth_analysis": "detailed assessment of technical depth",
            "architecture_experience": "system design and scaling experience",
            "technology_breadth": "range of technologies and domains"
        },
        "organizational_leadership": {
            "score": 1-10,
            "team_scale": "largest team managed and growth trajectory",
            "hiring_experience": "talent acquisition and retention track record",
            "cross_functional": "collaboration with product, sales, marketing"
        },
        "business_acumen": {
            "score": 1-10,
            "strategic_thinking": "business strategy and technology alignment",
            "scaling_experience": "experience with company growth stages",
            "budget_responsibility": "financial management and resource allocation"
        },
        "risk_assessment": {
            "potential_concerns": ["detailed list of risks"],
            "mitigation_strategies": ["ways to address concerns"],
            "culture_fit_indicators": ["alignment with company values"]
        },
        "interview_focus_areas": ["specific topics to explore in interviews"],
        "reference_check_questions": ["key questions for past colleagues"]
    }
    
    Analyze leadership philosophy, decision-making frameworks, and transformational impact on previous organizations.',
    'gpt-4o',
    'Comprehensive CTO evaluation using advanced reasoning for final hiring decisions',
    true,
    1,
    NOW(),
    NOW(),
    '{"stage": "deep_analysis", "premium_model": true, "target_role": "CTO"}'
),
(
    gen_random_uuid(),
    'CISO Deep Analysis - Security Leadership Excellence',
    'CISO',
    'Comprehensive CISO candidate evaluation with advanced security leadership analysis:
    
    {
        "executive_summary": {
            "overall_score": 1-100,
            "hire_confidence": "HIGH/MEDIUM/LOW",
            "recommendation": "STRONG_HIRE/HIRE/CONSIDER/PASS"
        },
        "security_expertise": {
            "technical_depth": "hands-on security skills and modern threat landscape",
            "governance_experience": "policy, compliance, and risk frameworks",
            "incident_leadership": "crisis management and response capabilities",
            "score": 1-10
        },
        "executive_presence": {
            "board_readiness": "ability to communicate with executives and board",
            "business_partnership": "collaboration with business stakeholders",
            "influence_without_authority": "change management and adoption skills",
            "score": 1-10
        },
        "organizational_impact": {
            "culture_transformation": "building security-conscious culture",
            "program_maturation": "elevating security program maturity",
            "team_development": "growing and retaining security talent",
            "score": 1-10
        },
        "strategic_thinking": {
            "risk_prioritization": "business risk assessment and resource allocation",
            "technology_strategy": "security architecture and tool selection",
            "future_readiness": "emerging threats and technology trends",
            "score": 1-10
        },
        "potential_challenges": ["areas requiring development or support"],
        "onboarding_focus": ["key success factors for first 90 days"],
        "interview_deep_dives": ["critical assessment areas"]
    }',
    'gpt-4o', 
    'Advanced CISO evaluation leveraging sophisticated reasoning for executive security roles',
    true,
    1,
    NOW(),
    NOW(),
    '{"stage": "deep_analysis", "premium_model": true, "target_role": "CISO"}'
);

-- Example usage queries:
-- SELECT name, category, preferred_model, description FROM prompt_templates WHERE metadata->>'stage' = 'sanity_check';
-- SELECT name, category, preferred_model, description FROM prompt_templates WHERE metadata->>'stage' = 'deep_analysis';
