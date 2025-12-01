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
      projectId,
      topic,
      style,
      mode = 'script',
      temperature = 0.7,
      wordCount = 500,
      imageCount = 10,
      videoLength = '1:00',
      selection,
      extraContext,
      // Real estate fields
      videoType,
      propertyAddress,
      propertyType,
      propertyPrice,
      bedrooms,
      bathrooms,
      squareFeet,
      mlsNumber,
      propertyFeatures,
    } = body;

    const finalTopic = (topic?.trim() || propertyAddress?.trim() || 'Property Listing');
    if (!finalTopic) {
      return NextResponse.json({ error: 'Topic or property address is required' }, { status: 400 });
    }

    const apiBase = process.env.NEXT_PUBLIC_API_BASE || 'http://127.0.0.1:8000';

    const fastApiResponse = await fetch(`${apiBase}/api/projects/save`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${(await supabase.auth.getSession()).data.session?.access_token}`,
      },
      body: JSON.stringify({
        project_id: projectId,
        title: finalTopic,
        topic: finalTopic,
        style_name: style,
        mode,
        temperature,
        word_count: wordCount,
        image_count: imageCount,
        video_length: videoLength,
        selection,
        extra_context: extraContext,
        video_type: videoType,
        property_address: propertyAddress,
        property_type: propertyType,
        property_price: propertyPrice,
        bedrooms,
        bathrooms,
        square_feet: squareFeet,
        mls_number: mlsNumber,
        property_features: propertyFeatures,
      }),
    });

    const text = await fastApiResponse.text();
    if (!fastApiResponse.ok) {
      let detail = text;
      try {
        const errJson = JSON.parse(text);
        detail = errJson.detail || errJson.error || text;
      } catch {
        // ignore
      }
      return NextResponse.json({ error: detail }, { status: fastApiResponse.status });
    }

    const data = JSON.parse(text);
    return NextResponse.json({ success: data.success, projectId: data.project_id });
  } catch (error) {
    console.error('Project save error:', error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Failed to save project' },
      { status: 500 },
    );
  }
}


