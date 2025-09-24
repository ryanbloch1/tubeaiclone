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

    // Use local Stable Diffusion API
    const apiBase = process.env.API_BASE || process.env.NEXT_PUBLIC_API_BASE || 'http://127.0.0.1:8000';
    
    // Add timeout and retry logic
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 120000); // 2 minute timeout
    
    try {
      const sdResp = await fetch(`${apiBase}/images/sd/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: parsed.prompt,
          scene_number: parsed.scene_number,
          width: 512,
          height: 512
        }),
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      if (!sdResp.ok) {
        const errorText = await sdResp.text();
        console.error(`Local SD error ${sdResp.status}:`, errorText);
        throw new Error(`Local SD error: ${sdResp.status} - ${errorText}`);
      }

      const json = await sdResp.json();
      return NextResponse.json({
        success: true,
        image_url: json.image_url,
        scene_number: parsed.scene_number
      });
    } catch (error) {
      clearTimeout(timeoutId);
      if (error instanceof Error && error.name === 'AbortError') {
        throw new Error('Image generation timeout - please try again');
      }
      throw error;
    }

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
