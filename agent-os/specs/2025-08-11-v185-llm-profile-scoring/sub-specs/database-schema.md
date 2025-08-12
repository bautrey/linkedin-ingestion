# Database Schema

This is the database schema implementation for the spec detailed in @agent-os/specs/2025-08-11-v185-llm-profile-scoring/spec.md

> Created: 2025-08-11
> Version: 1.0.0

## Database Changes

### New Tables

#### scoring_jobs
Table to track asynchronous LLM scoring job status and results.

### SQL Schema

```sql
-- Create scoring_jobs table for LLM evaluation job tracking
CREATE TABLE scoring_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
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
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Create indexes for efficient querying
CREATE INDEX idx_scoring_jobs_profile_id ON scoring_jobs(profile_id);
CREATE INDEX idx_scoring_jobs_status ON scoring_jobs(status);
CREATE INDEX idx_scoring_jobs_created_at ON scoring_jobs(created_at DESC);

-- Create composite index for job polling
CREATE INDEX idx_scoring_jobs_status_updated ON scoring_jobs(status, updated_at DESC);

-- Add RLS policy for data access control
ALTER TABLE scoring_jobs ENABLE ROW LEVEL SECURITY;

-- Policy: Users can access scoring jobs for profiles they have access to
CREATE POLICY scoring_jobs_access_policy ON scoring_jobs
    FOR ALL USING (profile_id IN (
        SELECT id FROM profiles WHERE 
        -- Inherit profile access permissions
        true -- Replace with actual profile access logic
    ));
```

### Migration Strategy

#### Forward Migration (Up)
```sql
-- Create the scoring_jobs table with all constraints and indexes
-- This is a new table, so no data migration needed
BEGIN;

-- Table creation (from schema above)
-- Index creation (from schema above)  
-- RLS policies (from schema above)

COMMIT;
```

#### Reverse Migration (Down)
```sql
-- Remove scoring_jobs table and related objects
BEGIN;

DROP TABLE IF EXISTS scoring_jobs CASCADE;

COMMIT;
```

## Data Integrity Rules

### Constraints
- `profile_id` must reference existing profile
- `status` must be one of: 'pending', 'processing', 'completed', 'failed'
- `prompt` cannot be empty
- `model_name` must be valid OpenAI model identifier
- `retry_count` cannot exceed maximum retry limit (5)

### Business Rules
- Jobs older than 7 days should be automatically cleaned up
- Maximum 10 concurrent scoring jobs per profile to prevent resource abuse
- Failed jobs with retry_count < 5 can be retried
- Completed jobs should cache results for 24 hours to prevent duplicate LLM calls

## Performance Considerations

### Indexes
- Primary key (id) for unique identification
- profile_id index for retrieving jobs by profile
- status index for filtering active/completed jobs
- Composite status+updated_at for efficient job polling

### Optimization
- JSONB columns for flexible LLM response storage with query capabilities
- Partitioning by created_at (monthly) if job volume becomes high
- Automatic cleanup job for old completed/failed records
