-- ============================================================================
-- Production Monitoring Queries for Company Processing Consolidation Testing
-- ============================================================================
-- Created: 2025-08-22
-- Purpose: Monitor companies table, profile_companies table, and processing 
--          status during real-time testing of consolidated approach
-- ============================================================================

-- Query 1: Monitor companies table in real-time
-- Shows recently added companies (last 5 minutes)
SELECT 
    id,
    company_name,
    linkedin_url,
    domain,
    employee_count,
    industries,
    hq_city,
    hq_country,
    created_at,
    updated_at
FROM companies 
WHERE created_at >= NOW() - INTERVAL '5 minutes'
ORDER BY created_at DESC;

-- Query 2: Monitor profile processing status
-- Shows recently processed profiles with company processing metadata
SELECT 
    p.id,
    p.name,
    p.url as linkedin_url,
    p.suggested_role,
    p.created_at,
    -- Count of companies associated with this profile
    COUNT(DISTINCT c.id) as companies_count,
    -- List of company names
    STRING_AGG(DISTINCT c.company_name, ', ') as company_names
FROM profiles p
LEFT JOIN profile_companies pc ON p.id = pc.profile_id  
LEFT JOIN companies c ON pc.company_id = c.id
WHERE p.created_at >= NOW() - INTERVAL '10 minutes'
GROUP BY p.id, p.name, p.url, p.suggested_role, p.created_at
ORDER BY p.created_at DESC;

-- Query 3: Monitor profile_companies relationships
-- Shows recent profile-company linkages
SELECT 
    pc.id,
    p.name as profile_name,
    p.url as profile_linkedin_url,
    c.company_name,
    c.linkedin_url as company_linkedin_url,
    pc.position_title,
    pc.start_date,
    pc.end_date,
    pc.is_current,
    pc.created_at
FROM profile_companies pc
JOIN profiles p ON pc.profile_id = p.id
JOIN companies c ON pc.company_id = c.id
WHERE pc.created_at >= NOW() - INTERVAL '10 minutes'
ORDER BY pc.created_at DESC;

-- Query 4: Processing time analysis
-- Monitor how long profile processing is taking
SELECT 
    id,
    name,
    url as linkedin_url,
    created_at,
    EXTRACT(EPOCH FROM (NOW() - created_at)) as processing_age_seconds,
    CASE 
        WHEN EXTRACT(EPOCH FROM (NOW() - created_at)) > 120 THEN '🔴 SLOW (>2min)'
        WHEN EXTRACT(EPOCH FROM (NOW() - created_at)) > 60 THEN '🟡 MEDIUM (>1min)'
        ELSE '🟢 FAST (<1min)'
    END as processing_speed
FROM profiles
WHERE created_at >= NOW() - INTERVAL '30 minutes'
ORDER BY created_at DESC;

-- Query 5: Company processing success rate
-- Monitor success/failure rate of company processing
WITH profile_stats AS (
    SELECT 
        p.id,
        p.name,
        p.created_at,
        COUNT(DISTINCT c.id) as companies_found,
        CASE 
            WHEN COUNT(DISTINCT c.id) > 0 THEN 'SUCCESS'
            ELSE 'NO_COMPANIES'
        END as company_processing_status
    FROM profiles p
    LEFT JOIN profile_companies pc ON p.id = pc.profile_id
    LEFT JOIN companies c ON pc.company_id = c.id
    WHERE p.created_at >= NOW() - INTERVAL '1 hour'
    GROUP BY p.id, p.name, p.created_at
)
SELECT 
    company_processing_status,
    COUNT(*) as profile_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
FROM profile_stats
GROUP BY company_processing_status
ORDER BY profile_count DESC;

-- Query 6: Real-time processing dashboard
-- Single query to show current processing activity
SELECT 
    'PROFILES_LAST_5_MIN' as metric,
    COUNT(*) as count
FROM profiles 
WHERE created_at >= NOW() - INTERVAL '5 minutes'

UNION ALL

SELECT 
    'COMPANIES_LAST_5_MIN' as metric,
    COUNT(*) as count
FROM companies 
WHERE created_at >= NOW() - INTERVAL '5 minutes'

UNION ALL

SELECT 
    'PROFILE_COMPANIES_LAST_5_MIN' as metric,
    COUNT(*) as count
FROM profile_companies 
WHERE created_at >= NOW() - INTERVAL '5 minutes'

UNION ALL

SELECT 
    'SLOW_PROFILES_LAST_30_MIN' as metric,
    COUNT(*) as count
FROM profiles 
WHERE created_at >= NOW() - INTERVAL '30 minutes'
    AND EXTRACT(EPOCH FROM (NOW() - created_at)) > 120;

-- Query 7: Company data quality check
-- Validate company data completeness
SELECT 
    c.id,
    c.company_name,
    c.linkedin_url,
    c.domain,
    c.employee_count,
    c.year_founded,
    c.industries,
    c.hq_city,
    c.hq_country,
    CASE 
        WHEN c.domain IS NULL THEN '❌ Missing domain'
        WHEN c.employee_count IS NULL THEN '⚠️ Missing employee count'
        WHEN c.industries IS NULL OR ARRAY_LENGTH(c.industries, 1) = 0 THEN '⚠️ Missing industries'
        WHEN c.hq_city IS NULL THEN '⚠️ Missing headquarters'
        ELSE '✅ Complete data'
    END as data_quality_status,
    c.created_at
FROM companies c
WHERE c.created_at >= NOW() - INTERVAL '10 minutes'
ORDER BY c.created_at DESC;

-- Query 8: Error tracking (if any processing fails)
-- Monitor for potential issues during processing
SELECT 
    p.id,
    p.name,
    p.url as linkedin_url,
    p.created_at,
    EXTRACT(EPOCH FROM (NOW() - p.created_at)) as age_seconds,
    COUNT(DISTINCT c.id) as companies_found,
    CASE 
        WHEN EXTRACT(EPOCH FROM (NOW() - p.created_at)) > 300 
             AND COUNT(DISTINCT c.id) = 0 THEN '🚨 LIKELY_STUCK'
        WHEN EXTRACT(EPOCH FROM (NOW() - p.created_at)) > 120 
             AND COUNT(DISTINCT c.id) = 0 THEN '⚠️ SLOW_NO_COMPANIES'
        ELSE '✅ OK'
    END as processing_health
FROM profiles p
LEFT JOIN profile_companies pc ON p.id = pc.profile_id
LEFT JOIN companies c ON pc.company_id = c.id
WHERE p.created_at >= NOW() - INTERVAL '1 hour'
GROUP BY p.id, p.name, p.url, p.created_at
HAVING EXTRACT(EPOCH FROM (NOW() - p.created_at)) > 60 -- Only show profiles older than 1 minute
ORDER BY p.created_at DESC;

-- ============================================================================
-- USAGE INSTRUCTIONS:
-- ============================================================================
-- 1. Run Query 6 every 30 seconds for real-time dashboard
-- 2. Run Query 2 to see recent profile processing results
-- 3. Run Query 4 to monitor processing times
-- 4. Run Query 5 to check overall success rate
-- 5. Run Query 8 to identify stuck or failed processing
-- ============================================================================
