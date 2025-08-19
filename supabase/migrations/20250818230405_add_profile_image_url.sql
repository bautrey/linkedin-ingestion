-- Add profile_image_url column to linkedin_profiles table
-- This column will store the URL to LinkedIn profile pictures

ALTER TABLE "public"."linkedin_profiles" 
ADD COLUMN "profile_image_url" TEXT;

-- Add comment for documentation
COMMENT ON COLUMN "public"."linkedin_profiles"."profile_image_url" 
IS 'URL to the LinkedIn profile picture image';

-- Create index for potential filtering by profiles with/without images
CREATE INDEX "idx_linkedin_profiles_profile_image_url" 
ON "public"."linkedin_profiles" ("profile_image_url") 
WHERE "profile_image_url" IS NOT NULL;
