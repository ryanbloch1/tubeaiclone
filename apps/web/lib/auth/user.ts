/**
 * Authentication utilities for getting current user
 */

import { createClient } from '@/lib/supabase/client'
import { createClient as createServerClient } from '@/lib/supabase/server'

/**
 * Get current user from client-side
 */
export async function getCurrentUser() {
  const supabase = createClient()
  
  const { data: { user }, error } = await supabase.auth.getUser()
  
  if (error) throw error
  return user
}

/**
 * Get current user from server-side
 */
export async function getCurrentUserServer() {
  const supabase = await createServerClient()
  
  const { data: { user }, error } = await supabase.auth.getUser()
  
  if (error) throw error
  return user
}

/**
 * Get current session
 */
export async function getCurrentSession() {
  const supabase = createClient()
  
  const { data: { session }, error } = await supabase.auth.getSession()
  
  if (error) throw error
  return session
}

