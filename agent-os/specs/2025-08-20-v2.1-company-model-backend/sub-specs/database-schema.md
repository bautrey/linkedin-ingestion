# Database Schema

This is the database schema implementation for the spec detailed in @agent-os/specs/2025-08-20-v2.1-company-model-backend/spec.md

> Created: 2025-08-20
> Version: 1.0.0

## Schema Changes

### New Tables

#### companies
```sql
CREATE TABLE companies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    linkedin_company_url VARCHAR(500) UNIQUE,
    name VARCHAR(255) NOT NULL,
    employee_count INTEGER,
    employee_range VARCHAR(50),
    industries JSONB,
    specialties TEXT,
    funding_info JSONB,
    locations JSONB,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### profile_companies (Junction Table)
```sql
CREATE TABLE profile_companies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    profile_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    position_title VARCHAR(255),
    start_date DATE,
    end_date DATE,
    is_current BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(profile_id, company_id, position_title, start_date)
);
```

### Table Modifications

#### profiles (No structural changes required)
- Existing table maintains current structure
- Company relationships handled through junction table
- Work experience data enhanced with company_id references

## Indexes and Constraints

### Performance Indexes
```sql
-- Company lookup optimization
CREATE INDEX idx_companies_linkedin_url ON companies(linkedin_company_url);
CREATE INDEX idx_companies_name ON companies(name);
CREATE INDEX idx_companies_employee_count ON companies(employee_count);

-- Profile-company relationship optimization
CREATE INDEX idx_profile_companies_profile_id ON profile_companies(profile_id);
CREATE INDEX idx_profile_companies_company_id ON profile_companies(company_id);
CREATE INDEX idx_profile_companies_current ON profile_companies(is_current) WHERE is_current = TRUE;

-- JSONB field optimization for querying
CREATE INDEX idx_companies_industries_gin ON companies USING GIN(industries);
CREATE INDEX idx_companies_locations_gin ON companies USING GIN(locations);
```

### Foreign Key Relationships
```sql
-- Profile-Company many-to-many relationship
ALTER TABLE profile_companies 
    ADD CONSTRAINT fk_profile_companies_profile 
    FOREIGN KEY (profile_id) REFERENCES profiles(id) ON DELETE CASCADE;

ALTER TABLE profile_companies 
    ADD CONSTRAINT fk_profile_companies_company 
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE;
```

### Data Integrity Constraints
```sql
-- Ensure employee count is non-negative
ALTER TABLE companies 
    ADD CONSTRAINT chk_employee_count_positive 
    CHECK (employee_count IS NULL OR employee_count >= 0);

-- Ensure date consistency in work experience
ALTER TABLE profile_companies 
    ADD CONSTRAINT chk_date_consistency 
    CHECK (start_date IS NULL OR end_date IS NULL OR start_date <= end_date);

-- Ensure company name is not empty
ALTER TABLE companies 
    ADD CONSTRAINT chk_company_name_not_empty 
    CHECK (TRIM(name) != '');
```

## Migration Scripts

### Migration Up: V2.1_add_company_model.sql
```sql
-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create companies table
CREATE TABLE companies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    linkedin_company_url VARCHAR(500) UNIQUE,
    name VARCHAR(255) NOT NULL,
    employee_count INTEGER,
    employee_range VARCHAR(50),
    industries JSONB,
    specialties TEXT,
    funding_info JSONB,
    locations JSONB,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT chk_employee_count_positive CHECK (employee_count IS NULL OR employee_count >= 0),
    CONSTRAINT chk_company_name_not_empty CHECK (TRIM(name) != '')
);

-- Create profile_companies junction table
CREATE TABLE profile_companies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    profile_id UUID NOT NULL,
    company_id UUID NOT NULL,
    position_title VARCHAR(255),
    start_date DATE,
    end_date DATE,
    is_current BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT fk_profile_companies_profile FOREIGN KEY (profile_id) REFERENCES profiles(id) ON DELETE CASCADE,
    CONSTRAINT fk_profile_companies_company FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
    CONSTRAINT chk_date_consistency CHECK (start_date IS NULL OR end_date IS NULL OR start_date <= end_date),
    UNIQUE(profile_id, company_id, position_title, start_date)
);

-- Create performance indexes
CREATE INDEX idx_companies_linkedin_url ON companies(linkedin_company_url);
CREATE INDEX idx_companies_name ON companies(name);
CREATE INDEX idx_companies_employee_count ON companies(employee_count);
CREATE INDEX idx_companies_industries_gin ON companies USING GIN(industries);
CREATE INDEX idx_companies_locations_gin ON companies USING GIN(locations);

CREATE INDEX idx_profile_companies_profile_id ON profile_companies(profile_id);
CREATE INDEX idx_profile_companies_company_id ON profile_companies(company_id);
CREATE INDEX idx_profile_companies_current ON profile_companies(is_current) WHERE is_current = TRUE;

-- Create updated_at trigger for companies
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_companies_updated_at BEFORE UPDATE ON companies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### Migration Down: V2.1_remove_company_model.sql
```sql
-- Drop triggers
DROP TRIGGER IF EXISTS update_companies_updated_at ON companies;
DROP FUNCTION IF EXISTS update_updated_at_column();

-- Drop indexes
DROP INDEX IF EXISTS idx_profile_companies_current;
DROP INDEX IF EXISTS idx_profile_companies_company_id;
DROP INDEX IF EXISTS idx_profile_companies_profile_id;
DROP INDEX IF EXISTS idx_companies_locations_gin;
DROP INDEX IF EXISTS idx_companies_industries_gin;
DROP INDEX IF EXISTS idx_companies_employee_count;
DROP INDEX IF EXISTS idx_companies_name;
DROP INDEX IF EXISTS idx_companies_linkedin_url;

-- Drop tables (CASCADE will handle foreign keys)
DROP TABLE IF EXISTS profile_companies CASCADE;
DROP TABLE IF EXISTS companies CASCADE;
```

## Data Population Strategy

### Company Data Extraction from Existing Profiles
```sql
-- Query to identify companies that need to be created from existing profile data
-- This will be used to populate companies table from existing work experience data
WITH company_data AS (
    SELECT DISTINCT 
        jsonb_array_elements(work_experience) ->> 'company_linkedin_url' as linkedin_url,
        jsonb_array_elements(work_experience) ->> 'company_name' as name
    FROM profiles 
    WHERE work_experience IS NOT NULL 
    AND jsonb_array_length(work_experience) > 0
)
SELECT linkedin_url, name 
FROM company_data 
WHERE linkedin_url IS NOT NULL 
AND name IS NOT NULL
ORDER BY name;
```

### Profile-Company Relationship Population
```sql
-- Query to establish profile-company relationships from existing work experience data
-- This will populate the junction table during migration
INSERT INTO profile_companies (profile_id, company_id, position_title, start_date, end_date, is_current)
SELECT 
    p.id as profile_id,
    c.id as company_id,
    we.value ->> 'position_title' as position_title,
    CASE 
        WHEN we.value ->> 'start_date' != '' 
        THEN (we.value ->> 'start_date')::DATE 
        ELSE NULL 
    END as start_date,
    CASE 
        WHEN we.value ->> 'end_date' != '' 
        THEN (we.value ->> 'end_date')::DATE 
        ELSE NULL 
    END as end_date,
    COALESCE((we.value ->> 'is_current')::BOOLEAN, FALSE) as is_current
FROM profiles p
CROSS JOIN LATERAL jsonb_array_elements(p.work_experience) we
JOIN companies c ON c.linkedin_company_url = we.value ->> 'company_linkedin_url'
WHERE p.work_experience IS NOT NULL;
```

## Performance Rationale

### JSONB Fields
- **industries**: Array of industry strings, optimized for containment queries (`@>` operator)
- **funding_info**: Nested object with funding rounds, valuations, and investment data
- **locations**: Array of location objects with address, city, country, and geographic data
- **GIN indexes**: Enable fast searches within JSONB fields for industry and location filtering

### Unique Constraints
- **companies.linkedin_company_url**: Prevents duplicate company records
- **profile_companies composite unique**: Prevents duplicate work experience relationships while allowing multiple positions at the same company

### Relationship Design
- **Many-to-many**: Profiles can work at multiple companies, companies can have multiple employees
- **Junction table attributes**: Captures work experience details (position, dates, current status)
- **Cascade deletions**: Maintains referential integrity when profiles or companies are removed

## Data Integrity Rules

### Company Validation
- **Name Required**: All companies must have a non-empty name
- **Employee Count**: Must be non-negative integer if provided
- **LinkedIn URL**: Must be unique across all companies if provided

### Work Experience Validation  
- **Date Consistency**: Start date must precede end date when both are provided
- **Unique Relationships**: Prevents duplicate entries for same person at same company in same role with same start date
- **Current Position**: Boolean flag for active employment status
