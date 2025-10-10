import { createClient } from '@/lib/supabase/client';
import type { Database } from '@/lib/database.types';

type Script = Database['public']['Tables']['scripts']['Row'];
type ScriptInsert = Database['public']['Tables']['scripts']['Insert'];

const supabase = createClient();

export async function createScript(scriptData: Omit<ScriptInsert, 'id' | 'created_at' | 'updated_at'>) {
  const { data, error } = await supabase
    .from('scripts')
    .insert(scriptData)
    .select()
    .single();

  if (error) throw error;
  return data;
}

export async function getScript(scriptId: string) {
  const { data, error } = await supabase
    .from('scripts')
    .select('*')
    .eq('id', scriptId)
    .single();

  if (error) throw error;
  return data;
}

export async function getScriptByProject(projectId: string) {
  const { data, error } = await supabase
    .from('scripts')
    .select('*')
    .eq('project_id', projectId)
    .order('created_at', { ascending: false })
    .limit(1)
    .single();

  if (error && error.code !== 'PGRST116') throw error; // PGRST116 = no rows found
  return data;
}

export async function updateScript(scriptId: string, updates: Partial<ScriptInsert>) {
  const { data, error } = await supabase
    .from('scripts')
    .update(updates)
    .eq('id', scriptId)
    .select()
    .single();

  if (error) throw error;
  return data;
}

export async function deleteScript(scriptId: string) {
  const { error } = await supabase
    .from('scripts')
    .delete()
    .eq('id', scriptId);

  if (error) throw error;
  return true;
}