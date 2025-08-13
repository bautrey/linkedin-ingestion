# Database Schema

> Spec: V1.88 Prompt Templates Management System
> Document: Database Schema Specification
> Created: 2025-08-13

## Schema Overview

The prompt templates system requires a single new table `prompt_templates` that stores reusable evaluation prompts with categorization, versioning, and metadata support. The schema integrates with the existing Supabase PostgreSQL database.

## Table: prompt_templates

### Schema Definition

```sql
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
```

### Field Specifications

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Unique identifier for each template |
| `name` | VARCHAR(255) | NOT NULL | Human-readable template name |
| `category` | VARCHAR(100) | NOT NULL | Template category (e.g., "CTO", "CIO", "CISO") |
| `prompt_text` | TEXT | NOT NULL | The actual evaluation prompt content |
| `version` | INTEGER | NOT NULL, DEFAULT 1 | Version number for template iterations |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT true | Whether template is currently active |
| `description` | TEXT | NULLABLE | Optional description of template purpose |
| `metadata` | JSONB | DEFAULT '{}'::jsonb | Additional structured data (tags, settings, etc.) |
| `created_at` | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | Template creation timestamp |
| `updated_at` | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | Last modification timestamp |

### Indexes

```sql
-- Primary key index (automatic)
-- Additional performance indexes
CREATE INDEX idx_prompt_templates_category ON prompt_templates(category);
CREATE INDEX idx_prompt_templates_active ON prompt_templates(is_active);
CREATE INDEX idx_prompt_templates_category_active ON prompt_templates(category, is_active);
CREATE INDEX idx_prompt_templates_created_at ON prompt_templates(created_at);
```

### Constraints

```sql
-- Ensure category values are consistent
ALTER TABLE prompt_templates ADD CONSTRAINT check_category_not_empty 
    CHECK (LENGTH(TRIM(category)) > 0);

-- Ensure prompt_text is not empty
ALTER TABLE prompt_templates ADD CONSTRAINT check_prompt_text_not_empty 
    CHECK (LENGTH(TRIM(prompt_text)) > 0);

-- Ensure name is not empty
ALTER TABLE prompt_templates ADD CONSTRAINT check_name_not_empty 
    CHECK (LENGTH(TRIM(name)) > 0);

-- Ensure version is positive
ALTER TABLE prompt_templates ADD CONSTRAINT check_version_positive 
    CHECK (version > 0);
```

### Triggers

```sql
-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_prompt_templates_updated_at ON prompt_templates;
CREATE TRIGGER update_prompt_templates_updated_at 
    BEFORE UPDATE ON prompt_templates 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### Row Level Security (RLS)

```sql
-- Enable RLS (following existing pattern)
ALTER TABLE prompt_templates ENABLE ROW LEVEL SECURITY;

-- Policy for API access (consistent with existing tables)
CREATE POLICY "Enable all operations for api access" ON prompt_templates
    FOR ALL USING (true) WITH CHECK (true);
```

## Default Data Seeding

### Fortium Standard Templates

```sql
-- CTO Evaluation Template
INSERT INTO prompt_templates (name, category, description, prompt_text) VALUES (
    'Fortium CTO Evaluation',
    'CTO',
    'Standard evaluation criteria for CTO candidates',
    'You are evaluating a candidate for a Chief Technology Officer (CTO) position. Based on the LinkedIn profile data provided, assess the candidate across these criteria:

1. **Technical Leadership Experience (0-10)**: Evaluate their experience leading technical teams, making architectural decisions, and driving technical strategy.

2. **Technology Stack Depth (0-10)**: Assess their hands-on experience with relevant technologies and their ability to stay current with tech trends.

3. **Business Acumen (0-10)**: Consider their understanding of business objectives and ability to align technology with business goals.

4. **Team Building & Management (0-10)**: Evaluate their experience recruiting, mentoring, and scaling technical teams.

5. **Strategic Vision (0-10)**: Assess their ability to define and execute long-term technical vision and roadmap.

**Overall CTO Fit Score (0-10)**: Provide an overall assessment of their suitability for a CTO role.

For each score, provide a brief justification based on specific evidence from their LinkedIn profile. Focus on concrete examples from their work experience, education, and achievements.

Respond in valid JSON format with numeric scores and string explanations.'
);

-- CIO Evaluation Template  
INSERT INTO prompt_templates (name, category, description, prompt_text) VALUES (
    'Fortium CIO Evaluation',
    'CIO',
    'Standard evaluation criteria for CIO candidates',
    'You are evaluating a candidate for a Chief Information Officer (CIO) position. Based on the LinkedIn profile data provided, assess the candidate across these criteria:

1. **IT Strategy & Governance (0-10)**: Evaluate their experience developing IT strategies, governance frameworks, and aligning IT with business objectives.

2. **Enterprise Systems Experience (0-10)**: Assess their experience with enterprise-scale systems, infrastructure, and digital transformation initiatives.

3. **Budget & Resource Management (0-10)**: Consider their experience managing IT budgets, vendor relationships, and resource allocation.

4. **Risk Management & Compliance (0-10)**: Evaluate their understanding of IT risk management, security, and regulatory compliance.

5. **Stakeholder Communication (0-10)**: Assess their ability to communicate with executives and translate technical concepts to business stakeholders.

**Overall CIO Fit Score (0-10)**: Provide an overall assessment of their suitability for a CIO role.

For each score, provide a brief justification based on specific evidence from their LinkedIn profile. Focus on concrete examples from their work experience, education, and achievements.

Respond in valid JSON format with numeric scores and string explanations.'
);

-- CISO Evaluation Template
INSERT INTO prompt_templates (name, category, description, prompt_text) VALUES (
    'Fortium CISO Evaluation', 
    'CISO',
    'Standard evaluation criteria for CISO candidates',
    'You are evaluating a candidate for a Chief Information Security Officer (CISO) position. Based on the LinkedIn profile data provided, assess the candidate across these criteria:

1. **Cybersecurity Expertise (0-10)**: Evaluate their depth of cybersecurity knowledge, certifications, and hands-on security experience.

2. **Risk Management (0-10)**: Assess their experience identifying, assessing, and mitigating information security risks.

3. **Compliance & Governance (0-10)**: Consider their knowledge of security frameworks, regulations, and governance practices.

4. **Incident Response (0-10)**: Evaluate their experience with security incident response, crisis management, and business continuity.

5. **Strategic Security Leadership (0-10)**: Assess their ability to develop security strategies and lead security transformation initiatives.

**Overall CISO Fit Score (0-10)**: Provide an overall assessment of their suitability for a CISO role.

For each score, provide a brief justification based on specific evidence from their LinkedIn profile. Focus on concrete examples from their work experience, education, and achievements.

Respond in valid JSON format with numeric scores and string explanations.'
);
```

## Migration Strategy

### Migration File Structure

Following the existing pattern (`supabase/migrations/YYYYMMDDHHMMSS_description.sql`):

```
supabase/migrations/20250813120000_add_prompt_templates.sql
```

### Migration Content

```sql
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

-- Insert default templates
INSERT INTO prompt_templates (name, category, description, prompt_text) VALUES
    ('Fortium CTO Evaluation', 'CTO', 'Standard evaluation criteria for CTO candidates', '[CTO_PROMPT_TEXT]'),
    ('Fortium CIO Evaluation', 'CIO', 'Standard evaluation criteria for CIO candidates', '[CIO_PROMPT_TEXT]'),
    ('Fortium CISO Evaluation', 'CISO', 'Standard evaluation criteria for CISO candidates', '[CISO_PROMPT_TEXT]');
```

## Data Model Relationships

### Relationship with Existing Tables

```sql
-- Future enhancement: Link templates to scoring jobs
-- This could be added in future versions if needed
-- ALTER TABLE scoring_jobs ADD COLUMN template_id UUID;
-- ALTER TABLE scoring_jobs ADD CONSTRAINT fk_scoring_jobs_template 
--     FOREIGN KEY (template_id) REFERENCES prompt_templates(id);
```

### Query Patterns

Common queries the application will perform:

```sql
-- Get all active templates by category
SELECT * FROM prompt_templates 
WHERE category = 'CTO' AND is_active = true 
ORDER BY created_at DESC;

-- Get template by ID
SELECT * FROM prompt_templates WHERE id = $1;

-- Get all active templates
SELECT id, name, category, description, created_at 
FROM prompt_templates 
WHERE is_active = true 
ORDER BY category, name;

-- Update template (application will handle updated_at via trigger)
UPDATE prompt_templates 
SET name = $1, prompt_text = $2, description = $3 
WHERE id = $4;
```

## Performance Considerations

### Expected Data Volume
- **Low Volume**: Estimated 10-50 templates initially
- **Growth Rate**: Slow growth, maybe 2-5 new templates per month
- **Query Patterns**: Primarily read operations (95% reads, 5% writes)

### Index Strategy
- Primary key lookups for template retrieval
- Category filtering for UI template selection
- Active status filtering for operational templates
- Creation date ordering for admin interfaces

### Optimization Notes
- JSONB metadata field allows flexible extension without schema changes
- Text fields sized appropriately (prompt_text as TEXT for long prompts)
- Minimal indexes to balance query performance with write overhead
