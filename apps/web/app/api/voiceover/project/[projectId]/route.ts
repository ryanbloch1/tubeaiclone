import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@/lib/supabase/server';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ projectId: string }> }
) {
  try {
    const supabase = await createClient();
    const { projectId } = await params;
    
    // Check authentication
    const { data: { user }, error: authError } = await supabase.auth.getUser();
    if (authError || !user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    // Call FastAPI to get voiceovers for this project
    const apiBase = process.env.NEXT_PUBLIC_API_BASE || 'http://127.0.0.1:8000';
    const resp = await fetch(`${apiBase}/api/voiceover/project/${projectId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${(await supabase.auth.getSession()).data.session?.access_token}`,
      },
    });

    if (!resp.ok) {
      const errorData = await resp.json().catch(() => ({ detail: 'Failed to fetch voiceovers' }));
      return NextResponse.json({ error: errorData.detail || 'Failed to fetch voiceovers' }, { status: resp.status });
    }

    const data = await resp.json();
    return NextResponse.json(data);

  } catch (error) {
    console.error('Voiceovers API error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}


