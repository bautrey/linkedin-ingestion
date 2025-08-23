# Production Deployment Checklist

## Pre-Deployment Verification

### 1. Code Quality & Testing
- [ ] **Full Test Suite**: Run `pytest` and ensure all tests pass
  ```bash
  pytest tests/ -v
  ```
- [ ] **Linting**: Run code linting to ensure code quality
  ```bash
  flake8 app/ tests/
  black --check app/ tests/
  ```
- [ ] **Type Checking**: Verify type annotations (if using mypy)
  ```bash
  mypy app/
  ```

### 2. Configuration Validation
- [ ] **Environment Variables**: Verify all required environment variables are set
  - `SUPABASE_URL`
  - `SUPABASE_KEY`
  - `CASSIDY_API_URL`
  - `CASSIDY_API_KEY`
  - `OPENAI_API_KEY`
  - `ENABLE_COMPANY_INGESTION`
- [ ] **Database Connection**: Test database connectivity
- [ ] **API Keys**: Validate all external API keys are working
- [ ] **Rate Limiting**: Confirm rate limiting settings are appropriate for production

### 3. Architecture Validation
- [ ] **Consolidation Complete**: Confirm ProfileController uses LinkedInDataPipeline
- [ ] **No Duplicate Methods**: Verify old company processing methods are removed
- [ ] **Error Handling**: Confirm proper error handling throughout the pipeline
- [ ] **Logging**: Verify comprehensive logging is in place

## Deployment Steps

### 1. Backup Current State
- [ ] **Database Backup**: Create backup of current database state
- [ ] **Configuration Backup**: Save current configuration files
- [ ] **Code Backup**: Tag current version in git
  ```bash
  git tag -a v1.0-pre-consolidation -m "Pre-consolidation backup"
  git push origin v1.0-pre-consolidation
  ```

### 2. Deploy New Code
- [ ] **Git Operations**: 
  ```bash
  git add -A
  git commit -m "Consolidate company processing pipeline"
  git push origin main
  ```
- [ ] **Service Restart**: Restart application services
- [ ] **Health Check**: Verify application starts without errors

### 3. Database Migration (if required)
- [ ] **Schema Changes**: Apply any necessary database schema changes
- [ ] **Data Migration**: Run any required data migration scripts
- [ ] **Index Updates**: Update database indexes if needed

## Post-Deployment Validation

### 1. Functional Testing
- [ ] **Basic Health Check**: Verify `/health` endpoint responds
- [ ] **Profile Creation**: Test single profile creation
  ```bash
  curl -X POST http://localhost:8000/profiles/ \
    -H "Content-Type: application/json" \
    -d '{"linkedin_url": "https://linkedin.com/in/test-profile"}'
  ```
- [ ] **Company Processing**: Verify companies are being processed and stored
- [ ] **Database Queries**: Confirm data is being written correctly

### 2. Production Data Testing
- [ ] **Real Profile Test**: Test with a known working LinkedIn profile
- [ ] **Company Data Validation**: Verify company data accuracy
- [ ] **Database Integrity**: Check for data consistency
- [ ] **Error Handling**: Test error scenarios (invalid URLs, API failures)

### 3. Performance Validation
- [ ] **Response Times**: Verify acceptable response times
- [ ] **Memory Usage**: Monitor memory consumption
- [ ] **API Rate Limits**: Confirm staying within rate limits
- [ ] **Database Performance**: Monitor database query performance

### 4. Monitoring Setup
- [ ] **Application Logs**: Verify logging is working
- [ ] **Error Tracking**: Set up error monitoring
- [ ] **Performance Metrics**: Configure performance monitoring
- [ ] **Alert Configuration**: Set up alerts for critical errors

## Rollback Plan

### 1. Rollback Triggers
- [ ] **Critical Errors**: Application won't start
- [ ] **Data Loss**: Data corruption or loss detected
- [ ] **Performance Issues**: Unacceptable performance degradation
- [ ] **API Failures**: External API integration failures

### 2. Rollback Steps
- [ ] **Revert Code**: 
  ```bash
  git revert HEAD
  git push origin main
  ```
- [ ] **Restore Database**: Restore from pre-deployment backup
- [ ] **Restart Services**: Restart application with previous version
- [ ] **Validate Rollback**: Confirm system is working with previous version

### 3. Post-Rollback Actions
- [ ] **Root Cause Analysis**: Identify what went wrong
- [ ] **Fix Planning**: Plan fixes for identified issues
- [ ] **Documentation**: Document lessons learned

## Production Environment Checklist

### 1. Infrastructure
- [ ] **Server Resources**: Adequate CPU, memory, storage
- [ ] **Load Balancing**: Configure if using multiple instances
- [ ] **SSL/TLS**: HTTPS properly configured
- [ ] **Firewall**: Proper security configurations

### 2. Security
- [ ] **API Keys**: Securely stored (not in code)
- [ ] **Access Controls**: Proper authentication/authorization
- [ ] **Network Security**: VPN/firewall configurations
- [ ] **Data Encryption**: Sensitive data encrypted

### 3. Maintenance
- [ ] **Log Rotation**: Configure log rotation to prevent disk issues
- [ ] **Backup Schedule**: Automated backup schedule in place
- [ ] **Update Process**: Plan for future updates
- [ ] **Documentation**: Update all relevant documentation

## Key Validation Commands

### Test Profile Creation
```bash
# Test single profile
curl -X POST http://localhost:8000/profiles/ \
  -H "Content-Type: application/json" \
  -d '{"linkedin_url": "https://linkedin.com/in/dankoellhofer"}'

# Check database for companies
# (Run in your database client)
SELECT COUNT(*) FROM companies;
SELECT name, domain, employee_count FROM companies LIMIT 10;
```

### Monitor Application Health
```bash
# Check application logs
tail -f logs/application.log

# Monitor resource usage
top -p $(pgrep -f "python.*main.py")

# Test health endpoint
curl http://localhost:8000/health
```

## Success Criteria

### ✅ Deployment Successful If:
1. **Application Starts**: Service starts without errors
2. **API Responds**: All endpoints return expected responses
3. **Data Processing**: Profiles and companies are processed correctly
4. **Database Writes**: Data is written to database successfully
5. **Performance**: Response times within acceptable limits
6. **Error Handling**: Errors are handled gracefully
7. **Logging**: Comprehensive logging is working

### ❌ Rollback Required If:
1. **Service Won't Start**: Application fails to start
2. **Data Corruption**: Database data is corrupted
3. **Critical Errors**: Unhandled exceptions causing crashes
4. **Performance Issues**: Response times > 30 seconds
5. **API Failures**: External API integration completely broken

## Contact Information

### Emergency Contacts
- **Primary Developer**: [Your Contact Info]
- **DevOps Team**: [DevOps Contact Info]
- **Database Admin**: [DBA Contact Info]

### Support Resources
- **Documentation**: This checklist and CONSOLIDATED_ARCHITECTURE.md
- **Monitoring**: [Link to monitoring dashboard]
- **Logs**: [Location of log files]
- **Backup**: [Backup location and restoration procedure]

---

**Note**: This checklist should be executed step-by-step. Do not proceed to the next section until all items in the current section are completed and verified.
