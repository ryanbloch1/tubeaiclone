import type { NextRequest } from 'next/server';

export const runtime = 'nodejs';

export async function POST(request: NextRequest) {
  try {
    const { script, filename, voice_id, model_id, format }: { script?: string; filename?: string; voice_id?: string; model_id?: string; format?: 'wav' | 'mp3' } = await request.json();
    if (!script || !script.trim()) {
      return new Response(JSON.stringify({ error: 'script is required' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    const elevenKey = process.env.ELEVENLABS_API_KEY;
    const hfToken = process.env.HF_TOKEN;

    // Prefer ElevenLabs if configured
    if (elevenKey) {
      const voiceId = voice_id || process.env.ELEVENLABS_VOICE_ID || '21m00Tcm4TlvDq8ikWAM'; // common public demo voice
      const modelId = model_id || process.env.ELEVENLABS_MODEL_ID || 'eleven_turbo_v2';
      const outFmt = (format || process.env.ELEVENLABS_OUTPUT || 'wav').toLowerCase();
      const accept = outFmt === 'mp3' ? 'audio/mpeg' : 'audio/wav';

      const resp = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${voiceId}`, {
        method: 'POST',
        headers: {
          'xi-api-key': elevenKey,
          'Content-Type': 'application/json',
          'Accept': accept,
        },
        body: JSON.stringify({
          text: script,
          model_id: modelId,
          // Optional defaults; safe values
          voice_settings: { stability: 0.5, similarity_boost: 0.5 },
        }),
      });

      if (!resp.ok) {
        const txt = await resp.text().catch(() => '');
        throw new Error(`ElevenLabs error: ${resp.status} ${txt}`);
      }

      const arrayBuffer = await resp.arrayBuffer();
      const buf = Buffer.from(arrayBuffer);
      return new Response(buf, {
        status: 200,
        headers: {
          'Content-Type': accept,
          'Content-Disposition': `inline; filename="${filename || `voiceover.${outFmt}`}"`,
          'Cache-Control': 'no-store',
        },
      });
    }

    // Fallback to Hugging Face if configured
    if (hfToken) {
      const hfModel = process.env.HF_TTS_MODEL || 'suno/bark-small';
      const headers: Record<string, string> = {
        Authorization: `Bearer ${hfToken}`,
        'Content-Type': 'application/json',
        Accept: 'audio/wav',
      };
      const billTo = process.env.HF_ORG;
      if (billTo) headers['X-HF-Bill-To'] = billTo;

      const resp = await fetch(`https://api-inference.huggingface.co/models/${hfModel}`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          inputs: script,
          options: { use_cache: true, wait_for_model: true },
        }),
      });

      if (!resp.ok) {
        const txt = await resp.text().catch(() => '');
        throw new Error(`HF TTS error: ${resp.status} ${txt}`);
      }

      const arrayBuffer = await resp.arrayBuffer();
      const buf = Buffer.from(arrayBuffer);
      return new Response(buf, {
        status: 200,
        headers: {
          'Content-Type': 'audio/wav',
          'Content-Disposition': `inline; filename="${filename || 'voiceover.wav'}"`,
          'Cache-Control': 'no-store',
        },
      });
    }

    return new Response(JSON.stringify({ error: 'No TTS provider configured' }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
    });
  } catch (error) {
    console.error('TTS generation error:', error);
    return new Response(JSON.stringify({ error: 'tts_failed' }), {
      status: 502,
      headers: { 'Content-Type': 'application/json' },
    });
  }
}
