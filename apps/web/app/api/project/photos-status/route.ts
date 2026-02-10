import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@/lib/supabase/server';
import { API_BASE } from '@/lib/config';

export async function GET(request: NextRequest) {
  try {
    const supabase = await createClient();
    const { searchParams } = new URL(request.url);
    const projectId = searchParams.get('projectId');

    if (!projectId) {
      return NextResponse.json({ error: 'projectId is required' }, { status: 400 });
    }

    const { data: { user }, error: authError } = await supabase.auth.getUser();
    if (authError || !user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const resp = await fetch(`${API_BASE}/api/projects/${projectId}/photos-status`, {
      headers: {
        'Authorization': `Bearer ${(await supabase.auth.getSession()).data.session?.access_token}`,
      },
      cache: 'no-store',
    });

    const text = await resp.text();
    let data: unknown;
    try {
      data = JSON.parse(text);
    } catch {
      data = { raw: text, error: text };
    }

    return NextResponse.json(data, { status: resp.status });
  } catch (error) {
    console.error('Photos status error:', error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Failed to fetch photos status' },
      { status: 500 },
    );
  }
}
