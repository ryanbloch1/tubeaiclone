-- Create videos table if it doesn't exist, or alter video_data column from BYTEA to TEXT
-- This avoids serialization issues with Supabase Python client when handling binary data

-- First, ensure the 'video' status exists in projects table
ALTER TABLE projects 
DROP CONSTRAINT IF EXISTS projects_status_check;

ALTER TABLE projects
ADD CONSTRAINT projects_status_check 
CHECK (status IN ('draft', 'script', 'voiceover', 'images', 'video', 'complete'));

-- Create videos table if it doesn't exist (with TEXT column from the start)
CREATE TABLE IF NOT EXISTS videos (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE NOT NULL,
  script_id UUID REFERENCES scripts(id) ON DELETE CASCADE,
  voiceover_id UUID REFERENCES voiceovers(id) ON DELETE SET NULL,
  video_data TEXT, -- Store video as base64-encoded text (to avoid BYTEA serialization issues)
  video_url TEXT, -- Optional URL if stored externally
  status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
  error_message TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- If table already exists with BYTEA column, convert it to TEXT
DO $$
BEGIN
  -- Check if video_data column exists and is BYTEA type
  IF EXISTS (
    SELECT 1 
    FROM information_schema.columns 
    WHERE table_name = 'videos' 
    AND column_name = 'video_data' 
    AND data_type = 'bytea'
  ) THEN
    -- Convert existing BYTEA data to base64 text
    ALTER TABLE videos 
    ALTER COLUMN video_data TYPE TEXT USING 
      CASE 
        WHEN video_data IS NULL THEN NULL
        ELSE encode(video_data, 'base64')
      END;
  END IF;
END $$;

-- Create indexes if they don't exist
CREATE INDEX IF NOT EXISTS videos_project_id_idx ON public.videos (project_id, created_at DESC);
CREATE INDEX IF NOT EXISTS videos_status_idx ON public.videos (status);

-- Add a comment explaining the format
COMMENT ON COLUMN videos.video_data IS 'Video data stored as base64-encoded text (to avoid BYTEA serialization issues with Supabase Python client)';

