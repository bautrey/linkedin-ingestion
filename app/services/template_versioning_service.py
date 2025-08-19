"""
Template versioning service for managing template versions, history, and comparisons

Extends the existing template service to provide comprehensive version management
"""

import uuid
import json
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timezone
from difflib import unified_diff
import re

from app.core.logging import LoggerMixin
from app.models.template_models import (
    PromptTemplate,
    CreateTemplateRequest,
    UpdateTemplateRequest,
    TemplateSummary
)


class TemplateVersioningService(LoggerMixin):
    """Service for managing template versions, history, and comparisons"""
    
    def __init__(self, supabase_client):
        """
        Initialize versioning service with Supabase client
        
        Args:
            supabase_client: Async Supabase client instance
        """
        self.client = supabase_client

    # Version Management Methods
    
    async def create_version(
        self, 
        template_id: str, 
        changes: Dict[str, Any],
        version_label: Optional[str] = None,
        change_summary: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> PromptTemplate:
        """
        Create new version of existing template
        
        Args:
            template_id: UUID of the original template
            changes: Dictionary of fields to change
            version_label: Optional custom version label
            change_summary: Optional description of changes
            created_by: User creating the version
            
        Returns:
            New PromptTemplate version
        """
        await self.client._ensure_client()
        
        self.logger.info(
            "Creating template version",
            template_id=template_id,
            version_label=version_label,
            change_summary=change_summary
        )
        
        try:
            # Get the original template
            original_template = await self._get_template_by_id(template_id)
            if not original_template:
                raise ValueError(f"Template {template_id} not found")
            
            # Get next version number
            next_version = await self._get_next_version_number(template_id)
            
            # Create new template record as a version
            new_template_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc)
            
            # Build new template data with changes applied
            new_template_data = {
                "id": new_template_id,
                "name": changes.get("name", original_template["name"]),
                "category": changes.get("category", original_template["category"]),
                "prompt_text": changes.get("prompt_text", original_template["prompt_text"]),
                "description": changes.get("description", original_template["description"]),
                "metadata": changes.get("metadata", original_template["metadata"]),
                "version": next_version,
                "version_label": version_label or f"v{next_version}.0",
                "version_notes": change_summary,
                "parent_template_id": template_id,
                "is_active": changes.get("is_active", original_template["is_active"]),
                "is_current_version": True,  # New version becomes current
                "created_by": created_by,
                "created_at": now.isoformat(),
                "updated_at": now.isoformat()
            }
            
            # Insert new template version
            table = self.client.client.table("prompt_templates")
            result = await table.insert(new_template_data).execute()
            
            if not result.data or len(result.data) == 0:
                raise ValueError("Failed to create template version")
            
            # Mark previous version as not current
            await table.update({"is_current_version": False}).eq("id", template_id).execute()
            
            # Create version history record
            await self._create_version_history_record(
                template_id=new_template_id,
                version_number=next_version,
                version_label=version_label,
                previous_version_id=template_id,
                change_type='update',
                change_summary=change_summary,
                changed_fields=list(changes.keys()),
                created_by=created_by
            )
            
            created_template = self._convert_db_to_model(result.data[0])
            
            self.logger.info(
                "Template version created successfully",
                template_id=template_id,
                new_version_id=new_template_id,
                version_number=next_version
            )
            
            return created_template
            
        except Exception as e:
            self.logger.error(
                "Failed to create template version",
                template_id=template_id,
                error=str(e),
                error_type=type(e).__name__
            )
            raise
    
    async def get_version_history(
        self, 
        template_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get complete version history for a template
        
        Args:
            template_id: UUID of the template
            limit: Maximum number of versions to return
            
        Returns:
            List of version history records
        """
        await self.client._ensure_client()
        
        self.logger.info("Retrieving version history", template_id=template_id)
        
        try:
            table = self.client.client.table("template_version_history")
            query = table.select("*").eq("template_id", template_id).order("version_number", desc=True)
            
            if limit:
                query = query.limit(limit)
            
            result = await query.execute()
            
            history = result.data if result.data else []
            
            self.logger.info(
                "Version history retrieved",
                template_id=template_id,
                version_count=len(history)
            )
            
            return history
            
        except Exception as e:
            self.logger.error(
                "Failed to retrieve version history",
                template_id=template_id,
                error=str(e)
            )
            raise
    
    async def compare_versions(
        self, 
        version_a_id: str, 
        version_b_id: str
    ) -> Dict[str, Any]:
        """
        Compare two versions and return diff
        
        Args:
            version_a_id: UUID of first version
            version_b_id: UUID of second version
            
        Returns:
            Comparison result with diff data
        """
        await self.client._ensure_client()
        
        self.logger.info(
            "Comparing template versions",
            version_a=version_a_id,
            version_b=version_b_id
        )
        
        try:
            # Check if diff is already cached
            cached_diff = await self._get_cached_diff(version_a_id, version_b_id)
            if cached_diff:
                return cached_diff
            
            # Get both versions
            version_a = await self._get_template_by_id(version_a_id)
            version_b = await self._get_template_by_id(version_b_id)
            
            if not version_a or not version_b:
                raise ValueError("One or both template versions not found")
            
            # Calculate diff
            diff_result = self._calculate_template_diff(version_a, version_b)
            
            # Cache the result
            await self._cache_diff(version_a_id, version_b_id, diff_result)
            
            self.logger.info(
                "Version comparison completed",
                version_a=version_a_id,
                version_b=version_b_id,
                changes_count=len(diff_result["changes"])
            )
            
            return {
                "version_a": version_a,
                "version_b": version_b,
                "diff": diff_result,
                "summary": {
                    "total_changes": len(diff_result["changes"]),
                    "field_changes": list(set(change["field"] for change in diff_result["changes"]))
                }
            }
            
        except Exception as e:
            self.logger.error(
                "Failed to compare versions",
                version_a=version_a_id,
                version_b=version_b_id,
                error=str(e)
            )
            raise
    
    async def restore_version(
        self, 
        template_id: str, 
        version_id: str,
        change_summary: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> PromptTemplate:
        """
        Restore previous version as current
        
        Args:
            template_id: UUID of the main template
            version_id: UUID of the version to restore
            change_summary: Optional description of restoration
            created_by: User performing the restoration
            
        Returns:
            Restored PromptTemplate
        """
        await self.client._ensure_client()
        
        self.logger.info(
            "Restoring template version",
            template_id=template_id,
            version_id=version_id
        )
        
        try:
            # Get the version to restore
            version_to_restore = await self._get_template_by_id(version_id)
            if not version_to_restore:
                raise ValueError(f"Version {version_id} not found")
            
            # Get next version number
            next_version = await self._get_next_version_number(template_id)
            
            # Create new version from the restored template
            restored_template_data = {
                "id": str(uuid.uuid4()),
                "name": version_to_restore["name"],
                "category": version_to_restore["category"], 
                "prompt_text": version_to_restore["prompt_text"],
                "description": version_to_restore["description"],
                "metadata": version_to_restore["metadata"],
                "version": next_version,
                "version_label": f"v{next_version}.0-restored",
                "version_notes": change_summary or f"Restored from version {version_to_restore['version']}",
                "parent_template_id": template_id,
                "is_active": version_to_restore["is_active"],
                "is_current_version": True,
                "created_by": created_by,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            # Insert restored version
            table = self.client.client.table("prompt_templates")
            result = await table.insert(restored_template_data).execute()
            
            if not result.data:
                raise ValueError("Failed to restore template version")
            
            # Mark other versions as not current
            await table.update({"is_current_version": False}).neq("id", restored_template_data["id"]).execute()
            
            # Create version history record for restoration
            await self._create_version_history_record(
                template_id=restored_template_data["id"],
                version_number=next_version,
                version_label=restored_template_data["version_label"],
                previous_version_id=version_id,
                change_type='restore',
                change_summary=change_summary or f"Restored from version {version_to_restore['version']}",
                changed_fields=["name", "prompt_text", "description"],
                created_by=created_by
            )
            
            restored_template = self._convert_db_to_model(result.data[0])
            
            self.logger.info(
                "Template version restored successfully",
                template_id=template_id,
                version_id=version_id,
                restored_id=restored_template_data["id"]
            )
            
            return restored_template
            
        except Exception as e:
            self.logger.error(
                "Failed to restore template version",
                template_id=template_id,
                version_id=version_id,
                error=str(e)
            )
            raise
    
    async def set_active_version(
        self, 
        template_id: str, 
        version_id: str
    ) -> PromptTemplate:
        """
        Set specific version as active for scoring
        
        Args:
            template_id: UUID of the main template
            version_id: UUID of the version to set as active
            
        Returns:
            Updated PromptTemplate
        """
        await self.client._ensure_client()
        
        self.logger.info(
            "Setting active template version",
            template_id=template_id,
            version_id=version_id
        )
        
        try:
            # Set all versions of this template to inactive
            table = self.client.client.table("prompt_templates")
            await table.update({"is_active": False}).eq("parent_template_id", template_id).execute()
            await table.update({"is_active": False}).eq("id", template_id).execute()
            
            # Set specified version as active
            result = await table.update({"is_active": True}).eq("id", version_id).execute()
            
            if not result.data:
                raise ValueError(f"Version {version_id} not found")
            
            # Create version history record
            await self._create_version_history_record(
                template_id=version_id,
                version_number=result.data[0]["version"],
                change_type='activate',
                change_summary=f"Set as active version for scoring",
                changed_fields=["is_active"]
            )
            
            active_template = self._convert_db_to_model(result.data[0])
            
            self.logger.info(
                "Template version set as active",
                template_id=template_id,
                version_id=version_id
            )
            
            return active_template
            
        except Exception as e:
            self.logger.error(
                "Failed to set active version",
                template_id=template_id,
                version_id=version_id,
                error=str(e)
            )
            raise
    
    async def get_template_family(
        self, 
        parent_id: str
    ) -> List[PromptTemplate]:
        """
        Get all versions of a template family
        
        Args:
            parent_id: UUID of the parent template
            
        Returns:
            List of all template versions in the family
        """
        await self.client._ensure_client()
        
        try:
            table = self.client.client.table("prompt_templates")
            # Get parent template and all its children
            parent_result = await table.select("*").eq("id", parent_id).execute()
            children_result = await table.select("*").eq("parent_template_id", parent_id).order("version", desc=True).execute()
            
            family_templates = []
            
            if parent_result.data:
                family_templates.extend([self._convert_db_to_model(t) for t in parent_result.data])
            
            if children_result.data:
                family_templates.extend([self._convert_db_to_model(t) for t in children_result.data])
            
            self.logger.info(
                "Template family retrieved",
                parent_id=parent_id,
                family_size=len(family_templates)
            )
            
            return family_templates
            
        except Exception as e:
            self.logger.error(
                "Failed to get template family",
                parent_id=parent_id,
                error=str(e)
            )
            raise
    
    # Helper Methods
    
    async def _get_template_by_id(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get template by ID, returning raw database data"""
        table = self.client.client.table("prompt_templates")
        result = await table.select("*").eq("id", template_id).execute()
        
        if result.data and len(result.data) > 0:
            return result.data[0]
        return None
    
    async def _get_next_version_number(self, template_id: str) -> int:
        """Get the next version number for a template"""
        table = self.client.client.table("template_version_history")
        result = await table.select("version_number").eq("template_id", template_id).order("version_number", desc=True).limit(1).execute()
        
        if result.data and len(result.data) > 0:
            return result.data[0]["version_number"] + 1
        else:
            # Check current template version
            template = await self._get_template_by_id(template_id)
            if template:
                return template["version"] + 1
            return 1
    
    async def _create_version_history_record(
        self,
        template_id: str,
        version_number: int,
        change_type: str,
        changed_fields: List[str],
        version_label: Optional[str] = None,
        previous_version_id: Optional[str] = None,
        change_summary: Optional[str] = None,
        created_by: Optional[str] = None
    ):
        """Create a version history record"""
        history_data = {
            "id": str(uuid.uuid4()),
            "template_id": template_id,
            "version_number": version_number,
            "version_label": version_label,
            "previous_version_id": previous_version_id,
            "change_type": change_type,
            "change_summary": change_summary,
            "changed_fields": json.dumps(changed_fields),
            "created_by": created_by,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        table = self.client.client.table("template_version_history")
        await table.insert(history_data).execute()
    
    def _calculate_template_diff(self, version_a: Dict[str, Any], version_b: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate differences between two template versions"""
        changes = []
        stats = {"additions": 0, "deletions": 0, "modifications": 0}
        
        # Fields to compare
        comparable_fields = ["name", "prompt_text", "description", "category", "metadata"]
        
        for field in comparable_fields:
            value_a = version_a.get(field, "")
            value_b = version_b.get(field, "")
            
            if value_a != value_b:
                # Convert to string for comparison
                str_a = json.dumps(value_a) if isinstance(value_a, dict) else str(value_a)
                str_b = json.dumps(value_b) if isinstance(value_b, dict) else str(value_b)
                
                if field == "prompt_text":
                    # For prompt text, generate line-by-line diff
                    lines_a = str_a.splitlines()
                    lines_b = str_b.splitlines()
                    
                    diff_lines = list(unified_diff(lines_a, lines_b, lineterm=""))
                    
                    change = {
                        "type": "modification",
                        "field": field,
                        "old_value": str_a,
                        "new_value": str_b,
                        "diff_lines": diff_lines
                    }
                else:
                    change = {
                        "type": "modification",
                        "field": field,
                        "old_value": str_a,
                        "new_value": str_b
                    }
                
                changes.append(change)
                stats["modifications"] += 1
        
        return {
            "changes": changes,
            "stats": stats
        }
    
    async def _get_cached_diff(self, version_a_id: str, version_b_id: str) -> Optional[Dict[str, Any]]:
        """Get cached diff between two versions"""
        try:
            table = self.client.client.table("template_version_diffs")
            result = await table.select("diff_data, diff_summary").eq("version_a_id", version_a_id).eq("version_b_id", version_b_id).execute()
            
            if result.data and len(result.data) > 0:
                return {
                    "diff": result.data[0]["diff_data"],
                    "summary": result.data[0]["diff_summary"]
                }
            return None
            
        except Exception as e:
            self.logger.warning("Failed to get cached diff", error=str(e))
            return None
    
    async def _cache_diff(self, version_a_id: str, version_b_id: str, diff_data: Dict[str, Any]):
        """Cache diff result for performance"""
        try:
            cache_data = {
                "id": str(uuid.uuid4()),
                "version_a_id": version_a_id,
                "version_b_id": version_b_id,
                "diff_data": diff_data,
                "diff_summary": diff_data.get("stats", {}),
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            table = self.client.client.table("template_version_diffs")
            await table.insert(cache_data).execute()
            
        except Exception as e:
            self.logger.warning("Failed to cache diff", error=str(e))
    
    def _convert_db_to_model(self, db_data: Dict[str, Any]) -> PromptTemplate:
        """Convert database record to PromptTemplate model"""
        try:
            # Convert string timestamps to datetime objects if needed
            created_at = db_data["created_at"]
            updated_at = db_data["updated_at"]
            
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            if isinstance(updated_at, str):
                updated_at = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
            
            return PromptTemplate(
                id=db_data["id"],
                name=db_data["name"],
                category=db_data["category"],
                prompt_text=db_data["prompt_text"],
                version=db_data["version"],
                is_active=db_data["is_active"],
                description=db_data.get("description"),
                metadata=db_data.get("metadata", {}),
                created_at=created_at,
                updated_at=updated_at
            )
        except Exception as e:
            self.logger.error(
                "Failed to convert database data to model",
                error=str(e),
                db_data_keys=list(db_data.keys())
            )
            raise
