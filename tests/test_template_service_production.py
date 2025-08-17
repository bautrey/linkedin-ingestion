"""
Production validation tests for TemplateService

Tests the service layer against the actual production database to ensure 
all CRUD operations work correctly in the real environment.
"""

import pytest
import asyncio
import os
from typing import Optional

from app.services.template_service import TemplateService
from app.models.template_models import (
    PromptTemplate,
    CreateTemplateRequest,
    UpdateTemplateRequest
)
from app.database.supabase_client import SupabaseClient


@pytest.mark.integration
class TestTemplateServiceProduction:
    """Production validation tests for TemplateService"""

    @pytest.fixture
    async def supabase_client(self):
        """Real Supabase client for production testing"""
        client = SupabaseClient()
        await client._ensure_client()
        yield client
        # Cleanup happens in individual tests

    @pytest.fixture
    def template_service(self, supabase_client):
        """TemplateService with real Supabase client"""
        return TemplateService(supabase_client)

    @pytest.fixture
    def test_template_request(self) -> CreateTemplateRequest:
        """Test template request for production testing"""
        return CreateTemplateRequest(
            name="Test Template - Production Validation",
            category="TEST",
            prompt_text="This is a test template for production validation. "
                       "Evaluate candidate technical skills and leadership potential.",
            description="Test template created during service layer validation",
            is_active=True,
            metadata={
                "test": True,
                "created_for": "service_validation",
                "version": "production_test"
            }
        )

    @pytest.mark.asyncio
    async def test_template_crud_operations_production(
        self, 
        template_service: TemplateService,
        test_template_request: CreateTemplateRequest
    ):
        """Test complete CRUD cycle against production database"""
        created_template = None
        
        try:
            # Test CREATE
            created_template = await template_service.create_template(test_template_request)
            
            assert created_template is not None
            assert isinstance(created_template, PromptTemplate)
            assert created_template.name == test_template_request.name
            assert created_template.category == test_template_request.category
            assert created_template.prompt_text == test_template_request.prompt_text
            assert created_template.is_active is True
            assert created_template.version == 1
            assert created_template.metadata["test"] is True
            
            template_id = created_template.id
            print(f"✅ CREATE: Template created with ID {template_id}")
            
            # Test GET BY ID
            retrieved_template = await template_service.get_template_by_id(template_id)
            
            assert retrieved_template is not None
            assert retrieved_template.id == template_id
            assert retrieved_template.name == test_template_request.name
            print(f"✅ READ: Template retrieved successfully")
            
            # Test LIST TEMPLATES (should include our test template)
            all_templates = await template_service.list_templates(include_inactive=True)
            test_templates = [t for t in all_templates if t.id == template_id]
            assert len(test_templates) == 1
            print(f"✅ LIST: Template found in list ({len(all_templates)} total templates)")
            
            # Test LIST BY CATEGORY
            test_category_templates = await template_service.list_templates(category="TEST")
            test_templates_in_category = [t for t in test_category_templates if t.id == template_id]
            assert len(test_templates_in_category) == 1
            print(f"✅ LIST BY CATEGORY: Template found in TEST category")
            
            # Test LIST SUMMARIES
            summaries = await template_service.list_template_summaries(category="TEST")
            summary_matches = [s for s in summaries if s.id == template_id]
            assert len(summary_matches) == 1
            assert summary_matches[0].name == test_template_request.name
            # Note: summaries don't include prompt_text, so we can't check that
            print(f"✅ LIST SUMMARIES: Template summary retrieved")
            
            # Test UPDATE
            update_request = UpdateTemplateRequest(
                name="Updated Test Template - Production",
                description="Updated description for production test",
                metadata={
                    "test": True,
                    "updated": True,
                    "validation_step": "update_test"
                }
            )
            
            updated_template = await template_service.update_template(template_id, update_request)
            
            assert updated_template is not None
            assert updated_template.id == template_id
            assert updated_template.name == update_request.name
            assert updated_template.description == update_request.description
            assert updated_template.metadata["updated"] is True
            assert updated_template.prompt_text == test_template_request.prompt_text  # Should remain unchanged
            print(f"✅ UPDATE: Template updated successfully")
            
            # Test SOFT DELETE
            delete_result = await template_service.delete_template(template_id)
            assert delete_result is True
            print(f"✅ DELETE: Template soft deleted successfully")
            
            # Verify soft delete (should not appear in active list)
            active_templates = await template_service.list_templates(category="TEST", include_inactive=False)
            active_test_templates = [t for t in active_templates if t.id == template_id]
            assert len(active_test_templates) == 0
            print(f"✅ DELETE VERIFICATION: Template not in active list")
            
            # Verify soft delete (should appear in inactive list)
            inactive_templates = await template_service.list_templates(category="TEST", include_inactive=True)
            inactive_test_templates = [t for t in inactive_templates if t.id == template_id]
            assert len(inactive_test_templates) == 1
            assert inactive_test_templates[0].is_active is False
            print(f"✅ DELETE VERIFICATION: Template found in inactive list")
            
            print("🎉 All CRUD operations validated successfully against production database!")
            
        except Exception as e:
            print(f"❌ Production validation failed: {e}")
            raise
        
        finally:
            # Cleanup: Ensure test template is removed
            if created_template and created_template.id:
                try:
                    await template_service.delete_template(created_template.id)
                    print(f"🧹 Cleanup: Test template {created_template.id} cleaned up")
                except:
                    pass  # Cleanup failed, but test already ran

    @pytest.mark.asyncio
    async def test_get_nonexistent_template_production(self, template_service: TemplateService):
        """Test retrieving non-existent template returns None"""
        nonexistent_id = "00000000-0000-0000-0000-000000000000"
        result = await template_service.get_template_by_id(nonexistent_id)
        assert result is None
        print("✅ GET NON-EXISTENT: Returns None as expected")

    @pytest.mark.asyncio
    async def test_update_nonexistent_template_production(self, template_service: TemplateService):
        """Test updating non-existent template returns None"""
        nonexistent_id = "00000000-0000-0000-0000-000000000000"
        update_request = UpdateTemplateRequest(name="Should not work")
        
        result = await template_service.update_template(nonexistent_id, update_request)
        assert result is None
        print("✅ UPDATE NON-EXISTENT: Returns None as expected")

    @pytest.mark.asyncio  
    async def test_delete_nonexistent_template_production(self, template_service: TemplateService):
        """Test deleting non-existent template returns False"""
        nonexistent_id = "00000000-0000-0000-0000-000000000000"
        result = await template_service.delete_template(nonexistent_id)
        assert result is False
        print("✅ DELETE NON-EXISTENT: Returns False as expected")

    @pytest.mark.asyncio
    async def test_list_existing_production_templates(self, template_service: TemplateService):
        """Test listing existing production templates (CTO, CIO, CISO)"""
        # Test that we can retrieve the default production templates
        all_templates = await template_service.list_templates()
        
        assert len(all_templates) >= 3  # Should have at least the default templates
        
        # Check for expected categories
        categories = {t.category for t in all_templates}
        expected_categories = {"CTO", "CIO", "CISO"}
        assert expected_categories.issubset(categories), f"Missing categories: {expected_categories - categories}"
        
        print(f"✅ LIST PRODUCTION: Found {len(all_templates)} templates with categories: {sorted(categories)}")
        
        # Test category filtering
        cto_templates = await template_service.get_templates_by_category("CTO")
        assert len(cto_templates) >= 1
        assert all(t.category == "CTO" for t in cto_templates)
        print(f"✅ CATEGORY FILTERING: Found {len(cto_templates)} CTO templates")

    @pytest.mark.asyncio
    async def test_production_template_content_validation(self, template_service: TemplateService):
        """Test that production templates have expected content structure"""
        templates = await template_service.list_templates()
        
        for template in templates[:3]:  # Check first 3 templates
            # Validate required fields
            assert template.id is not None
            assert template.name is not None and len(template.name) > 0
            assert template.category is not None and len(template.category) > 0
            assert template.prompt_text is not None and len(template.prompt_text) > 10  # Should have substantial content
            assert template.version >= 1
            assert template.created_at is not None
            assert template.updated_at is not None
            
            # Validate metadata structure if present
            if template.metadata:
                assert isinstance(template.metadata, dict)
            
            print(f"✅ VALIDATION: Template {template.name} has valid structure")

    @pytest.mark.asyncio
    async def test_error_handling_invalid_category_production(self, template_service: TemplateService):
        """Test error handling with invalid category filter"""
        # Should return empty list for non-existent category, not error
        result = await template_service.list_templates(category="NONEXISTENT_CATEGORY")
        assert isinstance(result, list)
        assert len(result) == 0
        print("✅ INVALID CATEGORY: Returns empty list as expected")


if __name__ == "__main__":
    # Allow running this test file directly for quick production validation
    async def run_production_tests():
        """Run production validation tests directly"""
        print("🚀 Starting TemplateService production validation...")
        
        # Create service instance
        client = SupabaseClient()
        await client._ensure_client()
        service = TemplateService(client)
        
        # Create test instance
        test_instance = TestTemplateServiceProduction()
        
        # Create test request
        test_request = CreateTemplateRequest(
            name="Direct Test Template",
            category="TEST", 
            prompt_text="Direct validation test template",
            description="Created by direct test run",
            is_active=True,
            metadata={"direct_test": True}
        )
        
        try:
            # Run main CRUD test
            await test_instance.test_template_crud_operations_production(service, test_request)
            
            # Run other tests
            await test_instance.test_list_existing_production_templates(service)
            await test_instance.test_production_template_content_validation(service)
            
            print("✅ All production validation tests passed!")
            
        except Exception as e:
            print(f"❌ Production validation failed: {e}")
            raise

    # Uncomment to run directly: asyncio.run(run_production_tests())
