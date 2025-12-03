import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@/lib/supabase/server';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const supabase = await createClient();
    const { id } = await params;
    
    // Check authentication
    const { data: { user }, error: authError } = await supabase.auth.getUser();
    if (authError || !user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    // Get project
    const { data: project, error: projectError } = await supabase
      .from('projects')
      .select('*')
      .eq('id', id)
      .eq('user_id', user.id) // Ensure user owns the project
      .single();

    if (projectError || !project) {
      return NextResponse.json({ error: 'Project not found' }, { status: 404 });
    }

    // Get associated script
    const { data: script } = await supabase
      .from('scripts')
      .select('*')
      .eq('project_id', id)
      .order('created_at', { ascending: false })
      .limit(1)
      .single();

    return NextResponse.json({
      project,
      script: script || null
    });

  } catch (error) {
    console.error('Project API error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const supabase = await createClient();
    const { id } = await params;
    
    // Check authentication
    const { data: { user }, error: authError } = await supabase.auth.getUser();
    if (authError || !user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    // Verify user owns the project before deletion (for user‑friendly 404)
    const { data: project, error: projectError } = await supabase
      .from('projects')
      .select('id, title')
      .eq('id', id)
      .eq('user_id', user.id)
      .single();

    if (projectError || !project) {
      return NextResponse.json({ error: 'Project not found' }, { status: 404 });
    }

    // 1) Find scripts for this project (to clean up scenes safely)
    const { data: scripts, error: scriptsSelectError } = await supabase
      .from('scripts')
      .select('id')
      .eq('project_id', id);

    if (scriptsSelectError) {
      console.error('Delete project - fetch scripts error:', scriptsSelectError);
      return NextResponse.json(
        { error: 'Failed to delete project', detail: 'Could not load scripts for project' },
        { status: 500 },
      );
    }

    const scriptIds = (scripts || []).map((s: { id: string }) => s.id);

    // 2) Delete scenes in batches by script_id (in case ON DELETE CASCADE is not set)
    const SCENE_BATCH_SIZE = 100;
    for (let i = 0; i < scriptIds.length; i += SCENE_BATCH_SIZE) {
      const batch = scriptIds.slice(i, i + SCENE_BATCH_SIZE);
      const { error: scenesDeleteError } = await supabase
        .from('scenes')
        .delete()
        .in('script_id', batch);

      if (scenesDeleteError) {
        console.error('Delete project - delete scenes error:', scenesDeleteError);
        return NextResponse.json(
          { error: 'Failed to delete project', detail: 'Could not delete scenes for project' },
          { status: 500 },
        );
      }
    }

    // 3) Delete images in ID batches to avoid long-running statements / timeouts
    const IMAGE_BATCH_SIZE = 500;
    // Loop until no more images remain for this project
    // eslint-disable-next-line no-constant-condition
    while (true) {
      const { data: imagesPage, error: imagesSelectError } = await supabase
        .from('images')
        .select('id')
        .eq('project_id', id)
        .limit(IMAGE_BATCH_SIZE);

      if (imagesSelectError) {
        console.error('Delete project - fetch images error:', imagesSelectError);
        return NextResponse.json(
          { error: 'Failed to delete project', detail: 'Could not load images for project' },
          { status: 500 },
        );
      }

      if (!imagesPage || imagesPage.length === 0) {
        break;
      }

      const imageIds = imagesPage.map((img: { id: string }) => img.id);

      const { error: imagesDeleteError } = await supabase
        .from('images')
        .delete()
        .in('id', imageIds);

      if (imagesDeleteError) {
        console.error('Delete project - delete images error:', imagesDeleteError);
        return NextResponse.json(
          { error: 'Failed to delete project', detail: 'Could not delete images for project' },
          { status: 500 },
        );
      }
    }

    // 4) Delete scripts for this project (scenes already removed above)
    const { error: scriptsDeleteError } = await supabase
      .from('scripts')
      .delete()
      .eq('project_id', id);

    if (scriptsDeleteError) {
      console.error('Delete project - delete scripts error:', scriptsDeleteError);
      return NextResponse.json(
        { error: 'Failed to delete project', detail: 'Could not delete scripts for project' },
        { status: 500 },
      );
    }

    // 5) Finally delete the project itself
    const { error: deleteError } = await supabase
      .from('projects')
      .delete()
      .eq('id', id)
      .eq('user_id', user.id);

    if (deleteError) {
      console.error('Delete project error:', deleteError);
      return NextResponse.json({ 
        error: 'Failed to delete project',
        detail: deleteError.message 
      }, { status: 500 });
    }

    return NextResponse.json({ 
      success: true, 
      message: `Project "${project.title}" deleted successfully` 
    });

  } catch (error) {
    console.error('Delete project API error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const supabase = await createClient();
    const { id } = await params;
    const body = await request.json();

    // Check authentication
    const { data: { user }, error: authError } = await supabase.auth.getUser();
    if (authError || !user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    // Validate incoming data (e.g., only allow updating specific fields)
    const { status, style } = body;
    const updateData: { status?: string; style?: string | null } = {};
    if (status && ['draft', 'script', 'voiceover', 'images', 'complete'].includes(status)) {
      updateData.status = status;
    }
    if (typeof style === 'string') {
      updateData.style = style.trim() || null;
    }

    if (Object.keys(updateData).length === 0) {
      return NextResponse.json({ error: 'No valid fields to update' }, { status: 400 });
    }

    // Update the project, RLS ensures the user owns it.
    const { data, error: updateError } = await supabase
      .from('projects')
      .update(updateData)
      .eq('id', id)
      .eq('user_id', user.id)
      .select()
      .single();

    if (updateError) {
      console.error('Update project error:', updateError);
      if (updateError.code === 'PGRST116') { // PostgREST error for no rows found
        return NextResponse.json({ error: 'Project not found or access denied' }, { status: 404 });
      }
      return NextResponse.json({ error: 'Failed to update project' }, { status: 500 });
    }

    return NextResponse.json({ success: true, project: data });

  } catch (error) {
    console.error('Update project API error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
