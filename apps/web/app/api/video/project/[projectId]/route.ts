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

    // Get video for project
    const { data: video, error: videoError } = await supabase
      .from('videos')
      .select('*')
      .eq('project_id', projectId)
      .order('created_at', { ascending: false })
      .limit(1)
      .single();

    if (videoError && videoError.code !== 'PGRST116') {
      return NextResponse.json({ error: 'Failed to fetch video' }, { status: 500 });
    }

    // Convert video_data to data_url if exists
    let video_data_url = null;
    if (video?.video_data) {
      const base64 = Buffer.from(video.video_data).toString('base64');
      video_data_url = `data:video/mp4;base64,${base64}`;
    }

    return NextResponse.json({
      video: video ? {
        ...video,
        video_data_url,
        video_data: undefined // Remove binary data from response
      } : null
    });

  } catch (error) {
    console.error('Video API error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}

