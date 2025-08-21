# LinkedIn Ingestion Testing Guide

This document provides comprehensive guidance on testing practices, patterns, and tools for the LinkedIn ingestion project.

## Overview

The LinkedIn ingestion project uses a multi-tiered testing strategy that separates different types of tests to ensure fast feedback loops during development while maintaining comprehensive coverage for production validation.

## Test Categories

### 🚀 Unit Tests (`app/tests/`)
- **Purpose**: Fast, isolated tests with no external dependencies
- **Location**: `app/tests/`
- **Runtime**: < 1 second each
- **Dependencies**: Mocked external services, in-memory data
- **When to run**: Every commit, during development

```bash
# Run unit tests
./scripts/test_runners.sh unit
```

### 🔗 Integration Tests (`tests/`)
- **Purpose**: Test component interactions with mocked external services
- **Location**: `tests/` (excluding `production_workflows/`)
- **Runtime**: 1-30 seconds each
- **Dependencies**: Database, mocked APIs
- **When to run**: Before merges, in CI/CD

```bash
# Run integration tests
./scripts/test_runners.sh integration
```

### 🏭 Production Tests (`tests/production_workflows/`)
- **Purpose**: End-to-end validation with live services
- **Location**: `tests/production_workflows/`
- **Runtime**: 2-5 minutes each
- **Dependencies**: Live APIs, production database
- **When to run**: Before releases, sparingly

```bash
# Run production tests (requires environment variables)
RUN_PRODUCTION_TESTS=1 ./scripts/test_runners.sh production
```

## Test Structure and Organization

### Directory Structure
```
linkedin-ingestion/
├── app/tests/              # Unit tests (304 tests)
│   ├── test_cassidy_adapter.py
│   ├── test_canonical_models.py
│   ├── test_company_service.py
│   └── ...
├── tests/                  # Integration tests
│   ├── production_workflows/    # Production tests
│   │   ├── test_profile_creation_workflow.py
│   │   ├── test_scoring_workflow.py
│   │   └── test_system_health_workflow.py
│   ├── test_production_integration.py
│   ├── test_llm_scoring_service.py
│   └── ...
├── conftest.py            # Global test configuration
├── pytest.ini            # Pytest configuration
└── scripts/test_runners.sh    # Test execution scripts
```

### Test Markers

The project uses pytest markers to categorize tests:

```python
# Environment markers
@pytest.mark.unit          # Fast, isolated tests
@pytest.mark.integration   # Component integration tests
@pytest.mark.production    # Live service tests

# Behavior markers
@pytest.mark.slow          # Tests > 5 seconds
@pytest.mark.external      # Makes real API calls
@pytest.mark.database      # Requires database
@pytest.mark.destructive   # Modifies/deletes data
@pytest.mark.flaky         # Known to be unreliable

# Service markers
@pytest.mark.linkedin      # LinkedIn API tests
@pytest.mark.openai        # OpenAI service tests
@pytest.mark.cassidy       # Cassidy adapter tests
@pytest.mark.scoring       # Profile scoring tests
@pytest.mark.templates     # Template management tests
```

## Running Tests

### Quick Commands

```bash
# Fast feedback during development
./scripts/test_runners.sh fast

# All safe tests (no external dependencies)
./scripts/test_runners.sh all

# CI/CD pipeline tests
./scripts/test_runners.sh ci

# Coverage analysis
./scripts/test_runners.sh coverage

# Service-specific tests
./scripts/test_runners.sh cassidy
./scripts/test_runners.sh scoring
./scripts/test_runners.sh database
```

### Environment Variables

Control test execution with environment variables:

```bash
# Enable production tests (use sparingly)
export RUN_PRODUCTION_TESTS=1

# Enable external API tests
export RUN_EXTERNAL_TESTS=1

# Run only fast tests
export FAST_TESTS_ONLY=1

# Example: Full production validation
RUN_PRODUCTION_TESTS=1 RUN_EXTERNAL_TESTS=1 ./scripts/test_runners.sh production
```

### Direct pytest Commands

```bash
# Run specific test files
pytest app/tests/test_cassidy_adapter.py -v

# Run tests matching a pattern
pytest -k "cassidy" -v

# Run tests with specific markers
pytest -m "unit and not slow" -v

# Skip production tests
pytest -m "not production and not external" -v
```

## Test Isolation and Cleanup

### Problem: Test Pollution

Tests can interfere with each other by:
- Creating data that persists between tests
- Leaving network connections open
- Modifying global state
- Using real external services

### Solution: Cleanup Management

The project provides automatic cleanup utilities:

```python
from app.testing.cleanup import cleanup_context

async def test_with_cleanup():
    async with cleanup_context(production_config) as cleanup:
        # Create test resources
        profile_id = await create_test_profile()
        cleanup.register_profile(profile_id)
        
        template_id = await create_test_template()
        cleanup.register_template(template_id)
        
        # Test logic here
        # Resources automatically cleaned up on exit
```

### Fixtures for Clean Tests

```python
@pytest.fixture
async def isolated_test_environment(test_cleanup, production_config):
    """Provides isolated test environment with automatic cleanup."""
    test_cleanup.set_production_config(production_config)
    yield test_cleanup
    # Cleanup happens automatically
```

## Production vs Development Testing

### Development Testing Philosophy

**Fast Feedback Loop**: 
- Unit tests should complete in seconds
- Use mocks for all external dependencies
- Focus on code logic and data transformations

**Example Unit Test**:
```python
@pytest.mark.unit
def test_cassidy_adapter_transforms_profile(mock_external_services):
    adapter = CassidyAdapter()
    profile_data = {"full_name": "Test User", "linkedin_url": "..."}
    
    result = adapter.transform(profile_data)
    
    assert result.full_name == "Test User"
    assert isinstance(result, CanonicalProfile)
```

### Production Testing Philosophy

**Real-World Validation**:
- Test actual API integrations
- Validate end-to-end workflows
- Use real (but safe) test data
- Include cleanup mechanisms

**Example Production Test**:
```python
@pytest.mark.production
@pytest.mark.external
async def test_full_profile_workflow(production_config, production_cleanup):
    async with httpx.AsyncClient() as client:
        # Create real profile
        response = await client.post(
            f"{production_config['base_url']}/api/v1/profiles",
            json={"linkedin_url": "https://linkedin.com/in/test-profile"},
            headers=production_config['api_headers']
        )
        
        profile_id = response.json()["id"]
        production_cleanup.register_profile(profile_id)
        
        # Validate workflow
        assert response.status_code == 201
        # Additional validations...
```

## Handling Hanging Tests

### Root Causes Identified

1. **Real API Calls**: Tests making actual HTTP requests to external services
2. **Missing Timeouts**: Network operations without proper timeout configuration
3. **Resource Leaks**: Unclosed HTTP clients, database connections
4. **Async Deadlocks**: Improper async/await patterns

### Solutions Implemented

1. **Timeout Configuration**:
```python
# Global timeout in pytest.ini
timeout = 300
timeout_method = thread

# Per-test timeouts
@pytest.mark.timeout(60)
async def test_with_timeout():
    # Test logic
```

2. **Proper Resource Management**:
```python
async def test_with_proper_cleanup():
    timeout = httpx.Timeout(30.0, connect=10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        # Use client
        pass  # Client automatically closed
```

3. **Mock External Dependencies**:
```python
@pytest.fixture
def mock_linkedin_api():
    with patch("app.linkedin.client.LinkedInClient") as mock:
        mock_instance = Mock()
        mock.return_value = mock_instance
        yield mock_instance
```

## Best Practices

### Writing Effective Tests

1. **Test Naming Convention**:
```python
def test_should_transform_profile_when_valid_data_provided():
    # Descriptive name explains what, when, expected outcome
```

2. **Arrange-Act-Assert Pattern**:
```python
def test_cassidy_adapter_validation():
    # Arrange
    adapter = CassidyAdapter()
    invalid_data = {"missing": "required_fields"}
    
    # Act
    with pytest.raises(IncompleteDataError):
        adapter.transform(invalid_data)
    
    # Assert (implicit in the exception check)
```

3. **Test Data Factories**:
```python
@pytest.fixture
def test_data_factory():
    class Factory:
        @staticmethod
        def profile_data(**overrides):
            data = {
                "profile_id": "test-123",
                "full_name": "Test User",
                "linkedin_url": "https://linkedin.com/in/test"
            }
            data.update(overrides)
            return data
    return Factory()

def test_with_factory(test_data_factory):
    profile = test_data_factory.profile_data(full_name="Custom Name")
    # Use profile data
```

### Debugging Test Issues

1. **Verbose Output**:
```bash
pytest -v --tb=long --capture=no
```

2. **Run Specific Test**:
```bash
pytest app/tests/test_specific.py::TestClass::test_method -v -s
```

3. **Debug Hanging Tests**:
```bash
# Set shorter timeout for debugging
pytest --timeout=30 tests/hanging_test.py
```

4. **Check Test Dependencies**:
```bash
# Show test collection without running
pytest --collect-only
```

## CI/CD Integration

### Pipeline Stages

1. **Fast Feedback** (< 2 minutes):
   ```yaml
   - name: Unit Tests
     run: ./scripts/test_runners.sh unit
   ```

2. **Integration Validation** (< 5 minutes):
   ```yaml
   - name: Integration Tests
     run: ./scripts/test_runners.sh integration
   ```

3. **Production Smoke Tests** (< 10 minutes):
   ```yaml
   - name: Production Health Check
     run: RUN_PRODUCTION_TESTS=1 ./scripts/test_runners.sh production
     if: github.ref == 'refs/heads/main'
   ```

### Parallel Execution

```bash
# Install pytest-xdist for parallel execution
pip install pytest-xdist

# Run tests in parallel
pytest -n auto  # Use all CPU cores
pytest -n 4     # Use 4 parallel workers
```

## Performance and Optimization

### Test Execution Times

- **Unit Tests**: ~31 seconds for 304 tests (0.1s avg)
- **Integration Tests**: Variable, depends on mocking effectiveness
- **Production Tests**: 2-5 minutes each (network dependent)

### Optimization Strategies

1. **Parallel Execution**: Use `pytest-xdist`
2. **Test Selection**: Run only relevant tests during development
3. **Mocking**: Mock slow operations in unit tests
4. **Database Transactions**: Use transaction rollback for database tests
5. **Test Caching**: Cache test results for unchanged code

## Troubleshooting Common Issues

### Test Hanging Issues

**Symptom**: Tests run indefinitely without completing

**Solutions**:
1. Add timeout markers: `@pytest.mark.timeout(60)`
2. Check for unclosed HTTP clients
3. Verify async/await patterns
4. Use environment variables to skip external tests

### Test Flakiness

**Symptom**: Tests pass/fail inconsistently

**Solutions**:
1. Add `@pytest.mark.flaky` marker
2. Improve test isolation
3. Add proper wait conditions for async operations
4. Use deterministic test data

### Import Errors

**Symptom**: `ImportError` or `ModuleNotFoundError`

**Solutions**:
1. Ensure virtual environment is activated
2. Check PYTHONPATH configuration
3. Verify test discovery patterns in `pytest.ini`
4. Check for circular imports

## Advanced Testing Patterns

### Parameterized Tests

```python
@pytest.mark.parametrize("input_year,expected", [
    ("2020", 2020),
    ("invalid", None),
    ("", None),
    ("Present", None)
])
def test_year_conversion(input_year, expected):
    result = convert_year(input_year)
    assert result == expected
```

### Custom Fixtures

```python
@pytest.fixture(scope="session")
def database_engine():
    """Single database engine for entire test session."""
    engine = create_test_engine()
    yield engine
    engine.dispose()

@pytest.fixture
def clean_database(database_engine):
    """Clean database state for each test."""
    with database_engine.begin() as conn:
        # Setup clean state
        yield conn
        # Rollback changes
        conn.rollback()
```

### Mock Strategies

```python
# Mock at the class level
@patch('app.external.service.ExternalService')
def test_with_mocked_service(mock_service):
    mock_service.return_value.fetch_data.return_value = {"data": "test"}
    # Test logic

# Mock with context manager
def test_with_context_mock():
    with patch('app.external.service.ExternalService') as mock_service:
        mock_service.return_value.fetch_data.return_value = {"data": "test"}
        # Test logic

# Fixture-based mocking
@pytest.fixture
def mock_service():
    with patch('app.external.service.ExternalService') as mock:
        yield mock
```

## Monitoring and Metrics

### Test Coverage

```bash
# Generate coverage report
./scripts/test_runners.sh coverage

# View HTML coverage report
open htmlcov/index.html
```

### Test Performance Tracking

```bash
# Show slowest tests
pytest --durations=10

# Profile test execution
pytest --profile --profile-svg
```

## Contributing to Tests

### Adding New Tests

1. **Choose appropriate directory**:
   - `app/tests/` for unit tests
   - `tests/` for integration tests
   - `tests/production_workflows/` for production tests

2. **Use appropriate markers**:
   - Add `@pytest.mark.unit` for unit tests
   - Add `@pytest.mark.integration` for integration tests
   - Add `@pytest.mark.production` for production tests

3. **Include cleanup**:
   - Register created resources for cleanup
   - Use context managers for resource management
   - Implement proper teardown

4. **Follow naming conventions**:
   - `test_should_action_when_condition()`
   - Use descriptive test names
   - Group related tests in classes

### Test Review Checklist

- [ ] Test has appropriate markers
- [ ] Test cleans up created resources
- [ ] Test is properly isolated
- [ ] Test has reasonable timeout
- [ ] Test uses mocks appropriately for unit tests
- [ ] Test validates expected behavior
- [ ] Test handles edge cases
- [ ] Test documentation is clear

## Conclusion

This testing strategy provides:

1. **Fast Development Feedback**: Unit tests complete in seconds
2. **Comprehensive Coverage**: Integration tests validate component interactions
3. **Production Confidence**: End-to-end tests validate real workflows
4. **Clean Test Environment**: Automatic cleanup prevents test pollution
5. **Scalable Architecture**: Clear separation of concerns and responsibilities

By following these guidelines, developers can maintain high code quality while ensuring efficient development workflows and robust production validation.
