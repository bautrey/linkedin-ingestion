# V1.8 Test Specification - Fortium Fit Scoring API

## Testing Strategy

### Test-Driven Development (TDD) Approach
- **ALL tests written BEFORE implementation**
- Tests must pass before moving to next subtask
- Zero tolerance for warnings or errors
- Production tests required after every 2-3 subtasks

## Unit Tests

### Scoring Engine Tests
```python
# test_scoring_engine.py
def test_cto_scoring_algorithm()
def test_cio_scoring_algorithm()  
def test_ciso_scoring_algorithm()
def test_invalid_role_handling()
def test_missing_profile_data_handling()
def test_deterministic_results()
def test_score_range_validation()
def test_category_weight_application()
```

### Database Configuration Tests
```python
# test_scoring_config.py
def test_load_scoring_algorithms()
def test_load_scoring_thresholds()
def test_algorithm_version_handling()
def test_missing_configuration_error()
def test_configuration_caching()
```

### API Endpoint Tests
```python
# test_scoring_api.py
def test_score_profile_success()
def test_score_profile_not_found()
def test_invalid_role_parameter()
def test_missing_api_key()
def test_invalid_api_key()
def test_response_format_validation()
def test_performance_under_load()
```

## Integration Tests

### Database Integration
```python
# test_scoring_integration.py
def test_end_to_end_scoring_flow()
def test_database_configuration_loading()
def test_score_caching_behavior()
def test_algorithm_version_consistency()
def test_concurrent_scoring_requests()
```

### Live API Tests
```python
# test_live_scoring_api.py
def test_live_cto_scoring()
def test_live_cio_scoring()
def test_live_ciso_scoring()
def test_live_error_handling()
def test_live_performance_metrics()
```

## Test Data Requirements

### Test Profiles
- **Ronald Sorozan**: Known CTO-fit profile for baseline testing
- **Mock Profiles**: Generated profiles for each role type
- **Edge Cases**: Profiles with missing data, unusual career paths
- **Performance Profiles**: Large dataset for load testing

### Scoring Configuration Test Data
```sql
-- Test scoring algorithms
INSERT INTO scoring_algorithms (role, category, algorithm_config) VALUES
('CTO', 'technical_leadership', '{"weights": {"years_experience": 0.4, "team_size": 0.3, "technical_depth": 0.3}}'),
('CIO', 'strategic_thinking', '{"weights": {"business_impact": 0.5, "transformation": 0.3, "vision": 0.2}}'),
('CISO', 'security_experience', '{"weights": {"security_roles": 0.6, "certifications": 0.2, "incident_response": 0.2}}');

-- Test thresholds
INSERT INTO scoring_thresholds (role, threshold_type, min_score, max_score) VALUES
('CTO', 'excellent', 0.85, 1.0),
('CTO', 'good', 0.70, 0.84),
('CTO', 'fair', 0.50, 0.69),
('CTO', 'poor', 0.0, 0.49);
```

## Performance Testing

### Load Testing
- 100 concurrent requests per second
- Response time measurements
- Memory usage monitoring
- Database connection pooling validation

### Benchmark Tests
```python
def test_scoring_performance_baseline():
    """Scoring must complete within 200ms for cached results"""
    
def test_scoring_performance_fresh():  
    """Fresh scoring must complete within 500ms"""
    
def test_concurrent_scoring_performance():
    """100 concurrent requests must maintain performance"""
```

## Error Handling Tests

### Edge Cases
- Profiles with missing work experience
- Profiles with unusual education backgrounds
- Malformed profile data
- Database connectivity issues
- Configuration missing scenarios

### Recovery Testing
- Database failover scenarios
- API rate limiting behavior
- Caching invalidation
- Configuration reload testing

## Test Execution Requirements

### Local Testing
- All unit tests must pass before committing
- Integration tests run with local database
- Performance benchmarks established locally

### Production Testing
- Live API tests against Railway deployment
- Real profile scoring validation
- Performance monitoring in production environment
- Error rate tracking and alerting

## Test Coverage Requirements

- **Minimum 95% code coverage**
- **100% API endpoint coverage**
- **All error paths tested**
- **All role combinations validated**
- **Performance requirements verified**

## Continuous Testing

### Pre-commit Hooks
- Run all unit tests
- Check test coverage
- Validate code formatting
- Run security scans

### CI/CD Pipeline
- Full test suite execution
- Performance regression detection
- Production deployment verification
- Rollback testing

## Test Data Management

### Test Database Setup
- Automated test database creation
- Seed data population scripts
- Test data cleanup procedures
- Isolation between test runs

### Mock Data Generation
- Realistic profile generation
- Configurable scoring scenarios
- Performance test data sets
- Edge case profile creation
