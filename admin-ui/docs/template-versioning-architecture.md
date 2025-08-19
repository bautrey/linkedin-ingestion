# Template Versioning System Architecture

## Overview

The Template Versioning System builds on the existing `prompt_templates` table structure to provide comprehensive version management, history tracking, comparison, and restoration capabilities for scoring templates.

## Architecture Goals

1. **Full Version History**: Track all changes to templates with complete audit trail
2. **Version Comparison**: Visual diff capabilities to compare any two versions
3. **Easy Restoration**: One-click restoration of previous template versions  
4. **Branch Management**: Support for experimental versions and parallel development
5. **Active Version Control**: Clear designation of which version is currently active
6. **Performance Optimized**: Efficient storage and retrieval of version data

## Database Architecture

### Current State (V1.88)
```sql
prompt_templates (
    id UUID PRIMARY KEY,
    name VARCHAR(255),
    category VARCHAR(100),
    prompt_text TEXT,
    version INTEGER DEFAULT 1,  -- Simple version counter
    is_active BOOLEAN DEFAULT true,
    description TEXT,
    metadata JSONB,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)
```

### Enhanced Design (V1.9)

#### 1. Main Templates Table (Modified)
```sql
-- Keep existing table but enhance with version tracking
ALTER TABLE prompt_templates ADD COLUMN parent_template_id UUID;
ALTER TABLE prompt_templates ADD COLUMN version_label VARCHAR(50); -- e.g., "v2.1", "draft", "experimental"
ALTER TABLE prompt_templates ADD COLUMN version_notes TEXT;
ALTER TABLE prompt_templates ADD COLUMN created_by VARCHAR(100); -- Future user tracking
ALTER TABLE prompt_templates ADD COLUMN is_current_version BOOLEAN DEFAULT false;

-- Add foreign key to support template families
ALTER TABLE prompt_templates ADD CONSTRAINT fk_parent_template 
    FOREIGN KEY (parent_template_id) REFERENCES prompt_templates(id);
```

#### 2. Version History Table (New)
```sql
CREATE TABLE template_version_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID NOT NULL,  -- Points to current version in prompt_templates
    version_number INTEGER NOT NULL,
    version_label VARCHAR(50),
    previous_version_id UUID, -- Points to previous version
    change_type VARCHAR(50) NOT NULL, -- 'create', 'update', 'restore', 'branch'
    change_summary TEXT,
    changed_fields JSONB, -- Track what specific fields were modified
    created_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(100),
    
    CONSTRAINT fk_template_version_history_template 
        FOREIGN KEY (template_id) REFERENCES prompt_templates(id),
    CONSTRAINT fk_template_version_history_previous 
        FOREIGN KEY (previous_version_id) REFERENCES prompt_templates(id)
);
```

#### 3. Version Comparison Cache (New)
```sql
CREATE TABLE template_version_diffs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version_a_id UUID NOT NULL,
    version_b_id UUID NOT NULL,
    diff_data JSONB, -- Stores computed diff for performance
    created_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT fk_version_diff_a FOREIGN KEY (version_a_id) REFERENCES prompt_templates(id),
    CONSTRAINT fk_version_diff_b FOREIGN KEY (version_b_id) REFERENCES prompt_templates(id),
    CONSTRAINT unique_version_comparison UNIQUE (version_a_id, version_b_id)
);
```

## API Architecture

### Version Management Endpoints

```yaml
# Get version history for a template
GET /api/templates/{template_id}/versions
Response: {
  template_id: UUID,
  current_version: TemplateVersion,
  versions: TemplateVersion[],
  total_count: integer
}

# Create new version from existing template
POST /api/templates/{template_id}/versions
Body: {
  version_label?: string,
  change_summary?: string,
  prompt_text: string,
  description?: string,
  metadata?: object
}

# Get specific version
GET /api/templates/{template_id}/versions/{version}

# Compare two versions
GET /api/templates/{template_id}/versions/{version_a}/compare/{version_b}
Response: {
  version_a: TemplateVersion,
  version_b: TemplateVersion,
  diff: DiffResult,
  changes_summary: ChangesSummary
}

# Restore version (make it current)
PUT /api/templates/{template_id}/versions/{version}/restore
Body: {
  change_summary?: string
}

# Set active version
PUT /api/templates/{template_id}/active-version
Body: {
  version_id: UUID,
  change_summary?: string
}
```

## Data Models

### Enhanced Template Model
```typescript
interface PromptTemplate {
  id: string;
  name: string;
  category: string;
  prompt_text: string;
  description?: string;
  version: number;
  version_label?: string;  // NEW
  version_notes?: string;  // NEW
  parent_template_id?: string;  // NEW
  is_active: boolean;
  is_current_version: boolean;  // NEW
  metadata: object;
  created_at: string;
  updated_at: string;
  created_by?: string;  // NEW
}
```

### Version History Model
```typescript
interface TemplateVersionHistory {
  id: string;
  template_id: string;
  version_number: number;
  version_label?: string;
  previous_version_id?: string;
  change_type: 'create' | 'update' | 'restore' | 'branch';
  change_summary?: string;
  changed_fields: string[];
  created_at: string;
  created_by?: string;
}
```

### Diff Result Model
```typescript
interface DiffResult {
  changes: DiffChange[];
  stats: {
    additions: number;
    deletions: number;
    modifications: number;
  };
}

interface DiffChange {
  type: 'addition' | 'deletion' | 'modification';
  field: string;
  old_value?: string;
  new_value?: string;
  line_number?: number;
  context?: string;
}
```

## UI Architecture

### Version Management Pages

1. **Template Version History Page** (`/templates/{id}/versions`)
   - List all versions with timestamps, labels, and change summaries
   - Quick actions: View, Compare, Restore, Set as Active
   - Version timeline visualization
   - Filtering and search capabilities

2. **Version Comparison Page** (`/templates/{id}/versions/compare?a={ver_a}&b={ver_b}`)
   - Side-by-side comparison of two template versions
   - Highlighted differences with color coding
   - Field-level change tracking (name, prompt_text, description, metadata)
   - Export comparison report

3. **Version Creation Modal**
   - Triggered from template edit form
   - Fields: Version label, Change summary, Save as new version checkbox
   - Preview of changes before saving

### Integration with Existing UI

1. **Template List Enhancement**
   - Add version indicator column
   - Show current/active version status
   - Quick version history access

2. **Template Detail Enhancement**
   - Version info panel showing current version, total versions
   - "View History" button leading to version history page
   - "Save as New Version" action in edit mode

3. **Template Edit Enhancement**
   - Option to save changes as new version vs updating current
   - Change summary field for version creation
   - Preview of changes before saving

## Service Layer Architecture

### TemplateVersioningService

```python
class TemplateVersioningService:
    async def create_version(
        self, 
        template_id: str, 
        changes: TemplateUpdateRequest,
        version_label: Optional[str] = None,
        change_summary: Optional[str] = None
    ) -> PromptTemplate:
        """Create new version of existing template"""
        
    async def get_version_history(
        self, 
        template_id: str,
        limit: Optional[int] = None
    ) -> List[TemplateVersionHistory]:
        """Get complete version history"""
        
    async def compare_versions(
        self, 
        version_a_id: str, 
        version_b_id: str
    ) -> DiffResult:
        """Compare two versions and return diff"""
        
    async def restore_version(
        self, 
        template_id: str, 
        version_id: str,
        change_summary: Optional[str] = None
    ) -> PromptTemplate:
        """Restore previous version as current"""
        
    async def set_active_version(
        self, 
        template_id: str, 
        version_id: str
    ) -> PromptTemplate:
        """Set specific version as active for scoring"""
        
    async def get_template_family(
        self, 
        parent_id: str
    ) -> List[PromptTemplate]:
        """Get all versions of a template family"""
```

## Version Lifecycle Management

### Version States
1. **Draft**: Work-in-progress version, not ready for use
2. **Current**: Latest version of the template (default for editing)
3. **Active**: Version currently used for scoring (may be different from current)
4. **Archived**: Older version, kept for history but not actively used

### Version Numbering Strategy
- **Semantic Versioning**: Major.Minor format (e.g., 1.0, 1.1, 2.0)
- **Auto-increment**: Automatic version number assignment
- **Custom Labels**: Support for custom version labels ("draft", "experimental", "v2.1-beta")

### Performance Considerations

1. **Version History Pagination**: Limit version history queries for large template families
2. **Diff Caching**: Cache computed diffs for frequently compared versions
3. **Lazy Loading**: Load full template content only when needed
4. **Index Optimization**: Indexes on template_id, version_number, created_at

## Migration Strategy

### Phase 1: Database Enhancement
1. Add new columns to existing prompt_templates table
2. Create template_version_history table
3. Create template_version_diffs table
4. Add indexes and constraints

### Phase 2: Backend Implementation  
1. Extend TemplateService with versioning methods
2. Add version management API endpoints
3. Update existing template endpoints to be version-aware

### Phase 3: Frontend Implementation
1. Build version history UI components
2. Implement version comparison interface
3. Integrate versioning into existing template management UI

### Phase 4: Testing and Validation
1. Unit tests for versioning service methods
2. Integration tests for API endpoints
3. End-to-end UI testing for version management workflows

This architecture provides a solid foundation for comprehensive template versioning while maintaining compatibility with the existing V1.88 template system.
