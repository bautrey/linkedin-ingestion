
-- Seed data for V1.8 scoring system
-- Execute this after creating the tables

-- Insert scoring categories
INSERT INTO scoring_categories (name, description, weight) VALUES
    ('technical_leadership', 'Technical leadership and architecture experience', 1.0),
    ('industry_experience', 'Relevant industry and domain experience', 1.0),
    ('company_scale', 'Experience at companies of appropriate scale', 1.0),
    ('education_background', 'Educational qualifications and continuous learning', 0.8),
    ('career_progression', 'Career advancement and role progression', 0.9)
ON CONFLICT (name) DO NOTHING;

-- Insert scoring thresholds for all roles
INSERT INTO scoring_thresholds (role, threshold_type, min_score, max_score) VALUES
    ('CTO', 'excellent', 0.85, 1.00),
    ('CTO', 'good', 0.70, 0.84),
    ('CTO', 'fair', 0.50, 0.69),
    ('CTO', 'poor', 0.00, 0.49),
    ('CIO', 'excellent', 0.85, 1.00),
    ('CIO', 'good', 0.70, 0.84),
    ('CIO', 'fair', 0.50, 0.69),
    ('CIO', 'poor', 0.00, 0.49),
    ('CISO', 'excellent', 0.85, 1.00),
    ('CISO', 'good', 0.70, 0.84),
    ('CISO', 'fair', 0.50, 0.69),
    ('CISO', 'poor', 0.00, 0.49)
ON CONFLICT (role, threshold_type) DO NOTHING;
