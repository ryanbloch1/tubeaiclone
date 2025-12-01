import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { text, voice = 'professional' } = body;

    if (!text || typeof text !== 'string' || text.trim().length === 0) {
      return NextResponse.json(
        { error: 'Text is required and must be a non-empty string' },
        { status: 400 }
      );
    }

    // Map voice styles to Hugging Face TTS models
    const voiceModelMap: Record<string, string> = {
      professional: 'microsoft/speecht5_tts',
      friendly: 'suno/bark-small',
      authoritative: 'microsoft/speecht5_tts',
    };

    const modelId = voiceModelMap[voice] || voiceModelMap.professional;

    // Use Hugging Face Inference API
    const hfApiKey = process.env.HUGGINGFACE_API_KEY;
    if (!hfApiKey || hfApiKey === 'your_api_key_here') {
      return NextResponse.json(
        { error: 'Hugging Face API key not configured' },
        { status: 500 }
      );
    }

    // Call Hugging Face Inference API
    const hfResponse = await fetch(
      `https://api-inference.huggingface.co/models/${modelId}`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${hfApiKey}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          inputs: text,
        }),
      }
    );

    if (!hfResponse.ok) {
      const errorText = await hfResponse.text();
      console.error('Hugging Face API error:', errorText);
      return NextResponse.json(
        { error: `Hugging Face API error: ${hfResponse.status}` },
        { status: 500 }
      );
    }

    // Get audio as ArrayBuffer
    const audioBuffer = await hfResponse.arrayBuffer();
    
    // Convert to base64
    const audioBase64 = Buffer.from(audioBuffer).toString('base64');
    const audioDataUrl = `data:audio/wav;base64,${audioBase64}`;

    return NextResponse.json({
      success: true,
      audio_data_url: audioDataUrl,
      model: modelId,
      voice_style: voice,
    });

  } catch (error) {
    console.error('Hugging Face TTS error:', error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Failed to generate voiceover' },
      { status: 500 }
    );
  }
}



