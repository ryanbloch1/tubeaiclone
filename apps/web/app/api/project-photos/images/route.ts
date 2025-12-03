import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@/lib/supabase/server';

export async function POST(request: NextRequest) {
  try {
    const supabase = await createClient();
    const { projectId, imageIds } = await request.json();

    if (!projectId || !imageIds || !Array.isArray(imageIds)) {
      return NextResponse.json({ error: 'projectId and imageIds array are required' }, { status: 400 });
    }

    const {
      data: { user },
      error: authError,
    } = await supabase.auth.getUser();
    if (authError || !user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const apiBase = process.env.NEXT_PUBLIC_API_BASE || 'http://127.0.0.1:8000';
    const token = (await supabase.auth.getSession()).data.session?.access_token;

    const resp = await fetch(`${apiBase}/api/images/project-photos/${projectId}/images`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ image_ids: imageIds }),
      cache: 'no-store',
    });

    const text = await resp.text();
    let data: any;
    try {
      data = JSON.parse(text);
    } catch {
      data = { raw: text, error: text };
    }

    return NextResponse.json(data, { status: resp.status });
  } catch (error) {
    console.error('Project photos images batch error:', error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Failed to fetch photo images' },
      { status: 500 },
    );
  }
}


