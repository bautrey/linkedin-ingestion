-- V1.88 Template Integration - Add template_id to scoring_jobs
-- Adds template_id reference to scoring_jobs table for template-based scoring

-- Add template_id column to scoring_jobs table
ALTER TABLE scoring_jobs 
ADD COLUMN template_id UUID REFERENCES prompt_templates(id) ON DELETE SET NULL;

-- Create index for efficient template-based job queries
CREATE INDEX IF NOT EXISTS idx_scoring_jobs_template_id ON scoring_jobs(template_id);

-- Add comment to document the column purpose
COMMENT ON COLUMN scoring_jobs.template_id IS 'Reference to prompt template used for scoring (optional, for template-based scoring)';

-- The column is nullable to maintain backward compatibility with existing prompt-based scoring jobs
