import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@/lib/supabase/server';

export async function PUT(request: NextRequest) {
  try {
    const supabase = await createClient();
    
    // Check authentication
    const { data: { user }, error: authError } = await supabase.auth.getUser();
    if (authError || !user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const { scriptId, content } = await request.json();

    if (!scriptId || !content) {
      return NextResponse.json({ error: 'Script ID and content required' }, { status: 400 });
    }

    // Update script
    const { error } = await supabase
      .from('scripts')
      .update({ edited_script: content })
      .eq('id', scriptId);

    if (error) {
      console.error('Error updating script:', error);
      return NextResponse.json({ error: 'Failed to update script' }, { status: 500 });
    }

    return NextResponse.json({ success: true });

  } catch (error) {
    console.error('Script update API error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
