-- Remove CASCADE constraints from profile_companies table
-- All deletion logic should be handled in application code for better debugging visibility

-- Drop existing foreign key constraints
ALTER TABLE profile_companies 
DROP CONSTRAINT IF EXISTS profile_companies_profile_id_fkey;

ALTER TABLE profile_companies 
DROP CONSTRAINT IF EXISTS profile_companies_company_id_fkey;

-- Re-add foreign key constraints WITHOUT CASCADE
ALTER TABLE profile_companies 
ADD CONSTRAINT profile_companies_profile_id_fkey 
FOREIGN KEY (profile_id) REFERENCES linkedin_profiles(id);

ALTER TABLE profile_companies 
ADD CONSTRAINT profile_companies_company_id_fkey 
FOREIGN KEY (company_id) REFERENCES companies(id);

-- Note: Deletion of profile-company relationships is now handled 
-- explicitly in application code via the delete_profile method
