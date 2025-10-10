/**
 * Database operations for Voiceovers
 */

import { createClient } from '@/lib/supabase/client'

export type Voiceover = {
  id: string
  script_id: string
  user_id: string
  audio_url?: string
  audio_data_url?: string
  duration?: number
  status: 'pending' | 'generating' | 'completed' | 'error'
  created_at: string
  updated_at: string
}

/**
 * Get voiceover by script ID
 */
export async function getVoiceoverByScript(scriptId: string) {
  const supabase = createClient()
  
  const { data, error } = await supabase
    .from('voiceovers')
    .select('*')
    .eq('script_id', scriptId)
    .order('created_at', { ascending: false })
    .limit(1)
    .maybeSingle()

  if (error) throw error
  return data as Voiceover | null
}

/**
 * Create a voiceover record
 */
export async function createVoiceover(voiceover: {
  script_id: string
  audio_url?: string
  audio_data_url?: string
  duration?: number
  status?: 'pending' | 'generating' | 'completed' | 'error'
}) {
  const supabase = createClient()
  
  const { data, error } = await supabase
    .from('voiceovers')
    .insert([{
      ...voiceover,
      status: voiceover.status || 'pending'
    }])
    .select()
    .single()

  if (error) throw error
  return data as Voiceover
}

/**
 * Update a voiceover
 */
export async function updateVoiceover(id: string, updates: Partial<Voiceover>) {
  const supabase = createClient()
  
  const { data, error } = await supabase
    .from('voiceovers')
    .update(updates)
    .eq('id', id)
    .select()
    .single()

  if (error) throw error
  return data as Voiceover
}

/**
 * Delete a voiceover
 */
export async function deleteVoiceover(id: string) {
  const supabase = createClient()
  
  const { error } = await supabase
    .from('voiceovers')
    .delete()
    .eq('id', id)

  if (error) throw error
}

