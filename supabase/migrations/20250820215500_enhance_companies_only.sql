-- Enhancement of companies table to support CanonicalCompany model
-- This migration adds missing fields and improves indexing for better performance

-- Add missing fields to companies table
ALTER TABLE companies 
ADD COLUMN IF NOT EXISTS tagline TEXT,
ADD COLUMN IF NOT EXISTS domain TEXT,
ADD COLUMN IF NOT EXISTS logo_url TEXT,
ADD COLUMN IF NOT EXISTS specialties TEXT,
ADD COLUMN IF NOT EXISTS follower_count INTEGER,
ADD COLUMN IF NOT EXISTS hq_address_line1 TEXT,
ADD COLUMN IF NOT EXISTS hq_address_line2 TEXT,
ADD COLUMN IF NOT EXISTS hq_postalcode TEXT,
ADD COLUMN IF NOT EXISTS hq_full_address TEXT,
ADD COLUMN IF NOT EXISTS email TEXT,
ADD COLUMN IF NOT EXISTS phone TEXT,
ADD COLUMN IF NOT EXISTS affiliated_companies JSONB DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS raw_data JSONB,
ADD COLUMN IF NOT EXISTS timestamp TIMESTAMPTZ DEFAULT NOW();

-- Add constraints for data integrity
DO $$ 
BEGIN
    -- Add email constraint if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'check_email_format') THEN
        ALTER TABLE companies
        ADD CONSTRAINT check_email_format 
        CHECK (email IS NULL OR email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$');
    END IF;

    -- Add employee count constraint if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'check_employee_count_non_negative') THEN
        ALTER TABLE companies
        ADD CONSTRAINT check_employee_count_non_negative
        CHECK (employee_count IS NULL OR employee_count >= 0);
    END IF;

    -- Add follower count constraint if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'check_follower_count_non_negative') THEN
        ALTER TABLE companies
        ADD CONSTRAINT check_follower_count_non_negative  
        CHECK (follower_count IS NULL OR follower_count >= 0);
    END IF;

    -- Add year founded constraint if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'check_year_founded_reasonable') THEN
        ALTER TABLE companies
        ADD CONSTRAINT check_year_founded_reasonable
        CHECK (year_founded IS NULL OR (year_founded >= 1600 AND year_founded <= EXTRACT(YEAR FROM NOW()) + 1));
    END IF;

    -- Add company name constraint if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'check_company_name_not_empty') THEN
        ALTER TABLE companies
        ADD CONSTRAINT check_company_name_not_empty
        CHECK (char_length(trim(company_name)) > 0);
    END IF;
END $$;

-- Create indexes for enhanced querying performance

-- Domain search index
CREATE INDEX IF NOT EXISTS idx_companies_domain 
ON companies(domain) 
WHERE domain IS NOT NULL;

-- Email search index  
CREATE INDEX IF NOT EXISTS idx_companies_email
ON companies(email)
WHERE email IS NOT NULL;

-- HQ location compound index
CREATE INDEX IF NOT EXISTS idx_companies_hq_location
ON companies(hq_city, hq_region, hq_country)
WHERE hq_city IS NOT NULL OR hq_region IS NOT NULL OR hq_country IS NOT NULL;

-- Employee count range index for size-based queries
CREATE INDEX IF NOT EXISTS idx_companies_employee_count_range
ON companies(employee_count)
WHERE employee_count IS NOT NULL;

-- Year founded index for age-based queries
CREATE INDEX IF NOT EXISTS idx_companies_year_founded
ON companies(year_founded)
WHERE year_founded IS NOT NULL;

-- Follower count index
CREATE INDEX IF NOT EXISTS idx_companies_follower_count
ON companies(follower_count)
WHERE follower_count IS NOT NULL;

-- JSONB indexes for nested data queries

-- Funding info JSONB index for funding queries
CREATE INDEX IF NOT EXISTS idx_companies_funding_info_gin
ON companies USING GIN(funding_info)
WHERE funding_info IS NOT NULL;

-- Locations JSONB index for location queries
CREATE INDEX IF NOT EXISTS idx_companies_locations_gin  
ON companies USING GIN(locations)
WHERE locations IS NOT NULL AND locations != '[]'::jsonb;

-- Affiliated companies JSONB index
CREATE INDEX IF NOT EXISTS idx_companies_affiliated_companies_gin
ON companies USING GIN(affiliated_companies)
WHERE affiliated_companies IS NOT NULL AND affiliated_companies != '[]'::jsonb;

-- Raw data JSONB index for flexible queries
CREATE INDEX IF NOT EXISTS idx_companies_raw_data_gin
ON companies USING GIN(raw_data)
WHERE raw_data IS NOT NULL;

-- Specialties text search index
CREATE INDEX IF NOT EXISTS idx_companies_specialties_gin
ON companies USING GIN(to_tsvector('english', specialties))
WHERE specialties IS NOT NULL;

-- Compound indexes for common query patterns

-- Company name + domain for duplicate detection
CREATE INDEX IF NOT EXISTS idx_companies_name_domain
ON companies(company_name, domain);

-- Location + size for company search
CREATE INDEX IF NOT EXISTS idx_companies_location_size
ON companies(hq_city, hq_country, employee_count);

-- Add comments for documentation
COMMENT ON COLUMN companies.tagline IS 'Company tagline or short slogan';
COMMENT ON COLUMN companies.domain IS 'Website domain (auto-extracted from website URL)';
COMMENT ON COLUMN companies.logo_url IS 'URL to company logo image';
COMMENT ON COLUMN companies.specialties IS 'Comma-separated list of company specialties';
COMMENT ON COLUMN companies.follower_count IS 'Number of LinkedIn followers';
COMMENT ON COLUMN companies.hq_address_line1 IS 'Headquarters address line 1';
COMMENT ON COLUMN companies.hq_address_line2 IS 'Headquarters address line 2';
COMMENT ON COLUMN companies.hq_postalcode IS 'Headquarters postal/ZIP code';
COMMENT ON COLUMN companies.hq_full_address IS 'Full headquarters address string';
COMMENT ON COLUMN companies.email IS 'Company contact email address';
COMMENT ON COLUMN companies.phone IS 'Company contact phone number';
COMMENT ON COLUMN companies.affiliated_companies IS 'JSONB array of affiliated companies (subsidiaries, parents, etc.)';
COMMENT ON COLUMN companies.raw_data IS 'Original raw data from data provider (Cassidy, etc.)';
COMMENT ON COLUMN companies.timestamp IS 'Timestamp when company data was processed/ingested';
