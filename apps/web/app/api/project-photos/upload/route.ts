import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@/lib/supabase/server';
import { API_BASE } from '@/lib/config';

export async function POST(request: NextRequest) {
  try {
    const supabase = await createClient();

    // Check authentication
    const { data: { user }, error: authError } = await supabase.auth.getUser();
    if (authError || !user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const body = await request.json();
    const { project_id, image_data, image_filename } = body;

    if (!project_id || !image_data) {
      return NextResponse.json(
        { error: 'project_id and image_data are required' },
        { status: 400 },
      );
    }

    const resp = await fetch(`${API_BASE}/api/images/project-photos/upload`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${(await supabase.auth.getSession()).data.session?.access_token}`,
      },
      body: JSON.stringify({
        project_id,
        image_data,
        image_filename,
      }),
    });

    const text = await resp.text();
    if (!resp.ok) {
      let detail = text;
      try {
        const errJson = JSON.parse(text);
        detail = errJson.detail || errJson.error || text;
      } catch {
        // ignore
      }
      return NextResponse.json({ error: detail }, { status: resp.status });
    }

    const data = JSON.parse(text);
    return NextResponse.json(data);
  } catch (error) {
    console.error('Project photo upload error:', error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Failed to upload project photo' },
      { status: 500 },
    );
  }
}

