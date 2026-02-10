import type { NextRequest } from 'next/server';
import { createClient } from '@/lib/supabase/server';
import { API_BASE } from '@/lib/config';

export const runtime = 'nodejs';

export async function POST(request: NextRequest) {
  try {
    const { script, voice_id, model_id, project_id, script_id }: { script?: string; voice_id?: string; model_id?: string; project_id?: string; script_id?: string } = await request.json();
    if (!script || !script.trim()) {
      return new Response(JSON.stringify({ error: 'script is required' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' },
      });
    }
    // Bridge to FastAPI System TTS
    const supabase = await createClient();
    const { data: { session }, error: authError } = await supabase.auth.getSession();
    if (authError || !session) {
      return new Response(JSON.stringify({ error: 'Unauthorized' }), { status: 401, headers: { 'Content-Type': 'application/json' } });
    }

    const resp = await fetch(`${API_BASE}/api/voiceover/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session.access_token}`,
      },
      body: JSON.stringify({
        project_id: project_id,
        script_id: script_id,
        text: script,
        voice_id: voice_id || 'default',
        model_id: model_id || 'system_tts',
      }),
    });

    if (!resp.ok) {
      const txt = await resp.text().catch(() => '');
      return new Response(JSON.stringify({ error: `FastAPI error: ${resp.status} ${txt}` }), {
        status: 502,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    const data = await resp.json();
    const audioDataUrl: string | undefined = data?.audio_data_url;
    if (!audioDataUrl || !audioDataUrl.startsWith('data:audio/')) {
      return new Response(JSON.stringify({ error: 'Invalid audio response' }), {
        status: 502,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    const base64 = audioDataUrl.split(',')[1] || '';
    
    // Return both the audio blob and the metadata
    return new Response(JSON.stringify({
      audio_blob: base64,
      audio_data_url: audioDataUrl,
      voiceover_id: data?.voiceover_id,
      success: data?.success
    }), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-store',
      },
    });
  } catch (error) {
    console.error('TTS generation error:', error);
    return new Response(JSON.stringify({ error: 'tts_failed' }), {
      status: 502,
      headers: { 'Content-Type': 'application/json' },
    });
  }
}
