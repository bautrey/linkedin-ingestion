# Make.com Integration Testing Guide

This document provides guidance for testing Make.com workflow integrations with the LinkedIn Ingestion Service to ensure production deployment doesn't break existing automations.

## Overview

The LinkedIn Ingestion Service integrates with Make.com (formerly Integromat) workflows for automated profile and company data processing. This testing ensures:

1. Existing workflows continue to function after service updates
2. New batch enhanced ingestion doesn't conflict with current automations
3. Data format compatibility is maintained
4. Webhook endpoints remain accessible and functional

## Pre-Testing Setup

### 1. Identify Active Make.com Workflows

Before testing, catalog all active Make.com workflows that integrate with the LinkedIn Ingestion Service:

#### Profile Ingestion Workflows
- **Enhanced Profile Processing**: Workflows that call `/api/v1/profiles/enhanced`
- **Basic Profile Creation**: Workflows that call `/api/v1/profiles`
- **Profile Updates**: Workflows that modify existing profiles
- **Profile Queries**: Workflows that search or retrieve profiles

#### Company Data Workflows  
- **Company Creation**: Workflows that create company records
- **Company Updates**: Workflows that modify company data
- **Company-Profile Linking**: Workflows that associate profiles with companies

#### Template & Scoring Workflows
- **Template Management**: Workflows that create/update scoring templates
- **Profile Scoring**: Workflows that trigger profile scoring operations

### 2. Document Current Endpoints

Ensure you have documentation of all endpoints currently used by Make.com:

```
GET /api/v1/health
GET /api/v1/profiles
POST /api/v1/profiles
POST /api/v1/profiles/enhanced
GET /api/v1/profiles/{profile_id}
PUT /api/v1/profiles/{profile_id}
DELETE /api/v1/profiles/{profile_id}
GET /api/v1/companies
POST /api/v1/companies
GET /api/v1/templates
POST /api/v1/templates
```

### 3. Test Environment Preparation

- **Development Testing**: Use development server for initial validation
- **Staging Testing**: Test against staging environment if available  
- **Production Testing**: Final validation against production deployment

## Testing Scenarios

### 1. Endpoint Availability Testing

Verify all existing endpoints remain accessible:

```bash
# Health check
curl -X GET "https://your-domain.com/api/v1/health"

# Profile endpoints
curl -X GET "https://your-domain.com/api/v1/profiles" \
  -H "X-API-Key: your_api_key"

# Enhanced ingestion (existing functionality)
curl -X POST "https://your-domain.com/api/v1/profiles/enhanced" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key" \
  -d '{"linkedin_url": "https://linkedin.com/in/example"}'
```

### 2. Data Format Compatibility

#### Profile Response Format
Ensure profile data structure remains consistent:

```json
{
  "id": "uuid",
  "linkedin_url": "string",
  "full_name": "string", 
  "headline": "string",
  "location": "string",
  "about": "string",
  "experience": [...],
  "education": [...],
  "skills": [...],
  "company_id": "uuid",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

#### Error Response Format
Verify error responses maintain expected structure:

```json
{
  "detail": "Error message",
  "error_code": "ERROR_CODE",
  "status_code": 400
}
```

### 3. Authentication Testing

Confirm API key authentication works as expected:

```bash
# Valid API key
curl -X GET "https://your-domain.com/api/v1/profiles" \
  -H "X-API-Key: valid_key"
# Expected: 200 OK

# Invalid API key  
curl -X GET "https://your-domain.com/api/v1/profiles" \
  -H "X-API-Key: invalid_key"
# Expected: 401 Unauthorized

# Missing API key
curl -X GET "https://your-domain.com/api/v1/profiles"
# Expected: 401 Unauthorized
```

### 4. Rate Limiting Validation

Test that rate limiting doesn't break workflows:

```bash
# Send multiple requests rapidly
for i in {1..10}; do
  curl -X GET "https://your-domain.com/api/v1/health" &
done
wait

# Check for 429 Too Many Requests responses
```

### 5. Webhook Processing Testing

If Make.com uses webhooks, test webhook endpoints:

```bash
# Test webhook endpoint (if applicable)
curl -X POST "https://your-domain.com/webhooks/makecom" \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'
```

## Make.com Workflow Testing

### 1. Individual Scenario Testing

For each identified Make.com scenario:

#### Test Steps:
1. **Trigger Workflow**: Activate the Make.com scenario manually
2. **Monitor Execution**: Watch the scenario execution in Make.com dashboard
3. **Verify Data Flow**: Ensure data passes correctly between modules
4. **Check Results**: Validate that expected outcomes occur
5. **Error Handling**: Test error conditions and recovery

#### Success Criteria:
- ✅ Workflow executes without errors
- ✅ Data is processed correctly
- ✅ Expected actions are completed
- ✅ Error handling works as expected

### 2. End-to-End Testing

Test complete automation flows:

#### Example: LinkedIn Profile Processing Flow
1. **Trigger**: New LinkedIn URL submitted to Make.com
2. **API Call**: Make.com calls `/api/v1/profiles/enhanced`
3. **Processing**: Service processes profile and company data
4. **Response**: Make.com receives processed profile data
5. **Actions**: Make.com performs follow-up actions (email, CRM update, etc.)

### 3. Batch Processing Impact

Test how new batch functionality affects existing workflows:

#### Considerations:
- Does batch processing change response times?
- Are there any resource contention issues?
- Do existing rate limits still apply appropriately?

## Production Integration Checklist

### Pre-Production
- [ ] All existing Make.com scenarios identified and documented
- [ ] Test data and scenarios prepared
- [ ] Backup/rollback plan established
- [ ] Stakeholders notified of testing schedule

### During Testing
- [ ] Health endpoint verification
- [ ] API authentication testing
- [ ] Data format compatibility verification
- [ ] Rate limiting functionality check
- [ ] Individual workflow testing
- [ ] End-to-end automation testing
- [ ] Error handling validation
- [ ] Performance impact assessment

### Post-Testing
- [ ] All scenarios pass successfully
- [ ] Performance metrics within acceptable range
- [ ] Error rates remain normal
- [ ] Make.com webhook deliverability confirmed
- [ ] Documentation updated with any changes
- [ ] Stakeholders notified of results

## Troubleshooting Common Issues

### 1. Authentication Failures
- **Issue**: Make.com workflows fail with 401 errors
- **Solution**: Verify API key is correctly configured in Make.com
- **Check**: Ensure production API key differs from development

### 2. Data Format Changes
- **Issue**: Make.com can't parse API responses
- **Solution**: Review response structure for breaking changes
- **Check**: Validate JSON schema compatibility

### 3. Rate Limiting Issues
- **Issue**: Workflows hit rate limits
- **Solution**: Adjust Make.com scenario timing or contact support for limits
- **Check**: Monitor rate limit headers in responses

### 4. Timeout Problems
- **Issue**: Make.com workflows timeout waiting for responses
- **Solution**: Increase timeout settings in Make.com or optimize API performance
- **Check**: Monitor API response times

### 5. Webhook Delivery Failures
- **Issue**: Webhooks from service to Make.com fail
- **Solution**: Verify webhook URLs and authentication
- **Check**: Test webhook endpoints directly

## Monitoring and Alerts

### 1. Set Up Monitoring
- Monitor Make.com scenario execution rates
- Track API error rates from Make.com requests
- Watch for authentication failures
- Monitor response times for Make.com endpoints

### 2. Alert Thresholds
- **Error Rate**: >5% failure rate for Make.com requests
- **Response Time**: >10 second response times
- **Authentication**: Multiple 401 errors from same Make.com account

### 3. Dashboard Metrics
- Make.com request volume
- Success/failure rates by endpoint
- Average response times
- Rate limiting occurrences

## Documentation Updates

After successful integration testing:

1. **API Documentation**: Update any endpoint documentation changes
2. **Make.com Templates**: Provide updated Make.com scenario templates
3. **Integration Guide**: Update integration guide with new capabilities
4. **Troubleshooting**: Document any new issues and solutions discovered

---

**Contact Information:**
- **Technical Support**: [support-email]
- **Make.com Account**: [account-details] 
- **Emergency Contact**: [emergency-contact]

**Last Updated**: 2024-01-XX  
**Version**: 2.1.0-development+ae6d5ec9
