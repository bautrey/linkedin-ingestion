-- V1.9 Template Versioning System Migration
-- Adds comprehensive version management to existing prompt templates
-- Migration: 20250819_v1_9_template_versioning.sql
-- Created: 2025-08-19

-- Step 1: Add new columns to existing prompt_templates table
ALTER TABLE prompt_templates ADD COLUMN IF NOT EXISTS parent_template_id UUID;
ALTER TABLE prompt_templates ADD COLUMN IF NOT EXISTS version_label VARCHAR(50);
ALTER TABLE prompt_templates ADD COLUMN IF NOT EXISTS version_notes TEXT;
ALTER TABLE prompt_templates ADD COLUMN IF NOT EXISTS created_by VARCHAR(100);
ALTER TABLE prompt_templates ADD COLUMN IF NOT EXISTS is_current_version BOOLEAN DEFAULT true;

-- Add foreign key constraint for parent template relationship
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_parent_template') THEN
        ALTER TABLE prompt_templates ADD CONSTRAINT fk_parent_template 
            FOREIGN KEY (parent_template_id) REFERENCES prompt_templates(id) ON DELETE CASCADE;
    END IF;
END $$;

-- Add index for parent template queries
CREATE INDEX IF NOT EXISTS idx_prompt_templates_parent_id ON prompt_templates(parent_template_id);
CREATE INDEX IF NOT EXISTS idx_prompt_templates_current_version ON prompt_templates(is_current_version);

-- Step 2: Create template version history table
CREATE TABLE IF NOT EXISTS template_version_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID NOT NULL,
    version_number INTEGER NOT NULL,
    version_label VARCHAR(50),
    previous_version_id UUID,
    change_type VARCHAR(50) NOT NULL DEFAULT 'update',
    change_summary TEXT,
    changed_fields JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(100),
    
    -- Constraints
    CONSTRAINT fk_template_version_history_template 
        FOREIGN KEY (template_id) REFERENCES prompt_templates(id) ON DELETE CASCADE,
    CONSTRAINT fk_template_version_history_previous 
        FOREIGN KEY (previous_version_id) REFERENCES prompt_templates(id) ON DELETE SET NULL,
    CONSTRAINT check_change_type_valid 
        CHECK (change_type IN ('create', 'update', 'restore', 'branch', 'activate')),
    CONSTRAINT check_version_number_positive 
        CHECK (version_number > 0)
);

-- Add indexes for version history queries
CREATE INDEX IF NOT EXISTS idx_template_version_history_template_id ON template_version_history(template_id);
CREATE INDEX IF NOT EXISTS idx_template_version_history_created_at ON template_version_history(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_template_version_history_version_number ON template_version_history(template_id, version_number);

-- Step 3: Create version comparison cache table for performance
CREATE TABLE IF NOT EXISTS template_version_diffs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version_a_id UUID NOT NULL,
    version_b_id UUID NOT NULL,
    diff_data JSONB,
    diff_summary JSONB, -- Summary stats: additions, deletions, modifications
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT fk_version_diff_a 
        FOREIGN KEY (version_a_id) REFERENCES prompt_templates(id) ON DELETE CASCADE,
    CONSTRAINT fk_version_diff_b 
        FOREIGN KEY (version_b_id) REFERENCES prompt_templates(id) ON DELETE CASCADE,
    CONSTRAINT unique_version_comparison 
        UNIQUE (version_a_id, version_b_id)
);

-- Add indexes for diff queries
CREATE INDEX IF NOT EXISTS idx_template_version_diffs_version_a ON template_version_diffs(version_a_id);
CREATE INDEX IF NOT EXISTS idx_template_version_diffs_version_b ON template_version_diffs(version_b_id);

-- Step 4: Enable RLS on new tables (consistent with existing security model)
ALTER TABLE template_version_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE template_version_diffs ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for new tables
CREATE POLICY "Enable all operations for api access" ON template_version_history
    FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "Enable all operations for api access" ON template_version_diffs
    FOR ALL USING (true) WITH CHECK (true);

-- Step 5: Create trigger for automatic version history tracking
CREATE OR REPLACE FUNCTION create_template_version_history()
RETURNS TRIGGER AS $$
DECLARE
    changed_fields_array TEXT[] := '{}';
    prev_version_id UUID;
    new_version_number INTEGER;
BEGIN
    -- Skip if this is an insert (initial creation)
    IF TG_OP = 'INSERT' THEN
        RETURN NEW;
    END IF;
    
    -- Determine what fields changed
    IF OLD.name IS DISTINCT FROM NEW.name THEN
        changed_fields_array := array_append(changed_fields_array, 'name');
    END IF;
    
    IF OLD.prompt_text IS DISTINCT FROM NEW.prompt_text THEN
        changed_fields_array := array_append(changed_fields_array, 'prompt_text');
    END IF;
    
    IF OLD.description IS DISTINCT FROM NEW.description THEN
        changed_fields_array := array_append(changed_fields_array, 'description');
    END IF;
    
    IF OLD.category IS DISTINCT FROM NEW.category THEN
        changed_fields_array := array_append(changed_fields_array, 'category');
    END IF;
    
    IF OLD.metadata IS DISTINCT FROM NEW.metadata THEN
        changed_fields_array := array_append(changed_fields_array, 'metadata');
    END IF;
    
    -- Only create history if there were actual content changes
    IF array_length(changed_fields_array, 1) > 0 THEN
        -- Get the previous version number and increment
        SELECT COALESCE(MAX(version_number), 0) + 1 
        INTO new_version_number
        FROM template_version_history 
        WHERE template_id = NEW.id;
        
        -- Get the previous version ID (current template before changes)
        SELECT id INTO prev_version_id FROM prompt_templates WHERE id = OLD.id;
        
        -- Insert version history record
        INSERT INTO template_version_history (
            template_id,
            version_number,
            version_label,
            previous_version_id,
            change_type,
            change_summary,
            changed_fields,
            created_by
        ) VALUES (
            NEW.id,
            new_version_number,
            NEW.version_label,
            prev_version_id,
            CASE 
                WHEN OLD.is_active IS DISTINCT FROM NEW.is_active AND NEW.is_active = true 
                THEN 'activate'
                ELSE 'update'
            END,
            NEW.version_notes,
            to_jsonb(changed_fields_array),
            NEW.created_by
        );
        
        -- Update version number on template
        NEW.version := new_version_number;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for automatic version history
DROP TRIGGER IF EXISTS trigger_template_version_history ON prompt_templates;
CREATE TRIGGER trigger_template_version_history
    BEFORE UPDATE ON prompt_templates
    FOR EACH ROW
    EXECUTE FUNCTION create_template_version_history();

-- Step 6: Migrate existing templates to new versioning system
-- Mark all existing templates as current versions and create initial history
DO $$
DECLARE
    template_record RECORD;
BEGIN
    FOR template_record IN SELECT * FROM prompt_templates LOOP
        -- Mark as current version
        UPDATE prompt_templates 
        SET is_current_version = true 
        WHERE id = template_record.id;
        
        -- Create initial version history record
        INSERT INTO template_version_history (
            template_id,
            version_number,
            version_label,
            change_type,
            change_summary,
            changed_fields,
            created_by
        ) VALUES (
            template_record.id,
            template_record.version,
            'v' || template_record.version || '.0',
            'create',
            'Initial template creation (migrated from V1.88)',
            '["name", "prompt_text", "description", "category"]'::jsonb,
            'system_migration'
        );
    END LOOP;
END $$;

-- Step 7: Create helper functions for version management

-- Function to get next version number for a template
CREATE OR REPLACE FUNCTION get_next_template_version_number(template_id UUID)
RETURNS INTEGER AS $$
DECLARE
    next_version INTEGER;
BEGIN
    SELECT COALESCE(MAX(version_number), 0) + 1 
    INTO next_version
    FROM template_version_history 
    WHERE template_version_history.template_id = $1;
    
    RETURN next_version;
END;
$$ LANGUAGE plpgsql;

-- Function to get template version history count
CREATE OR REPLACE FUNCTION get_template_version_count(template_id UUID)
RETURNS INTEGER AS $$
DECLARE
    version_count INTEGER;
BEGIN
    SELECT COUNT(*) 
    INTO version_count
    FROM template_version_history 
    WHERE template_version_history.template_id = $1;
    
    RETURN version_count;
END;
$$ LANGUAGE plpgsql;

-- Step 8: Create views for easier querying

-- View for template with version information
CREATE OR REPLACE VIEW templates_with_version_info AS
SELECT 
    pt.*,
    get_template_version_count(pt.id) as total_versions,
    CASE 
        WHEN pt.parent_template_id IS NOT NULL THEN false
        ELSE true
    END as is_primary_template,
    -- Get latest version history entry
    (SELECT jsonb_build_object(
        'change_type', tvh.change_type,
        'change_summary', tvh.change_summary,
        'changed_fields', tvh.changed_fields,
        'created_at', tvh.created_at,
        'created_by', tvh.created_by
    )
     FROM template_version_history tvh 
     WHERE tvh.template_id = pt.id 
     ORDER BY tvh.version_number DESC 
     LIMIT 1) as latest_change
FROM prompt_templates pt;

-- View for active templates (for scoring operations)
CREATE OR REPLACE VIEW active_templates_only AS
SELECT * FROM prompt_templates 
WHERE is_active = true 
ORDER BY category, name;

-- Grant permissions on new tables and views
GRANT ALL ON template_version_history TO authenticated;
GRANT ALL ON template_version_diffs TO authenticated;
GRANT SELECT ON templates_with_version_info TO authenticated;
GRANT SELECT ON active_templates_only TO authenticated;

-- Grant execute permissions on functions
GRANT EXECUTE ON FUNCTION get_next_template_version_number(UUID) TO authenticated;
GRANT EXECUTE ON FUNCTION get_template_version_count(UUID) TO authenticated;

-- Migration completed successfully
-- Template versioning system is now available with:
-- 1. Enhanced prompt_templates table with parent relationships and version tracking
-- 2. Complete version history tracking in template_version_history table
-- 3. Performance-optimized diff caching in template_version_diffs table
-- 4. Automatic version history creation via triggers
-- 5. Helper functions for version management operations
-- 6. Convenient views for querying templates with version information

COMMENT ON TABLE template_version_history IS 'Stores complete version history for all template changes';
COMMENT ON TABLE template_version_diffs IS 'Caches computed diffs between template versions for performance';
COMMENT ON FUNCTION get_next_template_version_number(UUID) IS 'Returns the next version number for a template';
COMMENT ON FUNCTION get_template_version_count(UUID) IS 'Returns total number of versions for a template';
