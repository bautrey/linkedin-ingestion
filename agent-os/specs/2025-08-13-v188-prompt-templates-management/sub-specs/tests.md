# Tests Specification

> Spec: V1.88 Prompt Templates Management System
> Document: Tests Specification
> Created: 2025-08-13

## Testing Strategy

Comprehensive test coverage for the prompt templates management system, emphasizing production-ready validation and integration with existing LLM scoring infrastructure. Tests follow the existing pytest patterns with proper async support and database mocking.

## Test Categories

### Unit Tests
- **Pydantic Models**: Template validation and serialization
- **Service Layer**: Business logic and error handling
- **Database Operations**: CRUD operations with proper mocking

### Integration Tests
- **API Endpoints**: Full request/response cycle testing
- **Database Integration**: Real database operations (when available)
- **LLM Scoring Integration**: Template-based scoring workflows

### Production Validation Tests
- **Migration Verification**: Database schema deployment validation
- **End-to-End Workflows**: Complete template creation to scoring completion
- **Performance Tests**: Template system response times and concurrency

## Test File Structure

Following existing patterns in `app/tests/`:

```
app/tests/
├── test_template_models.py          # Pydantic model tests
├── test_template_service.py         # Service layer tests  
├── test_template_controllers.py     # Controller tests
├── test_template_api_endpoints.py   # API endpoint tests
├── test_template_integration.py     # Integration tests
└── test_template_production.py      # Production validation tests
```

## Unit Tests

### 1. Template Model Tests (`test_template_models.py`)

#### Pydantic Model Validation

```python
import pytest
from pydantic import ValidationError
from app.models.template_models import PromptTemplate, CreateTemplateRequest, UpdateTemplateRequest

class TestPromptTemplateModel:
    def test_valid_template_creation(self):
        """Test creating a valid template model."""
        template = PromptTemplate(
            id="123e4567-e89b-12d3-a456-426614174000",
            name="Test CTO Template",
            category="CTO",
            prompt_text="Test prompt content",
            version=1,
            is_active=True,
            created_at="2025-08-13T12:00:00Z",
            updated_at="2025-08-13T12:00:00Z",
            metadata={}
        )
        assert template.name == "Test CTO Template"
        assert template.category == "CTO"
        assert template.is_active is True

    def test_template_serialization(self):
        """Test template model serialization."""
        template = PromptTemplate(
            id="123e4567-e89b-12d3-a456-426614174000",
            name="Test Template",
            category="CTO", 
            prompt_text="Test prompt",
            version=1,
            is_active=True,
            created_at="2025-08-13T12:00:00Z",
            updated_at="2025-08-13T12:00:00Z"
        )
        
        serialized = template.model_dump()
        assert "id" in serialized
        assert serialized["name"] == "Test Template"
        assert serialized["category"] == "CTO"

    def test_template_validation_errors(self):
        """Test template validation with invalid data."""
        with pytest.raises(ValidationError) as exc_info:
            PromptTemplate(
                name="",  # Empty name should fail
                category="CTO",
                prompt_text="Test prompt"
            )
        assert "name" in str(exc_info.value)

    def test_create_template_request_validation(self):
        """Test create template request validation."""
        request = CreateTemplateRequest(
            name="New Template",
            category="CIO",
            prompt_text="New prompt content",
            description="Test description",
            metadata={"tags": ["test"]}
        )
        assert request.name == "New Template"
        assert request.category == "CIO"

    def test_update_template_request_validation(self):
        """Test update template request validation."""
        request = UpdateTemplateRequest(
            name="Updated Name",
            description="Updated description"
        )
        assert request.name == "Updated Name"
        assert request.prompt_text is None  # Optional field
```

### 2. Template Service Tests (`test_template_service.py`)

#### Service Layer Business Logic

```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.template_service import TemplateService
from app.models.template_models import CreateTemplateRequest, UpdateTemplateRequest

class TestTemplateService:
    @pytest.fixture
    def mock_supabase_client(self):
        """Mock Supabase client for testing."""
        client = MagicMock()
        client.table = MagicMock()
        return client

    @pytest.fixture
    def template_service(self, mock_supabase_client):
        """Create template service with mocked dependencies."""
        return TemplateService(supabase_client=mock_supabase_client)

    @pytest.mark.asyncio
    async def test_get_template_by_id_success(self, template_service, mock_supabase_client):
        """Test successful template retrieval by ID."""
        # Mock successful database response
        mock_response = MagicMock()
        mock_response.data = [{
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "name": "Test Template",
            "category": "CTO",
            "prompt_text": "Test prompt",
            "version": 1,
            "is_active": True,
            "created_at": "2025-08-13T12:00:00+00:00",
            "updated_at": "2025-08-13T12:00:00+00:00",
            "metadata": {}
        }]
        
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response

        template = await template_service.get_template_by_id("123e4567-e89b-12d3-a456-426614174000")
        
        assert template is not None
        assert template.name == "Test Template"
        assert template.category == "CTO"

    @pytest.mark.asyncio
    async def test_get_template_by_id_not_found(self, template_service, mock_supabase_client):
        """Test template not found scenario."""
        # Mock empty database response
        mock_response = MagicMock()
        mock_response.data = []
        
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response

        template = await template_service.get_template_by_id("nonexistent-id")
        assert template is None

    @pytest.mark.asyncio
    async def test_create_template_success(self, template_service, mock_supabase_client):
        """Test successful template creation."""
        request = CreateTemplateRequest(
            name="New Template",
            category="CTO",
            prompt_text="New prompt content"
        )
        
        # Mock successful insert response
        mock_response = MagicMock()
        mock_response.data = [{
            "id": "new-template-id",
            "name": "New Template",
            "category": "CTO",
            "prompt_text": "New prompt content",
            "version": 1,
            "is_active": True,
            "created_at": "2025-08-13T12:00:00+00:00",
            "updated_at": "2025-08-13T12:00:00+00:00",
            "metadata": {}
        }]
        
        mock_supabase_client.table.return_value.insert.return_value.execute.return_value = mock_response

        template = await template_service.create_template(request)
        
        assert template is not None
        assert template.name == "New Template"
        assert template.category == "CTO"

    @pytest.mark.asyncio 
    async def test_list_templates_with_filters(self, template_service, mock_supabase_client):
        """Test template listing with category filter."""
        # Mock filtered database response
        mock_response = MagicMock()
        mock_response.data = [
            {
                "id": "template1",
                "name": "CTO Template 1",
                "category": "CTO",
                "version": 1,
                "is_active": True,
                "created_at": "2025-08-13T12:00:00+00:00",
                "updated_at": "2025-08-13T12:00:00+00:00"
            }
        ]
        
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.execute.return_value = mock_response

        templates = await template_service.list_templates(category="CTO", include_inactive=False)
        
        assert len(templates) == 1
        assert templates[0].category == "CTO"

    @pytest.mark.asyncio
    async def test_update_template_success(self, template_service, mock_supabase_client):
        """Test successful template update."""
        request = UpdateTemplateRequest(
            name="Updated Template",
            description="Updated description"
        )
        
        # Mock successful update response
        mock_response = MagicMock()
        mock_response.data = [{
            "id": "template-id",
            "name": "Updated Template", 
            "description": "Updated description",
            "category": "CTO",
            "prompt_text": "Original prompt",
            "version": 1,
            "is_active": True,
            "created_at": "2025-08-13T12:00:00+00:00",
            "updated_at": "2025-08-13T13:00:00+00:00",
            "metadata": {}
        }]
        
        mock_supabase_client.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_response

        template = await template_service.update_template("template-id", request)
        
        assert template is not None
        assert template.name == "Updated Template"
        assert template.description == "Updated description"

    @pytest.mark.asyncio
    async def test_delete_template_success(self, template_service, mock_supabase_client):
        """Test successful template soft deletion."""
        # Mock successful soft delete (update is_active = false)
        mock_response = MagicMock()
        mock_response.data = [{"id": "template-id"}]
        
        mock_supabase_client.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_response

        result = await template_service.delete_template("template-id")
        assert result is True
```

### 3. Controller Tests (`test_template_controllers.py`)

#### Request/Response Handling Tests

```python
import pytest
from unittest.mock import AsyncMock
from app.controllers.template_controllers import TemplateController
from app.models.template_models import CreateTemplateRequest

class TestTemplateController:
    @pytest.fixture
    def mock_template_service(self):
        """Mock template service for testing."""
        return AsyncMock()

    @pytest.fixture
    def template_controller(self, mock_template_service):
        """Create template controller with mocked service."""
        return TemplateController(template_service=mock_template_service)

    @pytest.mark.asyncio
    async def test_get_template_success(self, template_controller, mock_template_service):
        """Test successful template retrieval."""
        # Mock service response
        mock_template = MagicMock()
        mock_template.id = "template-id"
        mock_template.name = "Test Template"
        mock_template_service.get_template_by_id.return_value = mock_template

        result = await template_controller.get_template("template-id")
        
        assert result is not None
        assert result.id == "template-id"
        mock_template_service.get_template_by_id.assert_called_once_with("template-id")

    @pytest.mark.asyncio
    async def test_get_template_not_found(self, template_controller, mock_template_service):
        """Test template not found handling."""
        mock_template_service.get_template_by_id.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await template_controller.get_template("nonexistent-id")
            
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_create_template_success(self, template_controller, mock_template_service):
        """Test successful template creation."""
        request = CreateTemplateRequest(
            name="New Template",
            category="CTO", 
            prompt_text="Test prompt"
        )
        
        mock_template = MagicMock()
        mock_template.id = "new-template-id"
        mock_template_service.create_template.return_value = mock_template

        result = await template_controller.create_template(request)
        
        assert result.id == "new-template-id"
        mock_template_service.create_template.assert_called_once_with(request)

    @pytest.mark.asyncio
    async def test_list_templates_with_filters(self, template_controller, mock_template_service):
        """Test template listing with filters."""
        mock_templates = [MagicMock(), MagicMock()]
        mock_template_service.list_templates.return_value = mock_templates

        result = await template_controller.list_templates(category="CTO", include_inactive=False)
        
        assert len(result.templates) == 2
        mock_template_service.list_templates.assert_called_once_with(category="CTO", include_inactive=False)
```

## Integration Tests

### 4. API Endpoint Tests (`test_template_api_endpoints.py`)

#### Full HTTP Request/Response Testing

```python
import pytest
from httpx import AsyncClient
from app.main import app

class TestTemplateAPIEndpoints:
    @pytest.fixture
    def api_headers(self):
        """Standard API headers for testing."""
        return {"x-api-key": "li_HieZz-IjBp0uE7d-rZkRE0qyy12r5_ZJS_FR4jMvv0I"}

    @pytest.mark.asyncio
    async def test_list_templates_endpoint(self, api_headers):
        """Test GET /api/v1/templates endpoint."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/templates", headers=api_headers)
            
        assert response.status_code == 200
        data = response.json()
        assert "templates" in data
        assert "count" in data
        assert isinstance(data["templates"], list)

    @pytest.mark.asyncio
    async def test_create_template_endpoint(self, api_headers):
        """Test POST /api/v1/templates endpoint."""
        template_data = {
            "name": "API Test Template",
            "category": "CTO",
            "prompt_text": "Test prompt for API testing",
            "description": "Created via API test"
        }
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/templates", 
                json=template_data,
                headers=api_headers
            )
            
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "API Test Template"
        assert data["category"] == "CTO"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_get_template_by_id_endpoint(self, api_headers):
        """Test GET /api/v1/templates/{id} endpoint."""
        # First create a template to test retrieval
        template_data = {
            "name": "Get Test Template",
            "category": "CIO", 
            "prompt_text": "Test prompt for get testing"
        }
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create template
            create_response = await client.post(
                "/api/v1/templates",
                json=template_data,
                headers=api_headers
            )
            template_id = create_response.json()["id"]
            
            # Get template by ID
            get_response = await client.get(
                f"/api/v1/templates/{template_id}",
                headers=api_headers
            )
            
        assert get_response.status_code == 200
        data = get_response.json()
        assert data["id"] == template_id
        assert data["name"] == "Get Test Template"

    @pytest.mark.asyncio
    async def test_template_not_found_endpoint(self, api_headers):
        """Test 404 response for non-existent template."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/templates/nonexistent-id",
                headers=api_headers
            )
            
        assert response.status_code == 404
        data = response.json()
        assert "error" in data

    @pytest.mark.asyncio
    async def test_authentication_required(self):
        """Test that API key authentication is required."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/templates")
            
        assert response.status_code == 401
```

### 5. Integration Tests (`test_template_integration.py`)

#### Template-Scoring Integration Tests

```python
import pytest
from httpx import AsyncClient
from app.main import app

class TestTemplateIntegration:
    @pytest.fixture
    def api_headers(self):
        return {"x-api-key": "li_HieZz-IjBp0uE7d-rZkRE0qyy12r5_ZJS_FR4jMvv0I"}

    @pytest.mark.asyncio
    async def test_scoring_with_template_id(self, api_headers):
        """Test scoring a profile using a template ID."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create template
            template_data = {
                "name": "Integration Test Template",
                "category": "CTO",
                "prompt_text": "Evaluate this candidate for CTO position: Technical skills (0-10), Leadership (0-10). Respond in JSON."
            }
            
            create_response = await client.post(
                "/api/v1/templates",
                json=template_data,
                headers=api_headers
            )
            template_id = create_response.json()["id"]
            
            # Use template for scoring (using test profile ID)
            scoring_data = {
                "template_id": template_id
            }
            
            score_response = await client.post(
                "/api/v1/profiles/435ccbf7-6c5e-4e2d-bdc3-052a244d7121/score",
                json=scoring_data,
                headers=api_headers
            )
            
        assert score_response.status_code == 202
        score_data = score_response.json()
        assert "job_id" in score_data
        assert score_data["template_id"] == template_id

    @pytest.mark.asyncio
    async def test_backward_compatibility_raw_prompt(self, api_headers):
        """Test that raw prompt scoring still works (backward compatibility)."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            scoring_data = {
                "prompt": "Evaluate this candidate: Technical skills (0-10). Respond in JSON."
            }
            
            response = await client.post(
                "/api/v1/profiles/435ccbf7-6c5e-4e2d-bdc3-052a244d7121/score",
                json=scoring_data,
                headers=api_headers
            )
            
        assert response.status_code == 202
        data = response.json()
        assert "job_id" in data
        assert "template_id" not in data  # Raw prompt shouldn't have template_id

    @pytest.mark.asyncio
    async def test_template_validation_in_scoring(self, api_headers):
        """Test scoring with invalid template ID."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            scoring_data = {
                "template_id": "nonexistent-template-id"
            }
            
            response = await client.post(
                "/api/v1/profiles/435ccbf7-6c5e-4e2d-bdc3-052a244d7121/score", 
                json=scoring_data,
                headers=api_headers
            )
            
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
```

## Production Validation Tests

### 6. Production Validation (`test_template_production.py`)

#### Production Environment Validation

```python
import pytest
import os
from httpx import AsyncClient

@pytest.mark.production
class TestTemplateProduction:
    """Production environment validation tests."""
    
    @pytest.fixture
    def production_url(self):
        """Production URL for testing."""
        return "https://smooth-mailbox-production.up.railway.app"
    
    @pytest.fixture
    def api_headers(self):
        return {"x-api-key": "li_HieZz-IjBp0uE7d-rZkRE0qyy12r5_ZJS_FR4jMvv0I"}

    @pytest.mark.asyncio
    async def test_production_health_check_includes_templates(self, production_url, api_headers):
        """Test that production health check includes template system."""
        async with AsyncClient() as client:
            response = await client.get(f"{production_url}/health", headers=api_headers)
            
        assert response.status_code == 200
        data = response.json()
        assert "services" in data
        assert "template_system" in data["services"]
        assert data["services"]["template_system"] == "healthy"

    @pytest.mark.asyncio
    async def test_production_default_templates_exist(self, production_url, api_headers):
        """Test that default Fortium templates exist in production."""
        async with AsyncClient() as client:
            response = await client.get(f"{production_url}/api/v1/templates", headers=api_headers)
            
        assert response.status_code == 200
        data = response.json()
        
        # Check for default templates
        template_names = [t["name"] for t in data["templates"]]
        assert "Fortium CTO Evaluation" in template_names
        assert "Fortium CIO Evaluation" in template_names
        assert "Fortium CISO Evaluation" in template_names

    @pytest.mark.asyncio
    async def test_production_end_to_end_template_scoring(self, production_url, api_headers):
        """Test complete end-to-end template-based scoring in production."""
        async with AsyncClient() as client:
            # Get CTO template
            templates_response = await client.get(
                f"{production_url}/api/v1/templates?category=CTO",
                headers=api_headers
            )
            templates = templates_response.json()["templates"]
            cto_template = next(t for t in templates if "CTO" in t["name"])
            
            # Score profile using template
            scoring_response = await client.post(
                f"{production_url}/api/v1/profiles/435ccbf7-6c5e-4e2d-bdc3-052a244d7121/score",
                json={"template_id": cto_template["id"]},
                headers=api_headers
            )
            
        assert scoring_response.status_code == 202
        job_data = scoring_response.json()
        assert job_data["template_id"] == cto_template["id"]
        
        # Note: We could poll for job completion here, but that would make the test slower
        # Production validation focuses on successful job creation

    @pytest.mark.asyncio
    async def test_production_template_crud_operations(self, production_url, api_headers):
        """Test template CRUD operations in production environment."""
        async with AsyncClient() as client:
            # Create test template
            template_data = {
                "name": f"Production Test Template {os.urandom(4).hex()}",
                "category": "TEST",
                "prompt_text": "Test prompt for production validation",
                "description": "Temporary template for production testing"
            }
            
            create_response = await client.post(
                f"{production_url}/api/v1/templates",
                json=template_data,
                headers=api_headers
            )
            assert create_response.status_code == 201
            template_id = create_response.json()["id"]
            
            # Update template
            update_data = {
                "description": "Updated description for production test"
            }
            update_response = await client.put(
                f"{production_url}/api/v1/templates/{template_id}",
                json=update_data,
                headers=api_headers
            )
            assert update_response.status_code == 200
            
            # Delete template (cleanup)
            delete_response = await client.delete(
                f"{production_url}/api/v1/templates/{template_id}",
                headers=api_headers
            )
            assert delete_response.status_code == 200
```

## Test Configuration

### Pytest Configuration Updates

Add to existing `pytest.ini` or `pyproject.toml`:

```ini
[tool.pytest.ini_options]
markers = [
    "production: marks tests as production environment validation (deselect with '-m \"not production\"')"
]
```

### Test Fixtures

Common test fixtures to add to `conftest.py`:

```python
import pytest
from unittest.mock import MagicMock, AsyncMock

@pytest.fixture
def mock_template_data():
    """Standard template data for testing."""
    return {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "name": "Test Template",
        "category": "CTO",
        "prompt_text": "Test evaluation prompt",
        "version": 1,
        "is_active": True,
        "description": "Test template description",
        "metadata": {"tags": ["test"]},
        "created_at": "2025-08-13T12:00:00+00:00",
        "updated_at": "2025-08-13T12:00:00+00:00"
    }

@pytest.fixture
def mock_supabase_template_client():
    """Mock Supabase client configured for template operations."""
    client = MagicMock()
    table_mock = MagicMock()
    client.table.return_value = table_mock
    return client
```

## Test Execution Strategy

### Local Development

```bash
# Run all template tests
pytest app/tests/test_template* -v

# Run only unit tests (fast)
pytest app/tests/test_template* -v -m "not production"

# Run with coverage
pytest app/tests/test_template* --cov=app.services.template_service --cov=app.controllers.template_controllers
```

### Production Validation

```bash
# Run production validation tests
pytest app/tests/test_template_production.py -v -m production

# Run full integration including production
pytest app/tests/test_template* -v
```

### Continuous Integration

```bash
# CI pipeline should run both local and production tests
pytest app/tests/test_template* -v --tb=short
```

## Performance Testing

### Load Testing Templates

```python
@pytest.mark.asyncio
async def test_template_retrieval_performance():
    """Test template retrieval performance under load."""
    import asyncio
    import time
    
    async def get_template():
        # Mock multiple concurrent template retrievals
        async with AsyncClient(app=app, base_url="http://test") as client:
            return await client.get("/api/v1/templates", headers=api_headers)
    
    start_time = time.time()
    tasks = [get_template() for _ in range(10)]
    responses = await asyncio.gather(*tasks)
    end_time = time.time()
    
    # Verify all requests succeeded
    for response in responses:
        assert response.status_code == 200
    
    # Performance assertion (adjust as needed)
    total_time = end_time - start_time
    assert total_time < 2.0  # Should complete 10 requests in under 2 seconds
```

## Test Data Management

### Test Database Seeding

For integration tests requiring specific templates:

```python
@pytest.fixture
async def seeded_templates():
    """Create test templates in database for integration tests."""
    # This fixture would create actual test templates
    # and clean them up after tests complete
    test_templates = []
    
    # Setup code here
    yield test_templates
    
    # Cleanup code here
```

This comprehensive test specification ensures robust validation of the prompt templates system across all layers, with special emphasis on production validation to catch deployment issues early.
