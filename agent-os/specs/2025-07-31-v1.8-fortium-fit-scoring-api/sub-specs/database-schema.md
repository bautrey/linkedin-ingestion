# V1.8 Database Schema - Fortium Fit Scoring

## New Tables

### scoring_algorithms
```sql
CREATE TABLE scoring_algorithms (
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
```

### scoring_thresholds
```sql
CREATE TABLE scoring_thresholds (
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
```

### profile_scores
```sql
CREATE TABLE profile_scores (
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
    FOREIGN KEY (profile_id) REFERENCES profiles(profile_id),
    INDEX(profile_id, role, scored_at)
);
```

### scoring_categories
```sql
CREATE TABLE scoring_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    weight DECIMAL(3,2) NOT NULL DEFAULT 1.0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## Initial Seed Data

### Scoring Categories
- technical_leadership
- industry_experience  
- company_scale
- education_background
- career_progression

### Default Thresholds (per role)
- excellent: 0.85-1.0
- good: 0.70-0.84
- fair: 0.50-0.69
- poor: 0.0-0.49

## Migration Strategy

1. Create tables in development
2. Populate seed data
3. Test with existing profiles
4. Deploy to production
5. Verify data integrity
