-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table (extends Supabase auth.users)
CREATE TABLE profiles (
  id UUID REFERENCES auth.users(id) PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  full_name TEXT,
  avatar_url TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Projects table
CREATE TABLE projects (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  user_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  description TEXT,
  status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'script', 'voiceover', 'images', 'complete')),
  -- Script generation settings (from ScriptState)
  topic TEXT,
  style TEXT,
  mode TEXT DEFAULT 'script' CHECK (mode IN ('script', 'outline', 'rewrite')),
  temperature DECIMAL(3,2) DEFAULT 0.7 CHECK (temperature >= 0 AND temperature <= 1),
  word_count INTEGER DEFAULT 500,
  image_count INTEGER DEFAULT 10,
  video_length TEXT DEFAULT '1:00',
  selection TEXT,
  extra_context TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Scripts table
CREATE TABLE scripts (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  raw_script TEXT NOT NULL,
  edited_script TEXT,
  sanitized_script TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Scenes table
CREATE TABLE scenes (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  script_id UUID REFERENCES scripts(id) ON DELETE CASCADE,
  scene_number INTEGER NOT NULL,
  description TEXT NOT NULL,
  duration_estimate INTEGER, -- in seconds
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Scene prompts table
CREATE TABLE scene_prompts (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  scene_id UUID REFERENCES scenes(id) ON DELETE CASCADE,
  prompt_text TEXT NOT NULL,
  status TEXT DEFAULT 'loading' CHECK (status IN ('loading', 'ready', 'error')),
  generated_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Images table
CREATE TABLE images (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  scene_id UUID REFERENCES scenes(id) ON DELETE CASCADE,
  prompt_text TEXT NOT NULL,
  image_url TEXT, -- URL to stored image (optional for base64 storage)
  image_data TEXT, -- Base64 encoded image data (for localStorage compatibility)
  status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'generating', 'completed', 'failed')),
  error_message TEXT,
  generated_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Voiceovers table
CREATE TABLE voiceovers (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  script_id UUID REFERENCES scripts(id) ON DELETE CASCADE,
  audio_url TEXT, -- URL to stored audio file
  audio_data_url TEXT, -- Base64 encoded audio data (for localStorage compatibility)
  status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'generating', 'complete', 'error')),
  generated_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Job queue table for background processing
CREATE TABLE job_queue (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  job_type TEXT NOT NULL CHECK (job_type IN ('voiceover', 'image', 'prompt')),
  entity_id UUID NOT NULL, -- ID of the related entity
  status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'complete', 'failed')),
  payload JSONB, -- Additional data needed for the job
  error_message TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  started_at TIMESTAMP WITH TIME ZONE,
  completed_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for performance
CREATE INDEX idx_projects_user_id ON projects(user_id);
CREATE INDEX idx_scripts_project_id ON scripts(project_id);
CREATE INDEX idx_scenes_script_id ON scenes(script_id);
CREATE INDEX idx_scene_prompts_scene_id ON scene_prompts(scene_id);
CREATE INDEX idx_images_scene_id ON images(scene_id);
CREATE INDEX idx_voiceovers_script_id ON voiceovers(script_id);
CREATE INDEX idx_job_queue_status ON job_queue(status);
CREATE INDEX idx_job_queue_type ON job_queue(job_type);

-- Row Level Security (RLS) policies
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE scripts ENABLE ROW LEVEL SECURITY;
ALTER TABLE scenes ENABLE ROW LEVEL SECURITY;
ALTER TABLE scene_prompts ENABLE ROW LEVEL SECURITY;
ALTER TABLE images ENABLE ROW LEVEL SECURITY;
ALTER TABLE voiceovers ENABLE ROW LEVEL SECURITY;
ALTER TABLE job_queue ENABLE ROW LEVEL SECURITY;

-- RLS Policies - Users can only access their own data
CREATE POLICY "Users can view own profile" ON profiles FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can update own profile" ON profiles FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Users can view own projects" ON projects FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own projects" ON projects FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own projects" ON projects FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own projects" ON projects FOR DELETE USING (auth.uid() = user_id);

CREATE POLICY "Users can view own scripts" ON scripts FOR SELECT USING (
  EXISTS (SELECT 1 FROM projects WHERE projects.id = scripts.project_id AND projects.user_id = auth.uid())
);
CREATE POLICY "Users can insert own scripts" ON scripts FOR INSERT WITH CHECK (
  EXISTS (SELECT 1 FROM projects WHERE projects.id = scripts.project_id AND projects.user_id = auth.uid())
);
CREATE POLICY "Users can update own scripts" ON scripts FOR UPDATE USING (
  EXISTS (SELECT 1 FROM projects WHERE projects.id = scripts.project_id AND projects.user_id = auth.uid())
);

-- Similar policies for other tables...
CREATE POLICY "Users can view own scenes" ON scenes FOR SELECT USING (
  EXISTS (SELECT 1 FROM scripts s JOIN projects p ON s.project_id = p.id WHERE s.id = scenes.script_id AND p.user_id = auth.uid())
);
CREATE POLICY "Users can insert own scenes" ON scenes FOR INSERT WITH CHECK (
  EXISTS (SELECT 1 FROM scripts s JOIN projects p ON s.project_id = p.id WHERE s.id = scenes.script_id AND p.user_id = auth.uid())
);
CREATE POLICY "Users can update own scenes" ON scenes FOR UPDATE USING (
  EXISTS (SELECT 1 FROM scripts s JOIN projects p ON s.project_id = p.id WHERE s.id = scenes.script_id AND p.user_id = auth.uid())
);

CREATE POLICY "Users can view own scene_prompts" ON scene_prompts FOR SELECT USING (
  EXISTS (SELECT 1 FROM scenes s JOIN scripts sc ON s.script_id = sc.id JOIN projects p ON sc.project_id = p.id WHERE s.id = scene_prompts.scene_id AND p.user_id = auth.uid())
);
CREATE POLICY "Users can insert own scene_prompts" ON scene_prompts FOR INSERT WITH CHECK (
  EXISTS (SELECT 1 FROM scenes s JOIN scripts sc ON s.script_id = sc.id JOIN projects p ON sc.project_id = p.id WHERE s.id = scene_prompts.scene_id AND p.user_id = auth.uid())
);
CREATE POLICY "Users can update own scene_prompts" ON scene_prompts FOR UPDATE USING (
  EXISTS (SELECT 1 FROM scenes s JOIN scripts sc ON s.script_id = sc.id JOIN projects p ON sc.project_id = p.id WHERE s.id = scene_prompts.scene_id AND p.user_id = auth.uid())
);

CREATE POLICY "Users can view own images" ON images FOR SELECT USING (
  EXISTS (SELECT 1 FROM scenes s JOIN scripts sc ON s.script_id = sc.id JOIN projects p ON sc.project_id = p.id WHERE s.id = images.scene_id AND p.user_id = auth.uid())
);
CREATE POLICY "Users can insert own images" ON images FOR INSERT WITH CHECK (
  EXISTS (SELECT 1 FROM scenes s JOIN scripts sc ON s.script_id = sc.id JOIN projects p ON sc.project_id = p.id WHERE s.id = images.scene_id AND p.user_id = auth.uid())
);
CREATE POLICY "Users can update own images" ON images FOR UPDATE USING (
  EXISTS (SELECT 1 FROM scenes s JOIN scripts sc ON s.script_id = sc.id JOIN projects p ON sc.project_id = p.id WHERE s.id = images.scene_id AND p.user_id = auth.uid())
);

CREATE POLICY "Users can view own voiceovers" ON voiceovers FOR SELECT USING (
  EXISTS (SELECT 1 FROM scripts s JOIN projects p ON s.project_id = p.id WHERE s.id = voiceovers.script_id AND p.user_id = auth.uid())
);
CREATE POLICY "Users can insert own voiceovers" ON voiceovers FOR INSERT WITH CHECK (
  EXISTS (SELECT 1 FROM scripts s JOIN projects p ON s.project_id = p.id WHERE s.id = voiceovers.script_id AND p.user_id = auth.uid())
);
CREATE POLICY "Users can update own voiceovers" ON voiceovers FOR UPDATE USING (
  EXISTS (SELECT 1 FROM scripts s JOIN projects p ON s.project_id = p.id WHERE s.id = voiceovers.script_id AND p.user_id = auth.uid())
);

-- Job queue policies (for background processing)
CREATE POLICY "Users can view own jobs" ON job_queue FOR SELECT USING (
  EXISTS (SELECT 1 FROM projects p WHERE p.id = (job_queue.payload->>'project_id')::UUID AND p.user_id = auth.uid())
);
CREATE POLICY "Users can insert own jobs" ON job_queue FOR INSERT WITH CHECK (
  EXISTS (SELECT 1 FROM projects p WHERE p.id = (job_queue.payload->>'project_id')::UUID AND p.user_id = auth.uid())
);

-- Functions for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_profiles_updated_at BEFORE UPDATE ON profiles FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_scripts_updated_at BEFORE UPDATE ON scripts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
