-- Add profile-company junction table to link profiles with their associated companies
-- This allows us to track which profiles worked at which companies and show company profiles

CREATE TABLE IF NOT EXISTS profile_companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID NOT NULL REFERENCES linkedin_profiles(id) ON DELETE CASCADE,
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    
    -- Relationship details from the profile's experience
    job_title TEXT,
    start_date TEXT, -- LinkedIn dates are often text like "Jan 2020" 
    end_date TEXT,
    duration_text TEXT, -- "2 yrs 3 mos"
    is_current_role BOOLEAN DEFAULT false,
    description TEXT,
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Ensure each profile-company relationship is unique
    UNIQUE(profile_id, company_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_profile_companies_profile_id ON profile_companies(profile_id);
CREATE INDEX IF NOT EXISTS idx_profile_companies_company_id ON profile_companies(company_id);
CREATE INDEX IF NOT EXISTS idx_profile_companies_is_current ON profile_companies(is_current_role);

-- Function to get profiles by company (for showing "X people worked here")
CREATE OR REPLACE FUNCTION get_profiles_for_company(
    target_company_id UUID
)
RETURNS TABLE (
    profile_id UUID,
    profile_name TEXT,
    profile_url TEXT,
    job_title TEXT,
    start_date TEXT,
    end_date TEXT,
    is_current_role BOOLEAN
)
LANGUAGE sql STABLE
AS $$
    SELECT 
        p.id as profile_id,
        p.name as profile_name,
        p.url as profile_url,
        pc.job_title,
        pc.start_date,
        pc.end_date,
        pc.is_current_role
    FROM profile_companies pc
    JOIN linkedin_profiles p ON pc.profile_id = p.id
    WHERE pc.company_id = target_company_id
    ORDER BY pc.is_current_role DESC, pc.end_date DESC NULLS FIRST;
$$;

-- Function to get companies for a profile
CREATE OR REPLACE FUNCTION get_companies_for_profile(
    target_profile_id UUID
)
RETURNS TABLE (
    company_id UUID,
    company_name TEXT,
    company_linkedin_url TEXT,
    job_title TEXT,
    start_date TEXT,
    end_date TEXT,
    is_current_role BOOLEAN
)
LANGUAGE sql STABLE
AS $$
    SELECT 
        c.id as company_id,
        c.company_name,
        c.linkedin_url as company_linkedin_url,
        pc.job_title,
        pc.start_date,
        pc.end_date,
        pc.is_current_role
    FROM profile_companies pc
    JOIN companies c ON pc.company_id = c.id
    WHERE pc.profile_id = target_profile_id
    ORDER BY pc.is_current_role DESC, pc.end_date DESC NULLS FIRST;
$$;
