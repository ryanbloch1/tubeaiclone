-- Add 'video' status to projects table
ALTER TABLE projects 
DROP CONSTRAINT IF EXISTS projects_status_check;

ALTER TABLE projects
ADD CONSTRAINT projects_status_check 
CHECK (status IN ('draft', 'script', 'voiceover', 'images', 'video', 'complete'));

-- Videos table
CREATE TABLE videos (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE NOT NULL,
  script_id UUID REFERENCES scripts(id) ON DELETE CASCADE,
  voiceover_id UUID REFERENCES voiceovers(id) ON DELETE SET NULL,
  video_data BYTEA, -- Store video as binary data
  video_url TEXT, -- Optional URL if stored externally
  status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
  error_message TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for faster video lookups by project
CREATE INDEX IF NOT EXISTS videos_project_id_idx ON public.videos (project_id, created_at DESC);

-- Index for status filtering
CREATE INDEX IF NOT EXISTS videos_status_idx ON public.videos (status);

