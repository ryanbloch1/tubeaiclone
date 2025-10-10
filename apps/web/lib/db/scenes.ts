/**
 * Database operations for Scenes
 */

import { createClient } from '@/lib/supabase/client'

export type Scene = {
  id: string
  script_id: string
  user_id: string
  scene_number: number
  text: string
  created_at: string
}

/**
 * Get scenes by script ID
 */
export async function getScenesByScript(scriptId: string) {
  const supabase = createClient()
  
  const { data, error } = await supabase
    .from('scenes')
    .select('*')
    .eq('script_id', scriptId)
    .order('scene_number', { ascending: true })

  if (error) throw error
  return data as Scene[]
}

/**
 * Create scenes in bulk
 */
export async function createScenes(scenes: Omit<Scene, 'id' | 'created_at'>[]) {
  const supabase = createClient()
  
  const { data, error } = await supabase
    .from('scenes')
    .insert(scenes)
    .select()

  if (error) throw error
  return data as Scene[]
}

/**
 * Update a scene
 */
export async function updateScene(id: string, updates: Partial<Scene>) {
  const supabase = createClient()
  
  const { data, error } = await supabase
    .from('scenes')
    .update(updates)
    .eq('id', id)
    .select()
    .single()

  if (error) throw error
  return data as Scene
}

/**
 * Delete scenes by script ID
 */
export async function deleteScenesByScript(scriptId: string) {
  const supabase = createClient()
  
  const { error } = await supabase
    .from('scenes')
    .delete()
    .eq('script_id', scriptId)

  if (error) throw error
}

