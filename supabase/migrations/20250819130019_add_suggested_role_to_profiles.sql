-- Add suggested_role column to profiles table for CIO/CTO/CISO role tracking
-- This allows storing the candidate's suggested role alongside their profile data
-- for use in role-specific scoring templates

-- Add the suggested_role column to linkedin_profiles table
ALTER TABLE linkedin_profiles 
ADD COLUMN suggested_role VARCHAR(10) 
CHECK (suggested_role IN ('CIO', 'CTO', 'CISO') OR suggested_role IS NULL);

-- Add index for role-based queries
CREATE INDEX IF NOT EXISTS idx_linkedin_profiles_suggested_role 
ON linkedin_profiles(suggested_role) 
WHERE suggested_role IS NOT NULL;

-- Add comment for documentation
COMMENT ON COLUMN linkedin_profiles.suggested_role IS 'Candidate''s suggested role for scoring: CIO, CTO, or CISO';
