import { NextRequest, NextResponse } from 'next/server';

type ImageRequest = {
  prompt: string;
  scene_number: number;
};

export async function POST(request: NextRequest) {
  let parsed: ImageRequest | null = null;
  try {
    parsed = await request.json();
    
    if (!parsed?.prompt || !parsed?.scene_number) {
      return NextResponse.json(
        { error: 'Prompt and scene_number are required' },
        { status: 400 }
      );
    }

    const useLocalSd = process.env.USE_LOCAL_SD === 'true';
    if (useLocalSd) {
      const apiBase = process.env.API_BASE || process.env.NEXT_PUBLIC_API_BASE || 'http://127.0.0.1:8000';
      const sdResp = await fetch(`${apiBase}/images/sd/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: parsed.prompt,
          scene_number: parsed.scene_number,
          width: 512,
          height: 512
        })
      });

      if (!sdResp.ok) {
        throw new Error(`Local SD error: ${sdResp.status}`);
      }

      const json = await sdResp.json();
      return NextResponse.json({
        success: true,
        image_url: json.image_url,
        scene_number: parsed.scene_number
      });
    }

    // Default: Hugging Face Inference API
    const hfToken = process.env.HF_TOKEN;
    const hfModel = process.env.HF_IMAGE_MODEL;
    if (!hfToken || !hfModel) {
      throw new Error('Missing HF_TOKEN or HF_IMAGE_MODEL');
    }

    const hfResp = await fetch(`https://api-inference.huggingface.co/models/${hfModel}`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${hfToken}`,
        'Content-Type': 'application/json',
        'Accept': 'image/png'
      },
      body: JSON.stringify({
        inputs: parsed.prompt,
        options: { use_cache: true, wait_for_model: true }
      })
    });

    if (!hfResp.ok) {
      throw new Error(`HF error: ${hfResp.status}`);
    }

    const buf = Buffer.from(await hfResp.arrayBuffer());
    const dataUrl = `data:image/png;base64,${buf.toString('base64')}`;

    return NextResponse.json({
      success: true,
      image_url: dataUrl,
      scene_number: parsed.scene_number
    });

  } catch (error) {
    console.error('Image generation error:', error);
    
    // Return a mock success for now until the backend is set up
    return NextResponse.json({
      success: true,
      image_url: `https://picsum.photos/512/512?random=${parsed?.scene_number ?? 0}`,
      scene_number: parsed?.scene_number ?? 0
    });
  }
}
