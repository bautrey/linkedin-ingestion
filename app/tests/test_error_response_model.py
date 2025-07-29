"""
Tests for ErrorResponse Pydantic model

Tests error response model validation, serialization, and OpenAPI documentation
"""

import pytest
from typing import Dict, Any, List
from pydantic import ValidationError

from app.models.errors import ErrorResponse


class TestErrorResponseModel:
    """Test ErrorResponse model functionality"""
    
    def test_error_response_creation_required_fields_only(self):
        """Test creating ErrorResponse with only required fields"""
        response = ErrorResponse(
            error_code="TEST_ERROR",
            message="Test error message"
        )
        
        assert response.error_code == "TEST_ERROR"
        assert response.message == "Test error message"
        assert response.details is None
        assert response.suggestions is None
    
    def test_error_response_creation_all_fields(self):
        """Test creating ErrorResponse with all fields"""
        details = {"field": "username", "provided_value": "invalid@example"}
        suggestions = ["Use valid LinkedIn URL format", "Check the URL for typos"]
        
        response = ErrorResponse(
            error_code="INVALID_LINKEDIN_URL",
            message="Invalid LinkedIn URL format",
            details=details,
            suggestions=suggestions
        )
        
        assert response.error_code == "INVALID_LINKEDIN_URL"
        assert response.message == "Invalid LinkedIn URL format"
        assert response.details == details
        assert response.suggestions == suggestions
    
    def test_error_response_missing_required_fields(self):
        """Test ErrorResponse validation fails with missing required fields"""
        # Missing error_code
        with pytest.raises(ValidationError) as exc_info:
            ErrorResponse(message="Test message")
        assert "error_code" in str(exc_info.value)
        
        # Missing message
        with pytest.raises(ValidationError) as exc_info:
            ErrorResponse(error_code="TEST_ERROR")
        assert "message" in str(exc_info.value)
    
    def test_error_response_serialization(self):
        """Test ErrorResponse serializes to correct JSON structure"""
        response = ErrorResponse(
            error_code="PROFILE_ALREADY_EXISTS",
            message="Profile already exists in database",
            details={"profile_id": "123", "existing_data": {"name": "John Doe"}},
            suggestions=["Use update endpoint instead", "Check existing profile data"]
        )
        
        json_data = response.model_dump()
        
        assert json_data == {
            "error_code": "PROFILE_ALREADY_EXISTS",
            "message": "Profile already exists in database", 
            "details": {"profile_id": "123", "existing_data": {"name": "John Doe"}},
            "suggestions": ["Use update endpoint instead", "Check existing profile data"]
        }
    
    def test_error_response_serialization_with_nulls(self):
        """Test ErrorResponse serializes correctly with None values"""
        response = ErrorResponse(
            error_code="INTERNAL_ERROR",
            message="An unexpected error occurred"
        )
        
        json_data = response.model_dump()
        
        assert json_data == {
            "error_code": "INTERNAL_ERROR",
            "message": "An unexpected error occurred",
            "details": None,
            "suggestions": None
        }
    
    def test_error_response_field_types(self):
        """Test ErrorResponse validates field types correctly"""
        # error_code must be string
        with pytest.raises(ValidationError):
            ErrorResponse(error_code=123, message="Test")
        
        # message must be string
        with pytest.raises(ValidationError):
            ErrorResponse(error_code="TEST", message=456)
        
        # details must be dict if provided
        with pytest.raises(ValidationError):
            ErrorResponse(error_code="TEST", message="Test", details="not a dict")
        
        # suggestions must be list if provided
        with pytest.raises(ValidationError):
            ErrorResponse(error_code="TEST", message="Test", suggestions="not a list")
    
    def test_error_response_empty_fields(self):
        """Test ErrorResponse handles empty but valid field values"""
        response = ErrorResponse(
            error_code="EMPTY_TEST",
            message="",  # Empty string should be allowed
            details={},  # Empty dict should be allowed
            suggestions=[]  # Empty list should be allowed
        )
        
        assert response.error_code == "EMPTY_TEST"
        assert response.message == ""
        assert response.details == {}
        assert response.suggestions == []


class TestErrorResponseOpenAPI:
    """Test ErrorResponse OpenAPI schema generation"""
    
    def test_error_response_schema_generation(self):
        """Test that ErrorResponse generates correct OpenAPI schema"""
        schema = ErrorResponse.model_json_schema()
        
        # Check schema structure
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "required" in schema
        
        # Check required fields
        assert set(schema["required"]) == {"error_code", "message"}
        
        # Check field properties
        properties = schema["properties"]
        
        assert properties["error_code"]["type"] == "string"
        assert properties["message"]["type"] == "string"
        
        assert properties["details"]["type"] == "object"
        assert "anyOf" in properties["details"] or "oneOf" in properties["details"] or "type" in properties["details"]
        
        assert properties["suggestions"]["type"] == "array"
        assert properties["suggestions"]["items"]["type"] == "string"
    
    def test_error_response_has_descriptions(self):
        """Test that ErrorResponse fields have proper descriptions"""
        schema = ErrorResponse.model_json_schema()
        properties = schema["properties"]
        
        # All fields should have descriptions for API documentation
        for field_name in ["error_code", "message", "details", "suggestions"]:
            assert "description" in properties[field_name], f"Missing description for {field_name}"
            assert len(properties[field_name]["description"]) > 0, f"Empty description for {field_name}"
    
    def test_error_response_examples_in_schema(self):
        """Test that ErrorResponse schema includes examples"""
        schema = ErrorResponse.model_json_schema()
        
        # Schema should include examples for documentation
        assert "examples" in schema or any("example" in prop for prop in schema["properties"].values())


class TestErrorResponseIntegration:
    """Test ErrorResponse integration with FastAPI"""
    
    def test_error_response_json_compatibility(self):
        """Test ErrorResponse works with FastAPI JSON responses"""
        import json
        
        response = ErrorResponse(
            error_code="API_TEST",
            message="Integration test",
            details={"key": "value"},
            suggestions=["suggestion1", "suggestion2"]
        )
        
        # Should be JSON serializable
        json_str = json.dumps(response.model_dump())
        parsed = json.loads(json_str)
        
        assert parsed["error_code"] == "API_TEST"
        assert parsed["message"] == "Integration test"
        assert parsed["details"] == {"key": "value"}
        assert parsed["suggestions"] == ["suggestion1", "suggestion2"]
    
    def test_error_response_fastapi_response_model(self):
        """Test ErrorResponse can be used as FastAPI response model"""
        # This test verifies the model structure is compatible with FastAPI
        # In actual integration, FastAPI will use this as response_model parameter
        
        response = ErrorResponse(
            error_code="FASTAPI_TEST",
            message="FastAPI integration test"
        )
        
        # Should have all attributes expected by FastAPI
        assert hasattr(response, 'model_dump')
        assert hasattr(response, 'model_json_schema')
        assert callable(response.model_dump)
        assert callable(response.model_json_schema)
