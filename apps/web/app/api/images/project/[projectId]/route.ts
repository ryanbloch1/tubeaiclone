import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@/lib/supabase/server';
import { API_BASE } from '@/lib/config';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ projectId: string }> }
) {
  try {
    const { projectId } = await params;
    const supabase = await createClient();
    
    // Check authentication using server-side Supabase client
    const { data: { user }, error: authError } = await supabase.auth.getUser();
    if (authError || !user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }
    
    // Get fresh session token
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) {
      return NextResponse.json({ error: 'No session found' }, { status: 401 });
    }
    
    const auth = `Bearer ${session.access_token}`;
    
    // Forward to FastAPI backend with fresh token
    const resp = await fetch(`${API_BASE}/api/images/project/${projectId}`, {
      headers: { 
        'Authorization': auth,
        'Content-Type': 'application/json'
      },
      cache: 'no-store'
    }).catch((fetchError) => {
      console.error('[IMAGES API] Backend fetch error:', fetchError);
      throw fetchError;
    });
    
    const text = await resp.text();
    let data: unknown;
    try {
      data = JSON.parse(text);
    } catch {
      data = { raw: text, error: text };
    }
    
    return NextResponse.json(data, { status: resp.status });
  } catch (e: unknown) {
    console.error('[IMAGES API] Error fetching images:', e);
    const message = e instanceof Error ? e.message : 'Failed to fetch images';
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
