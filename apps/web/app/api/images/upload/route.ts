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
    const { project_id, scene_number, image_data, image_filename } = body;

    if (!project_id || !scene_number || !image_data) {
      return NextResponse.json(
        { error: 'project_id, scene_number, and image_data are required' },
        { status: 400 }
      );
    }

    // Call FastAPI upload endpoint
    const resp = await fetch(`${API_BASE}/api/images/upload`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${(await supabase.auth.getSession()).data.session?.access_token}`,
      },
      body: JSON.stringify({
        project_id,
        scene_number,
        image_data,
        image_filename,
      }),
    });

    if (!resp.ok) {
      const errorText = await resp.text().catch(() => '');
      return NextResponse.json(
        { error: `Upload failed: ${resp.status} ${errorText}` },
        { status: resp.status }
      );
    }

    const data = await resp.json();
    return NextResponse.json(data);

  } catch (error) {
    console.error('Image upload error:', error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Failed to upload image' },
      { status: 500 }
    );
  }
}


