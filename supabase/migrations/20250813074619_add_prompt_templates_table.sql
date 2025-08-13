-- V1.88 Prompt Templates Management System
-- Create prompt_templates table with indexes, constraints, and default data

-- Create table
CREATE TABLE prompt_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL, 
    prompt_text TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    is_active BOOLEAN NOT NULL DEFAULT true,
    description TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_prompt_templates_category ON prompt_templates(category);
CREATE INDEX idx_prompt_templates_active ON prompt_templates(is_active);  
CREATE INDEX idx_prompt_templates_category_active ON prompt_templates(category, is_active);
CREATE INDEX idx_prompt_templates_created_at ON prompt_templates(created_at);

-- Add constraints
ALTER TABLE prompt_templates ADD CONSTRAINT check_category_not_empty 
    CHECK (LENGTH(TRIM(category)) > 0);
ALTER TABLE prompt_templates ADD CONSTRAINT check_prompt_text_not_empty 
    CHECK (LENGTH(TRIM(prompt_text)) > 0);
ALTER TABLE prompt_templates ADD CONSTRAINT check_name_not_empty 
    CHECK (LENGTH(TRIM(name)) > 0);
ALTER TABLE prompt_templates ADD CONSTRAINT check_version_positive 
    CHECK (version > 0);

-- Create update trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger
DROP TRIGGER IF EXISTS update_prompt_templates_updated_at ON prompt_templates;
CREATE TRIGGER update_prompt_templates_updated_at 
    BEFORE UPDATE ON prompt_templates 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Enable RLS
ALTER TABLE prompt_templates ENABLE ROW LEVEL SECURITY;

-- Create policy
CREATE POLICY "Enable all operations for api access" ON prompt_templates
    FOR ALL USING (true) WITH CHECK (true);

-- Insert default templates with role-fit assessment
INSERT INTO prompt_templates (name, category, description, prompt_text) VALUES
    (
        'Fortium CTO Evaluation',
        'CTO',
        'Standard evaluation criteria for CTO candidates',
        'You are evaluating a candidate for a Chief Technology Officer (CTO) position. Based on the LinkedIn profile data provided, assess the candidate across these criteria:

1. **Technical Leadership Experience (0-10)**: Evaluate their experience leading technical teams, making architectural decisions, and driving technical strategy.

2. **Technology Stack Depth (0-10)**: Assess their hands-on experience with relevant technologies and their ability to stay current with tech trends.

3. **Business Acumen (0-10)**: Consider their understanding of business objectives and ability to align technology with business goals.

4. **Team Building & Management (0-10)**: Evaluate their experience recruiting, mentoring, and scaling technical teams.

5. **Strategic Vision (0-10)**: Assess their ability to define and execute long-term technical vision and roadmap.

6. **Role Fit Assessment (0-10)**: Based on this candidate''s background, how well do they fit the CTO role specifically?

**Overall CTO Fit Score (0-10)**: Provide an overall assessment of their suitability for a CTO role.

**Alternative Role Recommendation**: If this candidate scores below 6 for CTO fit, recommend whether they might be better suited for a CIO or CISO role and explain why based on their background.

Respond in valid JSON format with numeric scores and string explanations.'
    ),
    (
        'Fortium CIO Evaluation',
        'CIO',
        'Standard evaluation criteria for CIO candidates',
        'You are evaluating a candidate for a Chief Information Officer (CIO) position. Based on the LinkedIn profile data provided, assess the candidate across these criteria:

1. **IT Strategy & Governance (0-10)**: Evaluate their experience developing IT strategies, governance frameworks, and aligning IT with business objectives.

2. **Enterprise Systems Experience (0-10)**: Assess their experience with enterprise-scale systems, infrastructure, and digital transformation initiatives.

3. **Budget & Resource Management (0-10)**: Consider their experience managing IT budgets, vendor relationships, and resource allocation.

4. **Risk Management & Compliance (0-10)**: Evaluate their understanding of IT risk management, security, and regulatory compliance.

5. **Stakeholder Communication (0-10)**: Assess their ability to communicate with executives and translate technical concepts to business stakeholders.

6. **Role Fit Assessment (0-10)**: Based on this candidate''s background, how well do they fit the CIO role specifically?

**Overall CIO Fit Score (0-10)**: Provide an overall assessment of their suitability for a CIO role.

**Alternative Role Recommendation**: If this candidate scores below 6 for CIO fit, recommend whether they might be better suited for a CTO or CISO role and explain why based on their background.

Respond in valid JSON format with numeric scores and string explanations.'
    ),
    (
        'Fortium CISO Evaluation',
        'CISO',
        'Standard evaluation criteria for CISO candidates',
        'You are evaluating a candidate for a Chief Information Security Officer (CISO) position. Based on the LinkedIn profile data provided, assess the candidate across these criteria:

1. **Cybersecurity Expertise (0-10)**: Evaluate their depth of cybersecurity knowledge, certifications, and hands-on security experience.

2. **Risk Management (0-10)**: Assess their experience identifying, assessing, and mitigating information security risks.

3. **Compliance & Governance (0-10)**: Consider their knowledge of security frameworks, regulations, and governance practices.

4. **Incident Response (0-10)**: Evaluate their experience with security incident response, crisis management, and business continuity.

5. **Strategic Security Leadership (0-10)**: Assess their ability to develop security strategies and lead security transformation initiatives.

6. **Role Fit Assessment (0-10)**: Based on this candidate''s background, how well do they fit the CISO role specifically?

**Overall CISO Fit Score (0-10)**: Provide an overall assessment of their suitability for a CISO role.

**Alternative Role Recommendation**: If this candidate scores below 6 for CISO fit, recommend whether they might be better suited for a CTO or CIO role and explain why based on their background.

Respond in valid JSON format with numeric scores and string explanations.'
    );
