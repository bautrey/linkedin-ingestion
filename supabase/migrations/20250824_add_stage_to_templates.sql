-- Add stage column to prompt_templates table for stage-based model selection
-- Migration: 20250824_add_stage_to_templates.sql

-- Add the stage column
ALTER TABLE prompt_templates 
ADD COLUMN stage VARCHAR(50) NULL;

-- Add a helpful comment
COMMENT ON COLUMN prompt_templates.stage IS 'Evaluation stage (stage_2_screening, stage_3_analysis) - determines which model to use automatically';

-- Create an index for efficient filtering by stage
CREATE INDEX idx_prompt_templates_stage ON prompt_templates(stage);

-- Update existing templates with stage classification based on their purpose
-- Set basic/evaluation templates to Stage 2 (cost-effective screening)
UPDATE prompt_templates 
SET stage = 'stage_2_screening'
WHERE name ILIKE '%evaluation%' 
   OR name ILIKE '%basic%'
   OR name ILIKE '%screening%'
   OR name ILIKE '%quick%'
   OR name ILIKE '%sanity%'
   OR name ILIKE '%filter%';

-- Set enhanced/comprehensive templates to Stage 3 (premium analysis)
UPDATE prompt_templates 
SET stage = 'stage_3_analysis'
WHERE name ILIKE '%enhanced%'
   OR name ILIKE '%comprehensive%'
   OR name ILIKE '%detailed%'
   OR name ILIKE '%deep%'
   OR name ILIKE '%analysis%';

-- Migration completed successfully
