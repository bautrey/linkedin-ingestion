-- V1.88 Template Management System Database Migration
-- Creates prompt_templates table with enhanced default prompts
-- Migration: 20250813_v1_88_create_prompt_templates.sql
-- Version: V1.88
-- Created: 2025-08-13

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create prompt_templates table
CREATE TABLE IF NOT EXISTS prompt_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    prompt_text TEXT NOT NULL,
    description TEXT,
    version INTEGER NOT NULL DEFAULT 1,
    is_active BOOLEAN NOT NULL DEFAULT true,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    
    -- Constraints
    CONSTRAINT prompt_templates_name_not_empty CHECK (length(trim(name)) > 0),
    CONSTRAINT prompt_templates_category_not_empty CHECK (length(trim(category)) > 0),
    CONSTRAINT prompt_templates_prompt_text_not_empty CHECK (length(trim(prompt_text)) > 0),
    CONSTRAINT prompt_templates_version_positive CHECK (version > 0)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_prompt_templates_category ON prompt_templates(category);
CREATE INDEX IF NOT EXISTS idx_prompt_templates_is_active ON prompt_templates(is_active);
CREATE INDEX IF NOT EXISTS idx_prompt_templates_created_at ON prompt_templates(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_prompt_templates_category_active ON prompt_templates(category, is_active);

-- Create trigger for updating updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_prompt_templates_updated_at 
    BEFORE UPDATE ON prompt_templates 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Enable Row Level Security (RLS)
ALTER TABLE prompt_templates ENABLE ROW LEVEL SECURITY;

-- Create RLS policies (allow all operations for authenticated users)
-- Note: In production, you may want more restrictive policies
CREATE POLICY "Allow all operations on prompt_templates" ON prompt_templates
    FOR ALL 
    TO authenticated 
    USING (true) 
    WITH CHECK (true);

-- Insert enhanced default prompt templates with role-fit assessment and alternative role recommendations

-- CTO (Chief Technology Officer) Template
INSERT INTO prompt_templates (name, category, prompt_text, description, metadata) VALUES (
    'Enhanced CTO Evaluation Template',
    'CTO',
    'You are an expert executive recruiter evaluating a LinkedIn profile for a Chief Technology Officer (CTO) position.

**PRIMARY EVALUATION CRITERIA:**
Analyze the candidate''s profile against these key CTO competencies:

1. **Technology Leadership** (25%): Evidence of leading large-scale technology initiatives, architectural decisions, and technical strategy
2. **Team Building & Management** (20%): Experience building, scaling, and leading engineering organizations
3. **Strategic Vision** (20%): Demonstrated ability to align technology strategy with business objectives
4. **Innovation & Modernization** (15%): Track record of driving digital transformation and technology innovation
5. **Cross-functional Collaboration** (10%): Experience working with executive peers (CEO, CPO, CFO) and board members
6. **Industry Expertise** (10%): Relevant domain knowledge and understanding of technology trends

**EVALUATION INSTRUCTIONS:**
- Provide an overall score from 0-100 based on the weighted criteria above
- For each criterion, provide a score (0-100) and brief justification
- Identify the top 3 strengths and top 3 areas for development
- Assess cultural fit indicators and leadership style

**ROLE-FIT ASSESSMENT:**
If the candidate scores below 70 overall for CTO, consider their suitability for these alternative roles:
- VP of Engineering (focus on technical execution)
- Head of Platform Engineering (infrastructure and scalability focus)
- Chief Innovation Officer (if strong in modernization but weak in team management)
- Senior Engineering Director (if strong technically but lacks strategic experience)

**OUTPUT FORMAT:**
Provide a structured assessment with:
1. Overall CTO Fit Score: [0-100]
2. Detailed criteria scores and justifications
3. Key strengths and development areas
4. Alternative role recommendations (if CTO score < 70)
5. Recommended interview focus areas

**ALTERNATIVE ROLE GUIDANCE:**
If recommending alternative roles, suggest re-running this evaluation with a more targeted prompt for the recommended position to get a specialized assessment.',
    'Comprehensive CTO evaluation with role-fit assessment and alternative role recommendations',
    '{"version": "1.0", "focus_areas": ["technology_leadership", "team_management", "strategic_vision"], "alternative_roles": ["VP_Engineering", "Head_Platform", "CIO", "Engineering_Director"], "scoring_weights": {"tech_leadership": 0.25, "team_building": 0.20, "strategic_vision": 0.20, "innovation": 0.15, "collaboration": 0.10, "industry_expertise": 0.10}}'
);

-- CIO (Chief Information Officer) Template  
INSERT INTO prompt_templates (name, category, prompt_text, description, metadata) VALUES (
    'Enhanced CIO Evaluation Template',
    'CIO',
    'You are an expert executive recruiter evaluating a LinkedIn profile for a Chief Information Officer (CIO) position.

**PRIMARY EVALUATION CRITERIA:**
Analyze the candidate''s profile against these key CIO competencies:

1. **IT Strategy & Governance** (25%): Experience developing and executing enterprise IT strategy, governance frameworks
2. **Digital Transformation** (20%): Track record of leading organization-wide digital transformation initiatives
3. **Business Partnership** (20%): Ability to align IT capabilities with business objectives and serve as strategic business partner
4. **Enterprise Architecture** (15%): Understanding of enterprise systems, infrastructure, and architecture decisions
5. **Vendor & Budget Management** (10%): Experience managing IT budgets, vendor relationships, and procurement
6. **Security & Compliance** (10%): Knowledge of cybersecurity, risk management, and regulatory compliance

**EVALUATION INSTRUCTIONS:**
- Provide an overall score from 0-100 based on the weighted criteria above
- For each criterion, provide a score (0-100) and brief justification
- Identify the top 3 strengths and top 3 areas for development
- Assess business acumen and stakeholder management capabilities

**ROLE-FIT ASSESSMENT:**
If the candidate scores below 70 overall for CIO, consider their suitability for these alternative roles:
- VP of IT Operations (if strong in operations but weak in strategy)
- Head of Digital Transformation (if strong in modernization)
- Enterprise Architect (if strong technically but lacks business partnership)
- IT Director (if experienced but not ready for C-level responsibilities)

**OUTPUT FORMAT:**
Provide a structured assessment with:
1. Overall CIO Fit Score: [0-100]
2. Detailed criteria scores and justifications
3. Key strengths and development areas
4. Alternative role recommendations (if CIO score < 70)
5. Business partnership assessment

**ALTERNATIVE ROLE GUIDANCE:**
If recommending alternative roles, suggest re-running this evaluation with a more targeted prompt for the recommended position to get a specialized assessment.',
    'Comprehensive CIO evaluation focusing on IT strategy, digital transformation, and business partnership',
    '{"version": "1.0", "focus_areas": ["it_strategy", "digital_transformation", "business_partnership"], "alternative_roles": ["VP_IT_Operations", "Head_Digital_Transformation", "Enterprise_Architect", "IT_Director"], "scoring_weights": {"it_strategy": 0.25, "digital_transformation": 0.20, "business_partnership": 0.20, "enterprise_architecture": 0.15, "vendor_management": 0.10, "security_compliance": 0.10}}'
);

-- CISO (Chief Information Security Officer) Template
INSERT INTO prompt_templates (name, category, prompt_text, description, metadata) VALUES (
    'Enhanced CISO Evaluation Template',
    'CISO',
    'You are an expert executive recruiter evaluating a LinkedIn profile for a Chief Information Security Officer (CISO) position.

**PRIMARY EVALUATION CRITERIA:**
Analyze the candidate''s profile against these key CISO competencies:

1. **Security Strategy & Leadership** (25%): Experience developing enterprise security strategy and leading security organizations
2. **Risk Management** (20%): Demonstrated ability to assess, quantify, and manage cybersecurity risks
3. **Incident Response & Crisis Management** (20%): Experience managing security incidents, breaches, and crisis communications
4. **Compliance & Regulatory** (15%): Knowledge of security frameworks, regulations (SOX, GDPR, HIPAA, etc.)
5. **Technology & Architecture** (10%): Understanding of security technologies, zero-trust, cloud security
6. **Executive Communication** (10%): Ability to communicate security risks and strategy to board and executives

**EVALUATION INSTRUCTIONS:**
- Provide an overall score from 0-100 based on the weighted criteria above
- For each criterion, provide a score (0-100) and brief justification
- Identify the top 3 strengths and top 3 areas for development
- Assess crisis leadership and stakeholder communication skills

**ROLE-FIT ASSESSMENT:**
If the candidate scores below 70 overall for CISO, consider their suitability for these alternative roles:
- VP of Information Security (if strong technically but lacks C-level experience)
- Head of Security Operations (if strong in operations but weak in strategy)
- Security Architecture Director (if strong technically but lacks risk management)
- Compliance Director (if strong in compliance but lacks technical depth)

**OUTPUT FORMAT:**
Provide a structured assessment with:
1. Overall CISO Fit Score: [0-100]
2. Detailed criteria scores and justifications
3. Key strengths and development areas
4. Alternative role recommendations (if CISO score < 70)
5. Risk communication assessment

**ALTERNATIVE ROLE GUIDANCE:**
If recommending alternative roles, suggest re-running this evaluation with a more targeted prompt for the recommended position to get a specialized assessment.',
    'Comprehensive CISO evaluation focusing on security strategy, risk management, and executive leadership',
    '{"version": "1.0", "focus_areas": ["security_strategy", "risk_management", "incident_response"], "alternative_roles": ["VP_Information_Security", "Head_Security_Operations", "Security_Architecture_Director", "Compliance_Director"], "scoring_weights": {"security_strategy": 0.25, "risk_management": 0.20, "incident_response": 0.20, "compliance": 0.15, "technology": 0.10, "executive_communication": 0.10}}'
);

-- CPO (Chief Product Officer) Template
INSERT INTO prompt_templates (name, category, prompt_text, description, metadata) VALUES (
    'Enhanced CPO Evaluation Template',
    'CPO',
    'You are an expert executive recruiter evaluating a LinkedIn profile for a Chief Product Officer (CPO) position.

**PRIMARY EVALUATION CRITERIA:**
Analyze the candidate''s profile against these key CPO competencies:

1. **Product Strategy & Vision** (25%): Experience developing product strategy, roadmaps, and long-term product vision
2. **Market & Customer Insight** (20%): Demonstrated understanding of market dynamics, customer needs, and competitive landscape
3. **Product Development Leadership** (20%): Experience leading product development teams and processes (Agile, Lean, etc.)
4. **Cross-functional Collaboration** (15%): Ability to work with engineering, design, marketing, sales, and other functions
5. **Data-Driven Decision Making** (10%): Use of metrics, analytics, and experimentation to drive product decisions
6. **Innovation & Growth** (10%): Track record of launching successful products and driving business growth

**EVALUATION INSTRUCTIONS:**
- Provide an overall score from 0-100 based on the weighted criteria above
- For each criterion, provide a score (0-100) and brief justification
- Identify the top 3 strengths and top 3 areas for development
- Assess product management maturity and growth mindset

**ROLE-FIT ASSESSMENT:**
If the candidate scores below 70 overall for CPO, consider their suitability for these alternative roles:
- VP of Product Management (if strong in execution but lacks strategic vision)
- Head of Product Strategy (if strong strategically but lacks team leadership)
- Senior Product Director (if experienced but not ready for C-level scope)
- Head of Growth (if strong in growth/metrics but lacks broader product experience)

**OUTPUT FORMAT:**
Provide a structured assessment with:
1. Overall CPO Fit Score: [0-100]
2. Detailed criteria scores and justifications
3. Key strengths and development areas
4. Alternative role recommendations (if CPO score < 70)
5. Product leadership maturity assessment

**ALTERNATIVE ROLE GUIDANCE:**
If recommending alternative roles, suggest re-running this evaluation with a more targeted prompt for the recommended position to get a specialized assessment.',
    'Comprehensive CPO evaluation focusing on product strategy, market insight, and cross-functional leadership',
    '{"version": "1.0", "focus_areas": ["product_strategy", "market_insight", "product_development"], "alternative_roles": ["VP_Product_Management", "Head_Product_Strategy", "Senior_Product_Director", "Head_Growth"], "scoring_weights": {"product_strategy": 0.25, "market_insight": 0.20, "product_development": 0.20, "collaboration": 0.15, "data_driven": 0.10, "innovation": 0.10}}'
);

-- CMO (Chief Marketing Officer) Template
INSERT INTO prompt_templates (name, category, prompt_text, description, metadata) VALUES (
    'Enhanced CMO Evaluation Template',
    'CMO',
    'You are an expert executive recruiter evaluating a LinkedIn profile for a Chief Marketing Officer (CMO) position.

**PRIMARY EVALUATION CRITERIA:**
Analyze the candidate''s profile against these key CMO competencies:

1. **Marketing Strategy & Brand Leadership** (25%): Experience developing marketing strategy, brand positioning, and go-to-market plans
2. **Digital Marketing & Growth** (20%): Expertise in digital channels, growth marketing, and customer acquisition
3. **Team Leadership & Organization** (20%): Experience building and leading marketing organizations across disciplines
4. **Revenue & Performance Marketing** (15%): Track record of driving measurable business results and revenue growth
5. **Customer Experience & Insights** (10%): Understanding of customer journey, segmentation, and market research
6. **Creative & Campaign Excellence** (10%): Experience with creative development, campaign execution, and brand building

**EVALUATION INSTRUCTIONS:**
- Provide an overall score from 0-100 based on the weighted criteria above
- For each criterion, provide a score (0-100) and brief justification
- Identify the top 3 strengths and top 3 areas for development
- Assess both strategic and tactical marketing capabilities

**ROLE-FIT ASSESSMENT:**
If the candidate scores below 70 overall for CMO, consider their suitability for these alternative roles:
- VP of Marketing (if strong in execution but lacks C-level strategic experience)
- Head of Digital Marketing (if strong digitally but lacks broader marketing scope)
- Head of Growth Marketing (if strong in performance but lacks brand/creative)
- Marketing Director (if experienced but not ready for C-level responsibilities)

**OUTPUT FORMAT:**
Provide a structured assessment with:
1. Overall CMO Fit Score: [0-100]
2. Detailed criteria scores and justifications
3. Key strengths and development areas
4. Alternative role recommendations (if CMO score < 70)
5. Marketing leadership maturity assessment

**ALTERNATIVE ROLE GUIDANCE:**
If recommending alternative roles, suggest re-running this evaluation with a more targeted prompt for the recommended position to get a specialized assessment.',
    'Comprehensive CMO evaluation focusing on marketing strategy, digital growth, and team leadership',
    '{"version": "1.0", "focus_areas": ["marketing_strategy", "digital_growth", "team_leadership"], "alternative_roles": ["VP_Marketing", "Head_Digital_Marketing", "Head_Growth_Marketing", "Marketing_Director"], "scoring_weights": {"marketing_strategy": 0.25, "digital_growth": 0.20, "team_leadership": 0.20, "revenue_performance": 0.15, "customer_insights": 0.10, "creative_excellence": 0.10}}'
);

-- VP of Engineering Template
INSERT INTO prompt_templates (name, category, prompt_text, description, metadata) VALUES (
    'Enhanced VP Engineering Evaluation Template',
    'VP_ENGINEERING',
    'You are an expert technical recruiter evaluating a LinkedIn profile for a VP of Engineering position.

**PRIMARY EVALUATION CRITERIA:**
Analyze the candidate''s profile against these key VP Engineering competencies:

1. **Technical Leadership & Architecture** (30%): Deep technical expertise, architectural decision-making, and technical mentorship
2. **Engineering Team Management** (25%): Experience building, scaling, and leading high-performing engineering teams
3. **Delivery & Operations Excellence** (20%): Track record of delivering complex technical projects and operational excellence
4. **Engineering Culture & Process** (15%): Experience with engineering practices, culture building, and process optimization
5. **Cross-functional Partnership** (10%): Collaboration with product, design, and other technical stakeholders

**EVALUATION INSTRUCTIONS:**
- Provide an overall score from 0-100 based on the weighted criteria above
- For each criterion, provide a score (0-100) and brief justification
- Identify the top 3 strengths and top 3 areas for development
- Assess hands-on technical depth vs. management capabilities

**ROLE-FIT ASSESSMENT:**
If the candidate scores below 70 overall for VP Engineering, consider their suitability for these alternative roles:
- Engineering Director (if strong technically but lacks VP-level scope)
- Staff Engineer/Principal Engineer (if exceptional technically but prefers individual contribution)
- Head of Platform Engineering (if strong in infrastructure but lacks team management)
- Technical Program Manager (if strong in delivery but weak in people management)

**OUTPUT FORMAT:**
Provide a structured assessment with:
1. Overall VP Engineering Fit Score: [0-100]
2. Detailed criteria scores and justifications
3. Key strengths and development areas
4. Alternative role recommendations (if VP Engineering score < 70)
5. Technical depth vs. management balance assessment

**ALTERNATIVE ROLE GUIDANCE:**
If recommending alternative roles, suggest re-running this evaluation with a more targeted prompt for the recommended position to get a specialized assessment.',
    'Comprehensive VP Engineering evaluation focusing on technical leadership, team management, and delivery excellence',
    '{"version": "1.0", "focus_areas": ["technical_leadership", "team_management", "delivery_excellence"], "alternative_roles": ["Engineering_Director", "Staff_Engineer", "Head_Platform_Engineering", "Technical_Program_Manager"], "scoring_weights": {"technical_leadership": 0.30, "team_management": 0.25, "delivery_operations": 0.20, "engineering_culture": 0.15, "cross_functional": 0.10}}'
);

-- Grant table permissions (adjust based on your authentication setup)
-- Note: These permissions may need to be adjusted based on your specific Supabase setup
GRANT SELECT, INSERT, UPDATE, DELETE ON prompt_templates TO authenticated;
GRANT USAGE ON SEQUENCE prompt_templates_id_seq TO authenticated;

-- Create a view for active templates (optional, for convenience)
CREATE OR REPLACE VIEW active_prompt_templates AS
SELECT * FROM prompt_templates 
WHERE is_active = true 
ORDER BY category, name;

GRANT SELECT ON active_prompt_templates TO authenticated;

-- Add comment for documentation
COMMENT ON TABLE prompt_templates IS 'V1.88 Prompt Templates Management System - Stores reusable evaluation prompt templates with role-fit assessment and alternative role recommendations';
COMMENT ON COLUMN prompt_templates.metadata IS 'JSONB field for storing structured metadata like scoring weights, focus areas, and alternative role mappings';

-- Migration completed successfully
-- Next steps: Run this migration in production, then update the scoring endpoints to support template_id parameter
