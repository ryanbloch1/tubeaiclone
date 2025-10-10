/**
 * Database operations for Images
 */

import { createClient } from '@/lib/supabase/client'

export type Image = {
  id: string
  scene_id: string
  user_id: string
  prompt: string
  image_url?: string
  image_data?: string
  status: 'pending' | 'generating' | 'completed' | 'error'
  error_message?: string
  created_at: string
  updated_at: string
}

/**
 * Get images by scene ID
 */
export async function getImagesByScene(sceneId: string) {
  const supabase = createClient()
  
  const { data, error } = await supabase
    .from('images')
    .select('*')
    .eq('scene_id', sceneId)

  if (error) throw error
  return data as Image[]
}

/**
 * Get images by script ID (via scenes)
 */
export async function getImagesByScript(scriptId: string) {
  const supabase = createClient()
  
  const { data, error } = await supabase
    .from('images')
    .select(`
      *,
      scenes!inner(script_id)
    `)
    .eq('scenes.script_id', scriptId)

  if (error) throw error
  return data as Image[]
}

/**
 * Create an image record
 */
export async function createImage(image: {
  scene_id: string
  prompt: string
  status?: 'pending' | 'generating' | 'completed' | 'error'
}) {
  const supabase = createClient()
  
  const { data, error } = await supabase
    .from('images')
    .insert([{
      ...image,
      status: image.status || 'pending'
    }])
    .select()
    .single()

  if (error) throw error
  return data as Image
}

/**
 * Update an image
 */
export async function updateImage(id: string, updates: Partial<Image>) {
  const supabase = createClient()
  
  const { data, error } = await supabase
    .from('images')
    .update(updates)
    .eq('id', id)
    .select()
    .single()

  if (error) throw error
  return data as Image
}

/**
 * Delete an image
 */
export async function deleteImage(id: string) {
  const supabase = createClient()
  
  const { error } = await supabase
    .from('images')
    .delete()
    .eq('id', id)

  if (error) throw error
}

