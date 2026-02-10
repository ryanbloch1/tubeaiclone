import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@/lib/supabase/server';
import { API_BASE } from '@/lib/config';

export async function POST(request: NextRequest) {
  try {
    const supabase = await createClient();

    const { data: { user }, error: authError } = await supabase.auth.getUser();
    if (authError || !user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const body = await request.json();
    const { project_id, image_ids } = body as { project_id?: string; image_ids?: string[] };

    if (!project_id || !Array.isArray(image_ids)) {
      return NextResponse.json(
        { error: 'project_id and image_ids are required' },
        { status: 400 },
      );
    }

    const resp = await fetch(`${API_BASE}/api/images/project-photos/reorder`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${(await supabase.auth.getSession()).data.session?.access_token}`,
      },
      body: JSON.stringify({ project_id, image_ids }),
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
    console.error('Project photos reorder error:', error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Failed to reorder project photos' },
      { status: 500 },
    );
  }
}
