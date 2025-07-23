-- LinkedIn Ingestion Database Schema
-- Requires pgvector extension for vector similarity search

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- LinkedIn Profiles table
CREATE TABLE IF NOT EXISTS linkedin_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    linkedin_id TEXT UNIQUE NOT NULL,
    name TEXT,
    url TEXT,
    position TEXT,
    about TEXT,
    city TEXT,
    country_code TEXT,
    followers INTEGER,
    connections INTEGER,
    experience JSONB DEFAULT '[]'::jsonb,
    education JSONB DEFAULT '[]'::jsonb,
    certifications JSONB DEFAULT '[]'::jsonb,
    current_company JSONB,
    timestamp TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    embedding vector(1536)  -- OpenAI embedding dimension
);

-- Companies table
CREATE TABLE IF NOT EXISTS companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    linkedin_company_id TEXT UNIQUE NOT NULL,
    company_name TEXT NOT NULL,
    description TEXT,
    website TEXT,
    linkedin_url TEXT,
    employee_count INTEGER,
    employee_range TEXT,
    year_founded INTEGER,
    industries TEXT[],
    hq_city TEXT,
    hq_region TEXT,
    hq_country TEXT,
    locations JSONB DEFAULT '[]'::jsonb,
    funding_info JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    embedding vector(1536)  -- OpenAI embedding dimension
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_linkedin_profiles_linkedin_id ON linkedin_profiles(linkedin_id);
CREATE INDEX IF NOT EXISTS idx_linkedin_profiles_created_at ON linkedin_profiles(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_linkedin_profiles_name ON linkedin_profiles(name);
CREATE INDEX IF NOT EXISTS idx_linkedin_profiles_city ON linkedin_profiles(city);
CREATE INDEX IF NOT EXISTS idx_linkedin_profiles_country_code ON linkedin_profiles(country_code);

CREATE INDEX IF NOT EXISTS idx_companies_linkedin_company_id ON companies(linkedin_company_id);
CREATE INDEX IF NOT EXISTS idx_companies_created_at ON companies(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_companies_company_name ON companies(company_name);
CREATE INDEX IF NOT EXISTS idx_companies_industries ON companies USING GIN(industries);

-- Vector similarity search indexes (HNSW for fast approximate search)
CREATE INDEX IF NOT EXISTS idx_linkedin_profiles_embedding ON linkedin_profiles 
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

CREATE INDEX IF NOT EXISTS idx_companies_embedding ON companies 
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Function to match similar profiles using vector similarity
CREATE OR REPLACE FUNCTION match_profiles(
    query_embedding vector(1536),
    match_threshold float DEFAULT 0.2,
    match_count int DEFAULT 10
)
RETURNS TABLE (
    id uuid,
    linkedin_id text,
    name text,
    position text,
    city text,
    country_code text,
    similarity float
)
LANGUAGE sql STABLE
AS $$
    SELECT
        p.id,
        p.linkedin_id,
        p.name,
        p.position,
        p.city,
        p.country_code,
        1 - (p.embedding <=> query_embedding) as similarity
    FROM linkedin_profiles p
    WHERE p.embedding IS NOT NULL
    AND 1 - (p.embedding <=> query_embedding) > match_threshold
    ORDER BY p.embedding <=> query_embedding
    LIMIT match_count;
$$;

-- Function to match similar companies using vector similarity
CREATE OR REPLACE FUNCTION match_companies(
    query_embedding vector(1536),
    match_threshold float DEFAULT 0.2,
    match_count int DEFAULT 10
)
RETURNS TABLE (
    id uuid,
    linkedin_company_id text,
    company_name text,
    description text,
    industries text[],
    similarity float
)
LANGUAGE sql STABLE
AS $$
    SELECT
        c.id,
        c.linkedin_company_id,
        c.company_name,
        c.description,
        c.industries,
        1 - (c.embedding <=> query_embedding) as similarity
    FROM companies c
    WHERE c.embedding IS NOT NULL
    AND 1 - (c.embedding <=> query_embedding) > match_threshold
    ORDER BY c.embedding <=> query_embedding
    LIMIT match_count;
$$;

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_linkedin_profiles_updated_at 
    BEFORE UPDATE ON linkedin_profiles 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_companies_updated_at 
    BEFORE UPDATE ON companies 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Row Level Security (RLS) policies can be added here if needed
-- ALTER TABLE linkedin_profiles ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE companies ENABLE ROW LEVEL SECURITY;
