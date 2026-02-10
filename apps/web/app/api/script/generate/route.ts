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
    const {
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
      modelProvider,
      modelName,
    } = body;

    // For real estate videos, use property address as topic if topic is empty
    const finalTopic = topic?.trim() || propertyAddress?.trim() || 'Property Listing';
    
    if (!finalTopic) {
      return NextResponse.json({ error: 'Topic or property address is required' }, { status: 400 });
    }

    // Ensure project exists via FastAPI project save endpoint (keeps logic in backend)
    const apiBase = API_BASE;
    let projectId = body.projectId;
    const saveResp = await fetch(`${apiBase}/api/projects/save`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${(await supabase.auth.getSession()).data.session?.access_token}`
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
        // Real estate fields
        video_type: videoType,
        property_address: propertyAddress,
        property_type: propertyType,
        property_price: propertyPrice,
        bedrooms,
        bathrooms,
        square_feet: squareFeet,
        mls_number: mlsNumber,
        property_features: propertyFeatures,
        model_provider: modelProvider,
        model_name: modelName,
      })
    });

    const saveText = await saveResp.text();
    if (!saveResp.ok) {
      let detail = saveText;
      try {
        const j = JSON.parse(saveText);
        detail = j.detail || j.error || saveText;
      } catch {
        // ignore
      }
      throw new Error(detail);
    }
    const saveData = JSON.parse(saveText);
    projectId = saveData.project_id || saveData.projectId || projectId;

    // Call FastAPI to generate script
    const fastApiResponse = await fetch(`${apiBase}/api/script/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${(await supabase.auth.getSession()).data.session?.access_token}`
      },
      body: JSON.stringify({
        project_id: projectId,
        topic: finalTopic,
        style_name: style,
        image_count: imageCount,
        mode,
        temperature,
        word_count: wordCount,
        selection: mode === 'script' ? undefined : selection,
        extra_context: extraContext,
        // Real estate fields for script generation
        video_type: videoType,
        property_address: propertyAddress,
        property_type: propertyType,
        property_price: propertyPrice,
        bedrooms: bedrooms,
        bathrooms: bathrooms,
        square_feet: squareFeet,
        mls_number: mlsNumber,
        property_features: propertyFeatures
      })
    });

    if (!fastApiResponse.ok) {
      const errorData = await fastApiResponse.json();
      throw new Error(errorData.detail || 'Failed to generate script');
    }

    const { content, script_id } = await fastApiResponse.json();

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
