#!/usr/bin/env python3
"""
Direct production validation for TemplateService
Validates all CRUD operations against production database
"""

import asyncio
import sys
from typing import Optional

from app.services.template_service import TemplateService
from app.models.template_models import (
    PromptTemplate,
    CreateTemplateRequest,
    UpdateTemplateRequest
)
from app.database.supabase_client import SupabaseClient


async def validate_template_service():
    """Run comprehensive TemplateService production validation"""
    print("🚀 Starting TemplateService production validation...")
    
    # Initialize client and service
    client = SupabaseClient()
    await client._ensure_client()
    service = TemplateService(client)
    
    # Test data
    test_request = CreateTemplateRequest(
        name="PRODUCTION TEST - Template Service Validation",
        category="TEST",
        prompt_text="This is a production validation template for V1.88 Task 3. "
                   "Evaluate candidate technical skills, leadership potential, and cultural fit. "
                   "Focus on technical depth, team management capabilities, and strategic vision.",
        description="Created during V1.88 Task 3 production validation",
        is_active=True,
        metadata={
            "test": True,
            "validation_purpose": "v188_task3_service_layer",
            "created_by": "production_validation_script"
        }
    )
    
    created_template = None
    validation_passed = True
    
    try:
        # Test 1: CREATE Template
        print("\n📝 Testing CREATE operation...")
        created_template = await service.create_template(test_request)
        
        assert created_template is not None, "Template creation returned None"
        assert isinstance(created_template, PromptTemplate), "Created template wrong type"
        assert created_template.name == test_request.name, "Name mismatch"
        assert created_template.category == test_request.category, "Category mismatch"
        assert created_template.prompt_text == test_request.prompt_text, "Prompt text mismatch"
        assert created_template.is_active is True, "Template should be active"
        assert created_template.version == 1, "New templates should be version 1"
        assert created_template.metadata["test"] is True, "Metadata not preserved"
        
        template_id = created_template.id
        print(f"✅ CREATE: Template created successfully with ID {template_id}")
        
        # Test 2: READ by ID
        print("\n📖 Testing READ by ID operation...")
        retrieved_template = await service.get_template_by_id(template_id)
        
        assert retrieved_template is not None, "Template retrieval returned None"
        assert retrieved_template.id == template_id, "ID mismatch on retrieval"
        assert retrieved_template.name == test_request.name, "Name mismatch on retrieval"
        
        print(f"✅ READ: Template retrieved successfully")
        
        # Test 3: LIST Templates
        print("\n📋 Testing LIST operation...")
        all_templates = await service.list_templates(include_inactive=True)
        test_templates = [t for t in all_templates if t.id == template_id]
        
        assert len(test_templates) == 1, "Test template not found in list"
        print(f"✅ LIST: Found test template in list of {len(all_templates)} total templates")
        
        # Test 4: LIST by Category
        print("\n🏷️  Testing LIST BY CATEGORY operation...")
        test_category_templates = await service.list_templates(category="TEST")
        test_in_category = [t for t in test_category_templates if t.id == template_id]
        
        assert len(test_in_category) == 1, "Test template not found in category filter"
        print(f"✅ CATEGORY LIST: Found template in TEST category")
        
        # Test 5: LIST Summaries
        print("\n📄 Testing LIST SUMMARIES operation...")
        summaries = await service.list_template_summaries(category="TEST")
        summary_matches = [s for s in summaries if s.id == template_id]
        
        assert len(summary_matches) == 1, "Template summary not found"
        assert summary_matches[0].name == test_request.name, "Summary name mismatch"
        print(f"✅ SUMMARIES: Template summary retrieved correctly")
        
        # Test 6: UPDATE Template
        print("\n✏️  Testing UPDATE operation...")
        update_request = UpdateTemplateRequest(
            name="UPDATED - Production Validation Template",
            description="Updated during validation testing",
            metadata={
                "test": True,
                "validation_purpose": "v188_task3_service_layer",
                "updated": True,
                "update_step": "production_validation"
            }
        )
        
        updated_template = await service.update_template(template_id, update_request)
        
        assert updated_template is not None, "Template update returned None"
        assert updated_template.id == template_id, "ID changed during update"
        assert updated_template.name == update_request.name, "Name not updated"
        assert updated_template.description == update_request.description, "Description not updated"
        assert updated_template.metadata["updated"] is True, "Metadata not updated"
        assert updated_template.prompt_text == test_request.prompt_text, "Prompt text should be unchanged"
        
        print(f"✅ UPDATE: Template updated successfully")
        
        # Test 7: SOFT DELETE
        print("\n🗑️  Testing SOFT DELETE operation...")
        delete_result = await service.delete_template(template_id)
        
        assert delete_result is True, "Delete operation returned False"
        print(f"✅ DELETE: Template soft deleted successfully")
        
        # Test 8: Verify soft delete behavior
        print("\n🔍 Testing SOFT DELETE verification...")
        
        # Should not appear in active list
        active_templates = await service.list_templates(category="TEST", include_inactive=False)
        active_matches = [t for t in active_templates if t.id == template_id]
        assert len(active_matches) == 0, "Deleted template still appears in active list"
        
        # Should appear in inactive list
        inactive_templates = await service.list_templates(category="TEST", include_inactive=True)
        inactive_matches = [t for t in inactive_templates if t.id == template_id]
        assert len(inactive_matches) == 1, "Deleted template not found in inactive list"
        assert inactive_matches[0].is_active is False, "Template still marked as active"
        
        print(f"✅ SOFT DELETE VERIFICATION: Confirmed template is inactive")
        
        # Test 9: Error handling - non-existent operations
        print("\n❌ Testing ERROR HANDLING...")
        
        nonexistent_id = "00000000-0000-0000-0000-000000000000"
        
        # Non-existent GET
        no_template = await service.get_template_by_id(nonexistent_id)
        assert no_template is None, "Non-existent template should return None"
        
        # Non-existent UPDATE
        no_update = await service.update_template(nonexistent_id, UpdateTemplateRequest(name="Won't work"))
        assert no_update is None, "Non-existent template update should return None"
        
        # Non-existent DELETE
        no_delete = await service.delete_template(nonexistent_id)
        assert no_delete is False, "Non-existent template delete should return False"
        
        print(f"✅ ERROR HANDLING: All error cases handled correctly")
        
        # Test 10: Validate production templates exist
        print("\n🏭 Testing PRODUCTION TEMPLATES validation...")
        all_production_templates = await service.list_templates()
        
        assert len(all_production_templates) >= 3, f"Expected at least 3 templates, found {len(all_production_templates)}"
        
        categories = {t.category for t in all_production_templates}
        expected_categories = {"CTO", "CIO", "CISO"}
        missing_categories = expected_categories - categories
        assert len(missing_categories) == 0, f"Missing production template categories: {missing_categories}"
        
        # Test category filtering with production templates
        cto_templates = await service.get_templates_by_category("CTO")
        assert len(cto_templates) >= 1, "No CTO templates found"
        assert all(t.category == "CTO" for t in cto_templates), "Non-CTO templates in CTO filter"
        
        print(f"✅ PRODUCTION TEMPLATES: Found {len(all_production_templates)} templates with categories {sorted(categories)}")
        print(f"✅ CATEGORY FILTERING: Found {len(cto_templates)} CTO templates")
        
    except Exception as e:
        print(f"\n❌ VALIDATION FAILED: {e}")
        print(f"Error type: {type(e).__name__}")
        validation_passed = False
        import traceback
        traceback.print_exc()
        
    finally:
        # Cleanup: Remove test template
        if created_template and created_template.id:
            try:
                await service.delete_template(created_template.id)
                print(f"\n🧹 CLEANUP: Test template {created_template.id} removed")
            except Exception as cleanup_error:
                print(f"\n⚠️  CLEANUP WARNING: Could not remove test template: {cleanup_error}")
    
    # Final result
    if validation_passed:
        print(f"\n🎉 ALL PRODUCTION VALIDATION TESTS PASSED!")
        print("✅ V1.88 Task 3.5 & 3.6 COMPLETE: TemplateService production validation successful")
        return True
    else:
        print(f"\n💥 PRODUCTION VALIDATION FAILED!")
        return False


async def main():
    """Main entry point"""
    success = await validate_template_service()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
