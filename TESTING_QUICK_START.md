# Quick Start: Testing Unified Profile Ingestion

## 🚀 Immediate Test Execution

### 1. Start the Service Locally
```bash
cd /Users/burke/projects/linkedin-ingestion
python main.py
```

### 2. Run Automated Tests
```bash
# Make the test script executable
chmod +x test_unified_ingestion.py

# Run the test suite
python test_unified_ingestion.py
```

### 3. Manual API Tests

#### Health Check
```bash
curl http://localhost:8000/api/v1/health | jq
```

#### Create Single Profile
```bash
curl -X POST "http://localhost:8000/api/v1/profiles" \
  -H "X-API-Key: li_HieZz-IjBp0uE7d-rZkRE0qyy12r5_ZJS_FR4jMvv0I" \
  -H "Content-Type: application/json" \
  -d '{
    "linkedin_url": "https://www.linkedin.com/in/test-profile/",
    "suggested_role": "CTO",
    "include_companies": true
  }' | jq
```

#### Create Batch Profiles
```bash
curl -X POST "http://localhost:8000/api/v1/profiles/batch" \
  -H "X-API-Key: li_HieZz-IjBp0uE7d-rZkRE0qyy12r5_ZJS_FR4jMvv0I" \
  -H "Content-Type: application/json" \
  -d '{
    "profiles": [
      {
        "linkedin_url": "https://www.linkedin.com/in/batch-test-1/",
        "suggested_role": "CTO",
        "include_companies": true
      },
      {
        "linkedin_url": "https://www.linkedin.com/in/batch-test-2/",
        "suggested_role": "CISO",
        "include_companies": true
      }
    ],
    "max_concurrent": 2
  }' | jq
```

## 🔍 Database Verification

### Check Junction Table
```sql
-- Connect to local database
psql postgresql://postgres:postgres@localhost:54322/postgres

-- View profile-company relationships
SELECT 
  p.name as profile_name,
  c.company_name,
  pc.job_title,
  pc.is_current_role,
  pc.start_date,
  pc.end_date
FROM profile_companies pc
JOIN linkedin_profiles p ON pc.profile_id = p.id  
JOIN companies c ON pc.company_id = c.id
ORDER BY p.created_at DESC
LIMIT 10;
```

### Check Profiles
```sql
-- View recent profiles
SELECT 
  id, name, url, suggested_role, 
  json_array_length(experience) as exp_count,
  created_at
FROM linkedin_profiles 
ORDER BY created_at DESC 
LIMIT 10;
```

### Check Companies  
```sql
-- View recent companies
SELECT 
  id, company_name, linkedin_url, employee_count,
  array_length(industries, 1) as industry_count,
  created_at
FROM companies 
ORDER BY created_at DESC 
LIMIT 10;
```

## ✅ Expected Results

### Successful Single Profile Creation
```json
{
  "id": "uuid-here",
  "name": "Profile Name",
  "url": "https://www.linkedin.com/in/test-profile/",
  "suggested_role": "CTO",
  "companies_processed": [
    {
      "company_id": "uuid-here",
      "company_name": "Company Name",
      "action": "created"
    }
  ],
  "pipeline_metadata": {
    "companies_found": 1,
    "companies_fetched_from_cassidy": true
  }
}
```

### Successful Batch Processing
```json
{
  "batch_id": "uuid-here",
  "total_requested": 2,
  "successful": 2,
  "failed": 0,
  "results": [
    { /* Profile 1 result */ },
    { /* Profile 2 result */ }
  ],
  "processing_time_seconds": 12.34
}
```

## 🚨 Common Issues & Solutions

### 1. Service Won't Start
- **Check environment variables**: Ensure `.env` file exists with correct values
- **Database connection**: Verify Supabase is running and accessible
- **Port conflicts**: Check if port 8000 is already in use

### 2. Profile Creation Fails
- **Invalid LinkedIn URL**: Use proper LinkedIn profile URL format
- **Missing API key**: Ensure `X-API-Key` header is set correctly
- **Cassidy API issues**: Check Cassidy workflow URLs and API access

### 3. Company Processing Issues
- **Rate limiting**: Companies processed with 1-second delays (expected)
- **Some companies fail**: Normal - profile creation continues
- **No companies processed**: Check `include_companies: true` in request

### 4. Database Issues
- **Junction table missing**: Run migration: `supabase db push --password "dvm2rjq6ngk@GZN-wth" --linked`
- **Foreign key errors**: Ensure both profiles and companies tables exist
- **Connection issues**: Check Supabase credentials and network access

## 🎯 Key Success Indicators

✅ **API Health**: `/api/v1/health` returns 200 with database status "healthy"  
✅ **Profile Creation**: Single profiles created with unique IDs  
✅ **Company Processing**: Companies extracted from experience and processed  
✅ **Junction Relationships**: Profile-company links created in database  
✅ **Batch Processing**: Multiple profiles processed concurrently  
✅ **Error Handling**: Proper error codes and messages for invalid inputs  
✅ **Data Integrity**: No duplicate profiles, proper cascade deletion  

## 📝 Test Log Locations

- **Application logs**: Check terminal output when running `python main.py`
- **Test results**: Output from `python test_unified_ingestion.py`
- **Database logs**: Check Supabase dashboard or local PostgreSQL logs
- **API documentation**: Available at `http://localhost:8000/docs` during development

## 🔄 Iterative Testing

1. **Start small**: Test single profile creation first
2. **Verify data**: Check database for expected records
3. **Test error cases**: Ensure proper error handling
4. **Scale up**: Test batch processing
5. **Performance**: Monitor processing times and rate limiting
6. **Cleanup**: Delete test profiles to keep database clean

## 🛠 Debugging Tips

- **Enable debug logging**: Set `LOG_LEVEL=DEBUG` in environment
- **Use API docs**: Visit `/docs` endpoint for interactive testing
- **Check network**: Verify Cassidy API connectivity
- **Database queries**: Use SQL queries above to inspect data
- **Monitor resources**: Check memory/CPU usage during batch processing
