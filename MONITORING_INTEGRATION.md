# LinkedIn Ingestion Service - Monitoring & Alerting Integration

## Overview

This document outlines the monitoring and alerting integration for the LinkedIn Ingestion Service, with special focus on the LLM scoring and template management features added in V1.85 and V1.88.

## Health Check Endpoints

### 🏥 Available Health Check Endpoints

#### 1. Basic Health Check
- **Endpoint**: `GET /api/v1/health`
- **Authentication**: ✅ API Key Required
- **Purpose**: Basic service health and database connectivity
- **Response Time**: < 200ms
- **Usage**: External load balancers, basic monitoring

```bash
curl -H "x-api-key: YOUR_API_KEY" \
  https://your-service.com/api/v1/health
```

#### 2. Detailed Health Check  
- **Endpoint**: `GET /api/v1/health/detailed`
- **Authentication**: ✅ API Key Required
- **Purpose**: Comprehensive service health including all components
- **Response Time**: < 2000ms
- **Usage**: Detailed monitoring, alerting systems

```bash
curl -H "x-api-key: YOUR_API_KEY" \
  https://your-service.com/api/v1/health/detailed
```

#### 3. Kubernetes Readiness Probe
- **Endpoint**: `GET /ready`
- **Authentication**: ❌ No authentication
- **Purpose**: Kubernetes readiness probe
- **Response Time**: < 500ms
- **Usage**: K8s readiness checks

#### 4. Kubernetes Liveness Probe
- **Endpoint**: `GET /live`
- **Authentication**: ❌ No authentication  
- **Purpose**: Kubernetes liveness probe
- **Response Time**: < 100ms
- **Usage**: K8s liveness checks

#### 5. OpenAI Service Test
- **Endpoint**: `GET /api/v1/openai-test`
- **Authentication**: ✅ API Key Required
- **Purpose**: Test OpenAI configuration and connectivity
- **Response Time**: < 1000ms
- **Usage**: LLM service monitoring

## Service Health Monitoring

### 📊 Monitored Components

The detailed health check monitors these critical components:

#### 1. Database Service
```json
{
  "database": {
    "status": "healthy",
    "response_time_ms": 172,
    "details": {
      "status": "healthy",
      "connection": "established", 
      "sample_query_results": 1,
      "vector_dimension": 1536,
      "similarity_threshold": 0.8
    }
  }
}
```

**Monitoring Points:**
- ✅ Connection established
- ✅ Query execution time < 200ms
- ✅ Vector search capability
- ✅ Sample data accessibility

#### 2. LLM Scoring Service  
```json
{
  "llm_service": {
    "status": "healthy",
    "response_time_ms": 801,
    "has_api_key": true,
    "has_client": true,
    "token_test_result": 3
  }
}
```

**Monitoring Points:**
- ✅ OpenAI API key configured
- ✅ OpenAI client initialized
- ✅ Token counting functionality
- ✅ Response time < 1000ms

#### 3. Template Management Service
```json
{
  "template_service": {
    "status": "healthy", 
    "response_time_ms": 272,
    "template_count": 3,
    "has_default_templates": true
  }
}
```

**Monitoring Points:**
- ✅ Service initialization
- ✅ Template listing functionality
- ✅ Default templates available
- ✅ Response time < 300ms

#### 4. Scoring Job Service
```json
{
  "scoring_service": {
    "status": "healthy",
    "response_time_ms": 0.014,
    "service_initialized": true
  }
}
```

**Monitoring Points:**
- ✅ Service initialization
- ✅ Job management capability
- ✅ Response time < 100ms

## Alerting Configuration

### 🚨 Recommended Alert Rules

#### Critical Alerts (Immediate Response Required)

1. **Service Down**
   - Trigger: Overall health status = "unhealthy"
   - Threshold: Any unhealthy status
   - Action: Page on-call engineer

2. **Database Connection Lost**
   - Trigger: Database status = "unhealthy"
   - Threshold: Any database connectivity issue
   - Action: Page on-call engineer

3. **OpenAI Service Failure**
   - Trigger: LLM service status = "unhealthy"
   - Threshold: API key missing or client failure
   - Action: Notify development team

#### Warning Alerts (Investigation Required)

1. **High Response Times**
   - Database: > 500ms
   - LLM Service: > 2000ms
   - Template Service: > 1000ms
   - Action: Create ticket for investigation

2. **Template Service Issues**
   - Trigger: Template service status = "unhealthy"
   - Threshold: Service initialization failure
   - Action: Notify development team

3. **Missing Default Templates**
   - Trigger: has_default_templates = false
   - Threshold: No CTO templates available
   - Action: Check template configuration

### 📈 Performance Metrics to Track

#### Response Time Metrics
- `health_check_response_time_ms`
- `database_query_time_ms`
- `llm_service_response_time_ms`
- `template_service_response_time_ms`
- `scoring_service_response_time_ms`

#### Availability Metrics
- `service_uptime_percentage`
- `database_connection_success_rate`
- `openai_api_success_rate`
- `template_service_availability`

#### Business Metrics
- `active_template_count`
- `scoring_jobs_completed_per_hour`
- `llm_api_token_usage`
- `profile_scoring_success_rate`

## Integration Examples

### Prometheus Configuration

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'linkedin-ingestion-health'
    static_configs:
      - targets: ['your-service.com:443']
    scheme: https
    metrics_path: '/api/v1/health/detailed'
    headers:
      x-api-key: 'YOUR_API_KEY'
    scrape_interval: 30s
    scrape_timeout: 10s
```

### Grafana Dashboard Queries

```promql
# Service Health Status
up{job="linkedin-ingestion-health"}

# Database Response Time
database_response_time_ms{service="linkedin-ingestion"}

# LLM Service Health
llm_service_status{service="linkedin-ingestion"} == 1

# Template Count
template_count{service="linkedin-ingestion"}
```

### DataDog Integration

```python
import requests
from datadog import statsd

def check_service_health():
    try:
        response = requests.get(
            'https://your-service.com/api/v1/health/detailed',
            headers={'x-api-key': 'YOUR_API_KEY'},
            timeout=10
        )
        data = response.json()
        
        # Send metrics to DataDog
        statsd.gauge('linkedin_ingestion.health.overall', 
                    1 if data['status'] == 'healthy' else 0)
        
        for service, metrics in data['services'].items():
            status_value = 1 if metrics['status'] == 'healthy' else 0
            statsd.gauge(f'linkedin_ingestion.service.{service}.status', status_value)
            
            if 'response_time_ms' in metrics:
                statsd.gauge(f'linkedin_ingestion.service.{service}.response_time', 
                           metrics['response_time_ms'])
                
    except Exception as e:
        statsd.gauge('linkedin_ingestion.health.check_failed', 1)
        # Alert on monitoring failure
```

### New Relic Integration

```bash
# Custom Event
curl -X POST 'https://insights-collector.newrelic.com/v1/accounts/YOUR_ACCOUNT/events' \
  -H 'Content-Type: application/json' \
  -H 'X-Insert-Key: YOUR_INSERT_KEY' \
  -d '{
    "eventType": "LinkedInIngestionHealth",
    "status": "healthy",
    "database_response_ms": 172,
    "llm_service_response_ms": 801,
    "template_count": 3,
    "timestamp": "2025-08-17T22:23:06Z"
  }'
```

### Slack Alerting Integration

```python
import json
import requests

def send_alert_to_slack(service_status):
    webhook_url = "YOUR_SLACK_WEBHOOK_URL"
    
    if service_status['status'] != 'healthy':
        color = "danger" if service_status['status'] == "unhealthy" else "warning"
        
        payload = {
            "attachments": [{
                "color": color,
                "title": "🚨 LinkedIn Ingestion Service Alert",
                "fields": [
                    {
                        "title": "Status",
                        "value": service_status['status'],
                        "short": True
                    },
                    {
                        "title": "Services", 
                        "value": f"Database: {service_status['services']['database']['status']}\n"
                                f"LLM: {service_status['services']['llm_service']['status']}\n"
                                f"Templates: {service_status['services']['template_service']['status']}\n"
                                f"Scoring: {service_status['services']['scoring_service']['status']}",
                        "short": True
                    }
                ],
                "footer": "LinkedIn Ingestion Monitoring",
                "ts": int(time.time())
            }]
        }
        
        requests.post(webhook_url, json=payload)
```

## Runbook: Common Issues

### 🔧 Troubleshooting Guide

#### Issue: LLM Service Unhealthy

**Symptoms:**
```json
{
  "llm_service": {
    "status": "unhealthy",
    "error": "OpenAI client not initialized - missing API key"
  }
}
```

**Resolution:**
1. Check environment variables: `OPENAI_API_KEY`
2. Verify API key has sufficient quota
3. Test OpenAI connectivity manually
4. Restart service if needed

#### Issue: Template Service Unhealthy

**Symptoms:**
```json
{
  "template_service": {
    "status": "unhealthy", 
    "error": "Template listing failed"
  }
}
```

**Resolution:**
1. Check database connectivity
2. Verify `prompt_templates` table exists
3. Check for missing default templates
4. Review template service logs

#### Issue: High Database Response Times

**Symptoms:**
```json
{
  "database": {
    "status": "degraded",
    "response_time_ms": 2500
  }
}
```

**Resolution:**
1. Check Supabase dashboard for performance
2. Review recent database queries
3. Check for connection pool exhaustion
4. Consider query optimization

## Best Practices

### 🎯 Monitoring Best Practices

1. **Set up multi-level alerting**
   - Critical: Page immediately
   - Warning: Create ticket
   - Info: Log for trends

2. **Monitor business metrics**
   - Track scoring job success rates
   - Monitor template usage patterns
   - Measure LLM API costs

3. **Implement health check caching**
   - Cache results for 30 seconds to reduce load
   - Use circuit breakers for external dependencies

4. **Regular health check validation**
   - Test alert mechanisms monthly
   - Validate monitoring during deployments
   - Review and update thresholds quarterly

5. **Documentation maintenance**
   - Keep runbooks updated
   - Document new failure modes
   - Share knowledge across team

## Deployment Monitoring

### 🚀 Production Deployment Validation

Use the comprehensive production tests for deployment validation:

```bash
# Run production integration tests
pytest tests/test_production_integration.py -v -m production

# Check all health endpoints
curl -s https://your-service.com/ready
curl -s https://your-service.com/live  
curl -s -H "x-api-key: KEY" https://your-service.com/api/v1/health
curl -s -H "x-api-key: KEY" https://your-service.com/api/v1/health/detailed
```

This comprehensive monitoring setup provides full visibility into the LinkedIn Ingestion Service health, with special attention to the LLM scoring and template management features that are critical for the service's core functionality.
