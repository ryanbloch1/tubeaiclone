import { NextRequest } from 'next/server';

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const auth = req.headers.get('authorization') || '';
    
    // Forward the streaming request to FastAPI
    const resp = await fetch('http://127.0.0.1:8000/api/images/generate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: auth,
      },
      body: JSON.stringify(body),
    });
    
    if (!resp.ok) {
      const errorText = await resp.text();
      return new Response(errorText, { status: resp.status });
    }
    
    // Return the streaming response directly
    return new Response(resp.body, {
      status: resp.status,
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'X-Accel-Buffering': 'no',
      },
    });
  } catch (e: any) {
    return new Response(JSON.stringify({ error: e?.message || 'Failed to generate images' }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
    });
  }
}
