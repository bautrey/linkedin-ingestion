-- V1.8 Fortium Fit Scoring API Database Schema
-- Migration for scoring tables and seed data

-- Create scoring_categories table
CREATE TABLE IF NOT EXISTS scoring_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    weight DECIMAL(3,2) NOT NULL DEFAULT 1.0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create scoring_algorithms table
CREATE TABLE IF NOT EXISTS scoring_algorithms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role VARCHAR(50) NOT NULL, -- CIO, CTO, CISO
    category VARCHAR(100) NOT NULL, -- technical_leadership, industry_experience, etc.
    algorithm_config JSONB NOT NULL, -- scoring logic and weights
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,
    UNIQUE(role, category, version)
);

-- Create scoring_thresholds table
CREATE TABLE IF NOT EXISTS scoring_thresholds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role VARCHAR(50) NOT NULL,
    threshold_type VARCHAR(50) NOT NULL, -- excellent, good, fair, poor
    min_score DECIMAL(3,2) NOT NULL,
    max_score DECIMAL(3,2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,
    UNIQUE(role, threshold_type)
);

-- Create profile_scores table
CREATE TABLE IF NOT EXISTS profile_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,
    overall_score DECIMAL(3,2) NOT NULL,
    category_scores JSONB NOT NULL,
    summary TEXT,
    recommendations JSONB,
    alternative_roles JSONB,
    algorithm_version INTEGER NOT NULL,
    scored_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    FOREIGN KEY (profile_id) REFERENCES linkedin_profiles(linkedin_id)
);

-- Create index on profile_scores for performance
CREATE INDEX IF NOT EXISTS idx_profile_scores_profile_role_date 
ON profile_scores(profile_id, role, scored_at);

-- Insert seed data for scoring categories
INSERT INTO scoring_categories (name, description, weight) VALUES
    ('technical_leadership', 'Technical leadership and architecture experience', 1.0),
    ('industry_experience', 'Relevant industry and domain experience', 1.0),
    ('company_scale', 'Experience at companies of appropriate scale', 1.0),
    ('education_background', 'Educational qualifications and continuous learning', 0.8),
    ('career_progression', 'Career advancement and role progression', 0.9)
ON CONFLICT (name) DO NOTHING;

-- Insert seed data for scoring thresholds (CTO)
INSERT INTO scoring_thresholds (role, threshold_type, min_score, max_score) VALUES
    ('CTO', 'excellent', 0.85, 1.00),
    ('CTO', 'good', 0.70, 0.84),
    ('CTO', 'fair', 0.50, 0.69),
    ('CTO', 'poor', 0.00, 0.49)
ON CONFLICT (role, threshold_type) DO NOTHING;

-- Insert seed data for scoring thresholds (CIO)
INSERT INTO scoring_thresholds (role, threshold_type, min_score, max_score) VALUES
    ('CIO', 'excellent', 0.85, 1.00),
    ('CIO', 'good', 0.70, 0.84),
    ('CIO', 'fair', 0.50, 0.69),
    ('CIO', 'poor', 0.00, 0.49)
ON CONFLICT (role, threshold_type) DO NOTHING;

-- Insert seed data for scoring thresholds (CISO)
INSERT INTO scoring_thresholds (role, threshold_type, min_score, max_score) VALUES
    ('CISO', 'excellent', 0.85, 1.00),
    ('CISO', 'good', 0.70, 0.84),
    ('CISO', 'fair', 0.50, 0.69),
    ('CISO', 'poor', 0.00, 0.49)
ON CONFLICT (role, threshold_type) DO NOTHING;

-- Insert seed data for scoring algorithms (CTO)
INSERT INTO scoring_algorithms (role, category, algorithm_config, version) VALUES
    ('CTO', 'technical_leadership', '{"keywords": ["CTO", "Chief Technology Officer", "VP Engineering", "Head of Engineering"], "experience_weight": 0.4, "title_weight": 0.3, "company_weight": 0.3}', 1),
    ('CTO', 'industry_experience', '{"tech_keywords": ["software", "technology", "engineering", "development"], "years_weight": 0.6, "relevance_weight": 0.4}', 1),
    ('CTO', 'company_scale', '{"size_multipliers": {"startup": 0.8, "mid": 1.0, "enterprise": 1.2}, "employee_ranges": {"1-50": 0.8, "51-500": 1.0, "500+": 1.2}}', 1),
    ('CTO', 'education_background', '{"degrees": {"BS": 0.8, "MS": 1.0, "PhD": 1.2}, "fields": ["Computer Science", "Engineering", "Technology"]}', 1),
    ('CTO', 'career_progression', '{"progression_bonus": 0.2, "leadership_roles": ["CTO", "VP", "Director", "Lead"]}', 1)
ON CONFLICT (role, category, version) DO NOTHING;

-- Insert seed data for scoring algorithms (CIO)
INSERT INTO scoring_algorithms (role, category, algorithm_config, version) VALUES
    ('CIO', 'technical_leadership', '{"keywords": ["CIO", "Chief Information Officer", "VP Information", "Head of IT"], "experience_weight": 0.4, "title_weight": 0.3, "company_weight": 0.3}', 1),
    ('CIO', 'industry_experience', '{"tech_keywords": ["information systems", "IT", "digital transformation", "enterprise"], "years_weight": 0.6, "relevance_weight": 0.4}', 1),
    ('CIO', 'company_scale', '{"size_multipliers": {"startup": 0.7, "mid": 1.0, "enterprise": 1.3}, "employee_ranges": {"1-50": 0.7, "51-500": 1.0, "500+": 1.3}}', 1),
    ('CIO', 'education_background', '{"degrees": {"BS": 0.8, "MS": 1.0, "PhD": 1.1, "MBA": 1.2}, "fields": ["Information Systems", "Business", "Technology"]}', 1),
    ('CIO', 'career_progression', '{"progression_bonus": 0.2, "leadership_roles": ["CIO", "VP", "Director", "Manager"]}', 1)
ON CONFLICT (role, category, version) DO NOTHING;

-- Insert seed data for scoring algorithms (CISO)
INSERT INTO scoring_algorithms (role, category, algorithm_config, version) VALUES
    ('CISO', 'technical_leadership', '{"keywords": ["CISO", "Chief Information Security Officer", "VP Security", "Head of Security"], "experience_weight": 0.4, "title_weight": 0.3, "company_weight": 0.3}', 1),
    ('CISO', 'industry_experience', '{"tech_keywords": ["security", "cybersecurity", "information security", "risk"], "years_weight": 0.6, "relevance_weight": 0.4}', 1),
    ('CISO', 'company_scale', '{"size_multipliers": {"startup": 0.9, "mid": 1.0, "enterprise": 1.1}, "employee_ranges": {"1-50": 0.9, "51-500": 1.0, "500+": 1.1}}', 1),
    ('CISO', 'education_background', '{"degrees": {"BS": 0.8, "MS": 1.0, "PhD": 1.1}, "fields": ["Computer Science", "Cybersecurity", "Information Security"], "certifications": ["CISSP", "CISM", "CISA"]}', 1),
    ('CISO', 'career_progression', '{"progression_bonus": 0.2, "leadership_roles": ["CISO", "VP", "Director", "Manager"]}', 1)
ON CONFLICT (role, category, version) DO NOTHING;
