-- Add indexes to speed up fetching scripts and voiceovers
CREATE INDEX IF NOT EXISTS scripts_project_id_created_at_idx ON public.scripts (project_id, created_at DESC);
CREATE INDEX IF NOT EXISTS voiceovers_script_id_created_at_idx ON public.voiceovers (script_id, created_at DESC);
