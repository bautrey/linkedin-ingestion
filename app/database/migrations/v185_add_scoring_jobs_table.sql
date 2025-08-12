-- V1.85 LLM Scoring Jobs Table Migration
-- Creates scoring_jobs table for tracking asynchronous LLM scoring operations

BEGIN;

-- Create scoring_jobs table for LLM evaluation job tracking
CREATE TABLE IF NOT EXISTS scoring_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID NOT NULL REFERENCES linkedin_profiles(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    prompt TEXT NOT NULL,
    model_name VARCHAR(50) NOT NULL DEFAULT 'gpt-3.5-turbo',
    
    -- LLM Response Data
    llm_response JSONB,
    parsed_score JSONB,
    
    -- Error Handling
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    
    -- Constraints
    CONSTRAINT valid_status CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    CONSTRAINT valid_retry_count CHECK (retry_count >= 0 AND retry_count <= 10),
    CONSTRAINT non_empty_prompt CHECK (char_length(trim(prompt)) > 0)
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_scoring_jobs_profile_id ON scoring_jobs(profile_id);
CREATE INDEX IF NOT EXISTS idx_scoring_jobs_status ON scoring_jobs(status);
CREATE INDEX IF NOT EXISTS idx_scoring_jobs_created_at ON scoring_jobs(created_at DESC);

-- Create composite index for job polling (most common query pattern)
CREATE INDEX IF NOT EXISTS idx_scoring_jobs_status_updated ON scoring_jobs(status, updated_at DESC);

-- Create index for profile-specific job retrieval
CREATE INDEX IF NOT EXISTS idx_scoring_jobs_profile_created ON scoring_jobs(profile_id, created_at DESC);

-- Add trigger to automatically update updated_at timestamp
CREATE TRIGGER IF NOT EXISTS update_scoring_jobs_updated_at 
    BEFORE UPDATE ON scoring_jobs 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Add RLS policy for data access control
ALTER TABLE scoring_jobs ENABLE ROW LEVEL SECURITY;

-- Policy: Users can access scoring jobs for profiles they have access to
-- Note: This inherits the same access pattern as linkedin_profiles
CREATE POLICY scoring_jobs_access_policy ON scoring_jobs
    FOR ALL USING (profile_id IN (
        SELECT id FROM linkedin_profiles WHERE 
        -- For now, allow all access - can be restricted later
        true
    ));

COMMIT;
