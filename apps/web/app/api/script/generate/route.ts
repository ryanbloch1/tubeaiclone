import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@/lib/supabase/server';

export async function POST(request: NextRequest) {
  try {
    const supabase = await createClient();
    
    // Check authentication
    const { data: { user }, error: authError } = await supabase.auth.getUser();
    if (authError || !user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const body = await request.json();
    const {
      topic,
      style,
      mode = 'script',
      temperature = 0.7,
      wordCount = 500,
      imageCount = 10,
      videoLength = '1:00',
      selection,
      extraContext
    } = body;

    if (!topic?.trim()) {
      return NextResponse.json({ error: 'Topic is required' }, { status: 400 });
    }

    // Create or update project directly using server supabase client
    let projectId = body.projectId;
    if (!projectId) {
      const { data: project, error: projectError } = await supabase
        .from('projects')
        .insert({
          user_id: user.id,
          title: topic,
          topic,
          style,
          mode,
          temperature,
          word_count: wordCount,
          image_count: imageCount,
          video_length: videoLength,
          selection,
          extra_context: extraContext,
          status: 'script'
        })
        .select()
        .single();
      
      if (projectError) throw projectError;
      projectId = project.id;
    } else {
      const { error: updateError } = await supabase
        .from('projects')
        .update({
          title: topic,
          topic,
          style,
          mode,
          temperature,
          word_count: wordCount,
          image_count: imageCount,
          video_length: videoLength,
          selection,
          extra_context: extraContext,
          status: 'script'
        })
        .eq('id', projectId)
        .eq('user_id', user.id);
      
      if (updateError) throw updateError;
    }

    // Call FastAPI to generate script
    const fastApiResponse = await fetch('http://localhost:8000/api/script/generate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${(await supabase.auth.getSession()).data.session?.access_token}`
      },
      body: JSON.stringify({
        project_id: projectId,
        topic,
        style_name: style,
        image_count: imageCount,
        mode,
        temperature,
        word_count: wordCount,
        selection: mode === 'script' ? undefined : selection,
        extra_context: extraContext
      })
    });

    if (!fastApiResponse.ok) {
      const errorData = await fastApiResponse.json();
      throw new Error(errorData.detail || 'Failed to generate script');
    }

    const { content, script_id } = await fastApiResponse.json();

    // Update project current_step to 'script' after successful generation
    const { error: updateStepError } = await supabase
      .from('projects')
      .update({ current_step: 'script' })
      .eq('id', projectId)
      .eq('user_id', user.id);

    if (updateStepError) {
      console.error('Failed to update project current_step:', updateStepError);
    }

    return NextResponse.json({
      script: content,
      scriptId: script_id,
      projectId,
      success: true
    });

  } catch (error) {
    console.error('Script generation error:', error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Failed to generate script' },
      { status: 500 }
    );
  }
}
