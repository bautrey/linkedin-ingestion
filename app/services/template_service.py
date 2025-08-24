"""
Template service for managing prompt templates

Handles CRUD operations for prompt templates using Supabase database
"""

import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from app.core.logging import LoggerMixin
from app.models.template_models import (
    PromptTemplate,
    CreateTemplateRequest,
    UpdateTemplateRequest,
    TemplateSummary
)


class TemplateService(LoggerMixin):
    """Service for managing prompt templates with Supabase database operations"""
    
    def __init__(self, supabase_client):
        """
        Initialize template service with Supabase client
        
        Args:
            supabase_client: Async Supabase client instance
        """
        self.client = supabase_client
    
    async def get_template_by_id(self, template_id: str) -> Optional[PromptTemplate]:
        """
        Retrieve a template by its ID
        
        Args:
            template_id: UUID string of the template
            
        Returns:
            PromptTemplate instance if found, None otherwise
        """
        await self.client._ensure_client()
        self.logger.info("Retrieving template by ID", template_id=template_id)
        
        try:
            table = self.client.client.table("prompt_templates")
            result = await table.select("*").eq("id", template_id).execute()
            
            if result.data and len(result.data) > 0:
                template_data = result.data[0]
                self.logger.info(
                    "Template retrieved successfully",
                    template_id=template_id,
                    template_name=template_data.get("name")
                )
                return self._convert_db_to_model(template_data)
            else:
                self.logger.info("Template not found", template_id=template_id)
                return None
                
        except Exception as e:
            self.logger.error(
                "Failed to retrieve template",
                template_id=template_id,
                error=str(e),
                error_type=type(e).__name__
            )
            raise
    
    async def list_templates(
        self, 
        category: Optional[str] = None,
        include_inactive: bool = False,
        limit: Optional[int] = None
    ) -> List[PromptTemplate]:
        """
        List templates with optional filtering
        
        Args:
            category: Filter by template category (CTO, CIO, CISO, etc.)
            include_inactive: Include inactive templates (default: False)
            limit: Maximum number of templates to return
            
        Returns:
            List of PromptTemplate instances
        """
        await self.client._ensure_client()
        self.logger.info(
            "Listing templates",
            category=category,
            include_inactive=include_inactive,
            limit=limit
        )
        
        try:
            table = self.client.client.table("prompt_templates")
            query = table.select("*")
            
            # Apply category filter
            if category:
                query = query.eq("category", category.upper())
            
            # Apply active status filter
            if not include_inactive:
                query = query.eq("is_active", True)
            
            # Apply limit
            if limit:
                query = query.limit(limit)
            
            # Order by creation date (newest first)
            query = query.order("created_at", desc=True)
            
            result = await query.execute()
            
            templates = []
            if result.data:
                for template_data in result.data:
                    template = self._convert_db_to_model(template_data)
                    templates.append(template)
            
            self.logger.info(
                "Templates retrieved successfully",
                count=len(templates),
                category=category,
                include_inactive=include_inactive
            )
            
            return templates
            
        except Exception as e:
            self.logger.error(
                "Failed to list templates",
                category=category,
                error=str(e),
                error_type=type(e).__name__
            )
            raise
    
    async def get_templates_for_role(self, role: str) -> List[PromptTemplate]:
        """
        Get templates that match a specific role category
        
        Args:
            role: Role string (CTO, CIO, CISO)
            
        Returns:
            List of active PromptTemplate instances for the role
        """
        self.logger.info("Retrieving templates for role", role=role)
        
        # Get templates for the specific role category
        templates = await self.list_templates(
            category=role.upper(),
            include_inactive=False,  # Only active templates
            limit=10  # Reasonable limit
        )
        
        self.logger.info(
            "Retrieved templates for role",
            role=role,
            template_count=len(templates)
        )
        
        return templates
    
    async def get_default_template_for_role(self, role: str) -> Optional[PromptTemplate]:
        """
        Get the default/recommended template for a specific role
        
        Args:
            role: Role string (CTO, CIO, CISO)
            
        Returns:
            Default PromptTemplate for the role, or None if none found
        """
        self.logger.info("Retrieving default template for role", role=role)
        
        templates = await self.get_templates_for_role(role)
        
        if not templates:
            self.logger.info("No templates found for role", role=role)
            return None
        
        # Return the first (most recently created) active template
        # In the future, this could be enhanced with a "is_default" flag
        default_template = templates[0]
        
        self.logger.info(
            "Default template selected for role",
            role=role,
            template_id=str(default_template.id),
            template_name=default_template.name
        )
        
        return default_template
    
    async def list_template_summaries(
        self, 
        category: Optional[str] = None,
        include_inactive: bool = False,
        limit: Optional[int] = None
    ) -> List[TemplateSummary]:
        """
        List template summaries (without full prompt text) for performance
        
        Args:
            category: Filter by template category
            include_inactive: Include inactive templates
            limit: Maximum number of templates to return
            
        Returns:
            List of TemplateSummary instances
        """
        await self.client._ensure_client()
        self.logger.info("Listing template summaries", category=category)
        
        try:
            table = self.client.client.table("prompt_templates")
            query = table.select("id, name, category, description, version, is_active, created_at, updated_at, metadata")
            
            # Apply same filtering as list_templates
            if category:
                query = query.eq("category", category.upper())
            
            if not include_inactive:
                query = query.eq("is_active", True)
            
            if limit:
                query = query.limit(limit)
                
            query = query.order("created_at", desc=True)
            
            result = await query.execute()
            
            summaries = []
            if result.data:
                for summary_data in result.data:
                    summary = TemplateSummary(**summary_data)
                    summaries.append(summary)
            
            self.logger.info("Template summaries retrieved", count=len(summaries))
            return summaries
            
        except Exception as e:
            self.logger.error(
                "Failed to list template summaries",
                error=str(e),
                error_type=type(e).__name__
            )
            raise
    
    async def create_template(self, request: CreateTemplateRequest) -> PromptTemplate:
        """
        Create a new template
        
        Args:
            request: CreateTemplateRequest with template data
            
        Returns:
            Created PromptTemplate instance
        """
        await self.client._ensure_client()
        template_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        
        self.logger.info(
            "Creating new template",
            template_id=template_id,
            template_name=request.name,
            category=request.category
        )
        
        # Prepare template data for database
        template_data = {
            "id": template_id,
            "name": request.name,
            "category": request.category,
            "prompt_text": request.prompt_text,
            "description": request.description,
            "stage": request.stage,  # Add stage field for model selection
            "is_active": request.is_active,
            "version": 1,  # New templates start at version 1
            "metadata": request.metadata,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat()
        }
        
        try:
            table = self.client.client.table("prompt_templates")
            result = await table.insert(template_data).execute()
            
            if result.data and len(result.data) > 0:
                created_template_data = result.data[0]
                template = self._convert_db_to_model(created_template_data)
                
                self.logger.info(
                    "Template created successfully",
                    template_id=template_id,
                    template_name=request.name,
                    category=request.category
                )
                
                return template
            else:
                raise ValueError("Template creation failed - no data returned")
                
        except Exception as e:
            self.logger.error(
                "Failed to create template",
                template_name=request.name,
                error=str(e),
                error_type=type(e).__name__
            )
            raise
    
    async def update_template(
        self, 
        template_id: str, 
        request: UpdateTemplateRequest
    ) -> Optional[PromptTemplate]:
        """
        Update an existing template
        
        Args:
            template_id: UUID string of the template to update
            request: UpdateTemplateRequest with updated fields
            
        Returns:
            Updated PromptTemplate instance if found and updated, None if not found
        """
        await self.client._ensure_client()
        self.logger.info("Updating template", template_id=template_id)
        
        # Build update data from non-None fields
        update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
        
        if request.name is not None:
            update_data["name"] = request.name
        if request.description is not None:
            update_data["description"] = request.description
        if request.prompt_text is not None:
            update_data["prompt_text"] = request.prompt_text
        if request.is_active is not None:
            update_data["is_active"] = request.is_active
        if request.metadata is not None:
            update_data["metadata"] = request.metadata
        
        try:
            table = self.client.client.table("prompt_templates")
            result = await table.update(update_data).eq("id", template_id).execute()
            
            if result.data and len(result.data) > 0:
                updated_template_data = result.data[0]
                template = self._convert_db_to_model(updated_template_data)
                
                self.logger.info(
                    "Template updated successfully",
                    template_id=template_id,
                    updated_fields=list(update_data.keys())
                )
                
                return template
            else:
                self.logger.info("Template not found for update", template_id=template_id)
                return None
                
        except Exception as e:
            self.logger.error(
                "Failed to update template",
                template_id=template_id,
                error=str(e),
                error_type=type(e).__name__
            )
            raise
    
    async def delete_template(self, template_id: str) -> bool:
        """
        Soft delete a template (sets is_active to False)
        
        Args:
            template_id: UUID string of the template to delete
            
        Returns:
            True if template was found and deleted, False otherwise
        """
        await self.client._ensure_client()
        self.logger.info("Soft deleting template", template_id=template_id)
        
        try:
            # Soft delete by setting is_active to False
            update_data = {
                "is_active": False,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            table = self.client.client.table("prompt_templates")
            result = await table.update(update_data).eq("id", template_id).execute()
            
            if result.data and len(result.data) > 0:
                self.logger.info("Template soft deleted successfully", template_id=template_id)
                return True
            else:
                self.logger.info("Template not found for deletion", template_id=template_id)
                return False
                
        except Exception as e:
            self.logger.error(
                "Failed to delete template",
                template_id=template_id,
                error=str(e),
                error_type=type(e).__name__
            )
            raise
    
    async def get_templates_by_category(self, category: str) -> List[PromptTemplate]:
        """
        Get all active templates for a specific category
        
        Args:
            category: Template category (CTO, CIO, CISO, etc.)
            
        Returns:
            List of active templates in the category
        """
        return await self.list_templates(category=category, include_inactive=False)
    
    def _parse_datetime(self, datetime_str: str) -> datetime:
        """
        Parse datetime string with flexible microsecond precision
        
        Args:
            datetime_str: ISO format datetime string
            
        Returns:
            datetime object
        """
        try:
            # First try standard parsing
            clean_str = datetime_str.replace('Z', '+00:00')
            return datetime.fromisoformat(clean_str)
        except ValueError:
            # Handle non-standard microsecond precision
            import re
            # Extract the microsecond part and normalize it to 6 digits
            match = re.match(r'([^.]+)(?:\.([0-9]+))?([+-][0-9:]+|Z)$', datetime_str)
            if match:
                date_part, microsec_part, tz_part = match.groups()
                
                if microsec_part:
                    # Pad or truncate to 6 digits
                    microsec_part = microsec_part.ljust(6, '0')[:6]
                    normalized_str = f"{date_part}.{microsec_part}{tz_part}"
                else:
                    normalized_str = f"{date_part}{tz_part}"
                
                # Replace Z with +00:00
                normalized_str = normalized_str.replace('Z', '+00:00')
                return datetime.fromisoformat(normalized_str)
            else:
                # Fallback: just replace Z and try again
                clean_str = datetime_str.replace('Z', '+00:00')
                return datetime.fromisoformat(clean_str)
    
    def _convert_db_to_model(self, db_data: Dict[str, Any]) -> PromptTemplate:
        """
        Convert database record to PromptTemplate model
        
        Args:
            db_data: Dictionary from Supabase query result
            
        Returns:
            PromptTemplate instance
        """
        try:
            # Convert string timestamps to datetime objects if needed
            created_at = db_data["created_at"]
            updated_at = db_data["updated_at"]
            
            if isinstance(created_at, str):
                created_at = self._parse_datetime(created_at)
            if isinstance(updated_at, str):
                updated_at = self._parse_datetime(updated_at)
            
            return PromptTemplate(
                id=db_data["id"],
                name=db_data["name"],
                category=db_data["category"],
                prompt_text=db_data["prompt_text"],
                version=db_data["version"],
                is_active=db_data["is_active"],
                description=db_data.get("description"),
                stage=db_data.get("stage"),  # Add stage field
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
