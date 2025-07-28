# Tests Specification

This is the tests coverage details for the spec detailed in @agent-os/specs/2025-07-27-critical-workflow-fix/spec.md

> Created: 2025-07-27
> Version: 1.0.0

## Test Coverage

### Unit Tests

**ProfileController**
- Test create_profile() calls LinkedInWorkflow.process_profile() with correct parameters
- Test create_profile() handles include_companies=True/False correctly
- Test create_profile() processes workflow results into proper API responses
- Test delete_profile() calls database delete method and returns 204
- Test delete_profile() returns 404 when profile not found
- Test duplicate detection logic with existing LinkedIn URLs
- Test force_create flag bypasses duplicate detection

**SupabaseClient**
- Test delete_profile() removes profile from database
- Test delete_profile() handles cascade deletion of related data
- Test delete_profile() returns appropriate success/failure indicators
- Test get_profile_by_url() correctly identifies existing profiles
- Test database constraint violations are caught and handled

**LinkedInWorkflow Integration**
- Test workflow.process_profile() is called with include_companies parameter
- Test workflow results contain complete experience/education/certifications data
- Test company profiles are properly fetched and associated
- Test workflow failure scenarios are handled gracefully

### Integration Tests

**Complete Workflow End-to-End**
- Test POST /api/v1/profiles with Gregory Pascuzzi LinkedIn URL returns complete profile data
- Test profile includes populated experience array with company details
- Test profile includes populated education and certifications arrays
- Test include_companies=False skips company data fetching
- Test workflow completion is tracked and reported in response

**DELETE Endpoint Functionality**
- Test DELETE /api/v1/profiles/{id} successfully removes profile
- Test DELETE request with invalid profile ID returns 404
- Test DELETE request without API key returns 403
- Test deleted profile is no longer retrievable via GET

**Enhanced Error Handling**
- Test duplicate LinkedIn URL returns 409 with existing_profile_id
- Test invalid LinkedIn URL returns 400 with clear error message
- Test workflow failures return appropriate errors instead of 500
- Test all error responses follow standardized format

**Smart Profile Management**
- Test existing profile detection by LinkedIn URL
- Test update-or-create logic with force_create=false (default)
- Test force_create=true bypasses duplicate detection
- Test conflict responses include actionable suggestions

### Mocking Requirements

**LinkedInWorkflow**: Mock process_profile() method to return controlled test data with complete experience/education arrays
**Cassidy API**: Mock underlying API calls to prevent external dependencies during testing
**Supabase Database**: Mock database operations for unit tests, use test database for integration tests
**Railway Deployment**: Mock deployment environment variables and API keys for testing

## Specific Test Cases

### Critical Test: Gregory Pascuzzi Profile
```python
def test_gregory_pascuzzi_complete_profile():
    """Test that Gregory Pascuzzi profile includes complete work experience"""
    response = client.post(
        "/api/v1/profiles",
        json={"linkedin_url": "https://linkedin.com/in/gregorypascuzzi"},
        headers={"x-api-key": API_KEY}
    )
    assert response.status_code == 200
    profile = response.json()
    assert len(profile["experience"]) > 0
    assert profile["experience"][0]["company_profile"] is not None
    assert profile["workflow_completed"] is True
```

### Error Handling Test: Duplicate Profile
```python
def test_duplicate_profile_handling():
    """Test duplicate profile returns 409 with suggestion"""
    # Create profile first
    client.post("/api/v1/profiles", json={"linkedin_url": "https://linkedin.com/in/test"})
    
    # Attempt duplicate
    response = client.post("/api/v1/profiles", json={"linkedin_url": "https://linkedin.com/in/test"})
    assert response.status_code == 409
    error = response.json()
    assert error["error_code"] == "PROFILE_EXISTS"
    assert "existing_profile_id" in error["details"]
    assert "suggestion" in error["details"]
```

### DELETE Functionality Test
```python
def test_delete_profile():
    """Test profile deletion works correctly"""
    # Create profile
    create_response = client.post("/api/v1/profiles", json={"linkedin_url": "https://linkedin.com/in/test"})
    profile_id = create_response.json()["id"]
    
    # Delete profile
    delete_response = client.delete(f"/api/v1/profiles/{profile_id}")
    assert delete_response.status_code == 204
    
    # Verify deletion
    get_response = client.get(f"/api/v1/profiles/{profile_id}")
    assert get_response.status_code == 404
```

### Workflow Integration Test
```python
def test_workflow_integration():
    """Test REST API uses LinkedInWorkflow instead of direct client"""
    with patch('app.workflows.LinkedInWorkflow.process_profile') as mock_workflow:
        mock_workflow.return_value = mock_complete_profile_data()
        
        response = client.post("/api/v1/profiles", json={"linkedin_url": "https://linkedin.com/in/test"})
        
        # Verify workflow was called correctly
        mock_workflow.assert_called_once()
        call_args = mock_workflow.call_args[0]
        assert call_args[0].include_companies is True
```

## Performance Tests

**Workflow Performance**
- Test workflow completion time vs direct client calls
- Test concurrent profile creation under load
- Test system behavior when multiple company fetches are required

**Error Response Time**
- Test error responses are fast even when underlying operations fail
- Test timeout handling for slow LinkedIn/Cassidy responses

## Regression Tests

**Existing API Compatibility**
- Test existing Make.com integration continues to work
- Test GET /api/v1/profiles functionality unchanged
- Test existing profile data format maintained
- Test API key authentication unchanged

**Database Integrity**
- Test profile relationships remain intact after changes
- Test existing profiles continue to be queryable
- Test no data corruption during workflow integration
