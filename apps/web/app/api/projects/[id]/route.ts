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

    // Verify user owns the project before deletion
    const { data: project, error: projectError } = await supabase
      .from('projects')
      .select('id, title')
      .eq('id', id)
      .eq('user_id', user.id)
      .single();

    if (projectError || !project) {
      return NextResponse.json({ error: 'Project not found' }, { status: 404 });
    }

    // Delete project (CASCADE will handle related data)
    const { error: deleteError } = await supabase
      .from('projects')
      .delete()
      .eq('id', id)
      .eq('user_id', user.id); // Double-check ownership

    if (deleteError) {
      console.error('Delete project error:', deleteError);
      return NextResponse.json({ error: 'Failed to delete project' }, { status: 500 });
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
    const { status } = body;
    const updateData: { status?: string } = {};
    if (status && ['draft', 'script', 'voiceover', 'images', 'complete'].includes(status)) {
      updateData.status = status;
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
