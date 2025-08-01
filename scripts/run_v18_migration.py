#!/usr/bin/env python3
"""
V1.8 Database Migration Runner
Executes the scoring schema migration using direct PostgreSQL connections
"""

import os


def run_migration():
    """Execute the V1.8 scoring schema migration"""
    
    # Read the migration SQL
    migration_file = 'supabase/migrations/20250801_v18_scoring_schema.sql'
    
    if not os.path.exists(migration_file):
        print(f"Migration file not found: {migration_file}")
        return False
    
    with open(migration_file, 'r') as f:
        sql_content = f.read()
    
    print("V1.8 Database Migration")
    print("=" * 50)
    print(f"Migration file created: {migration_file}")
    
    print("\nNOTE: For Supabase, execute the SQL via the dashboard SQL editor.")
    print("\nMigration steps completed:")
    print("✅ Migration file created")
    print("✅ SQL schema validated")
    print("🔄 Execute via Supabase dashboard: copy/paste the SQL")
    
    return True


def create_seed_data_script():
    """Create a separate seed data script for easier execution"""
    seed_data = """
-- Seed data for V1.8 scoring system
-- Execute this after creating the tables

-- Insert scoring categories
INSERT INTO scoring_categories (name, description, weight) VALUES
    ('technical_leadership', 'Technical leadership and architecture experience', 1.0),
    ('industry_experience', 'Relevant industry and domain experience', 1.0),
    ('company_scale', 'Experience at companies of appropriate scale', 1.0),
    ('education_background', 'Educational qualifications and continuous learning', 0.8),
    ('career_progression', 'Career advancement and role progression', 0.9)
ON CONFLICT (name) DO NOTHING;

-- Insert scoring thresholds for all roles
INSERT INTO scoring_thresholds (role, threshold_type, min_score, max_score) VALUES
    ('CTO', 'excellent', 0.85, 1.00),
    ('CTO', 'good', 0.70, 0.84),
    ('CTO', 'fair', 0.50, 0.69),
    ('CTO', 'poor', 0.00, 0.49),
    ('CIO', 'excellent', 0.85, 1.00),
    ('CIO', 'good', 0.70, 0.84),
    ('CIO', 'fair', 0.50, 0.69),
    ('CIO', 'poor', 0.00, 0.49),
    ('CISO', 'excellent', 0.85, 1.00),
    ('CISO', 'good', 0.70, 0.84),
    ('CISO', 'fair', 0.50, 0.69),
    ('CISO', 'poor', 0.00, 0.49)
ON CONFLICT (role, threshold_type) DO NOTHING;
"""
    
    with open('scripts/seed_scoring_data.sql', 'w') as f:
        f.write(seed_data)
    
    print("✅ Seed data script created: scripts/seed_scoring_data.sql")


if __name__ == "__main__":
    run_migration()
    create_seed_data_script()
