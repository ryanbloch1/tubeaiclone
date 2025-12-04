-- WARNING: This script will delete ALL projects and all related data!
-- This is irreversible. Make sure you have a backup if needed.
-- 
-- This script deletes:
-- - All images with project_id
-- - All projects (which cascades to: scripts, scenes, scene_prompts, voiceovers, videos, real_estate_metadata)
-- - Job queue entries related to projects (optional cleanup)

BEGIN;

-- Step 1: Delete all images that are directly linked to projects
-- (images.project_id doesn't have ON DELETE CASCADE, so we delete manually)
DELETE FROM images
WHERE project_id IS NOT NULL;

-- Step 2: (Optional) Clean up job_queue entries that reference projects
-- This is optional since job_queue doesn't have a foreign key constraint
DELETE FROM job_queue
WHERE payload->>'project_id' IS NOT NULL
  AND EXISTS (
    SELECT 1 FROM projects 
    WHERE id = (payload->>'project_id')::UUID
  );

-- Step 3: Delete all projects
-- This will cascade to:
--   - scripts (ON DELETE CASCADE)
--   - videos (ON DELETE CASCADE)
--   - real_estate_metadata (ON DELETE CASCADE)
-- And scripts deletion will cascade to:
--   - scenes (ON DELETE CASCADE)
--   - voiceovers (ON DELETE CASCADE)
-- And scenes deletion will cascade to:
--   - scene_prompts (ON DELETE CASCADE)
--   - images (via scene_id, ON DELETE CASCADE)

DELETE FROM projects;

-- Verify deletion
SELECT 
  (SELECT COUNT(*) FROM projects) as remaining_projects,
  (SELECT COUNT(*) FROM scripts) as remaining_scripts,
  (SELECT COUNT(*) FROM scenes) as remaining_scenes,
  (SELECT COUNT(*) FROM images) as remaining_images,
  (SELECT COUNT(*) FROM voiceovers) as remaining_voiceovers,
  (SELECT COUNT(*) FROM videos) as remaining_videos;

COMMIT;



