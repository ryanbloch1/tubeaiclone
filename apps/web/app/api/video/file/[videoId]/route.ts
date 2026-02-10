import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@/lib/supabase/server';
import { API_BASE } from '@/lib/config';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ videoId: string }> }
) {
  try {
    const supabase = await createClient();
    const { videoId } = await params;
    
    // Check authentication
    const { data: { user }, error: authError } = await supabase.auth.getUser();
    if (authError || !user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    // Get video to verify ownership
    const { data: video, error: videoError } = await supabase
      .from('videos')
      .select('project_id')
      .eq('id', videoId)
      .single();

    if (videoError || !video) {
      return NextResponse.json({ error: 'Video not found' }, { status: 404 });
    }

    // Verify project ownership
    const { data: project } = await supabase
      .from('projects')
      .select('id')
      .eq('id', video.project_id)
      .eq('user_id', user.id)
      .single();

    if (!project) {
      return NextResponse.json({ error: 'Access denied' }, { status: 403 });
    }

    // Proxy request to FastAPI backend
    const backendUrl = `${API_BASE}/api/video/file/${videoId}`;
    
    const session = await supabase.auth.getSession();
    const resp = await fetch(backendUrl, {
      headers: {
        'Authorization': `Bearer ${session.data.session?.access_token}`,
      },
    });

    if (!resp.ok) {
      return NextResponse.json(
        { error: 'Failed to fetch video' },
        { status: resp.status }
      );
    }

    // Stream the video file
    const videoBlob = await resp.blob();
    return new NextResponse(videoBlob, {
      headers: {
        'Content-Type': 'video/mp4',
        'Content-Disposition': `attachment; filename="video-${videoId}.mp4"`,
      },
    });

  } catch (error) {
    console.error('Video file API error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
