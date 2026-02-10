import { NextRequest, NextResponse } from 'next/server';
import { API_BASE } from '@/lib/config';

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const auth = req.headers.get('authorization') || '';
    
    // Debug logging
    
    if (!auth) {
      return NextResponse.json({ error: 'No authorization header provided' }, { status: 401 });
    }
    
    
    // Video compilation can take a while - set a longer timeout (5 minutes)
    const controller = new AbortController();
    const timeoutId = setTimeout(() => {
      controller.abort();
      console.error('[VIDEO API] Request to backend timed out after 5 minutes');
    }, 300000); // 5 minutes
    
    let resp: Response;
    try {
      resp = await fetch(`${API_BASE}/api/video/compile`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: auth,
        },
        body: JSON.stringify(body),
        signal: controller.signal,
      });
      clearTimeout(timeoutId);
    } catch (fetchError: unknown) {
      clearTimeout(timeoutId);
      console.error('[VIDEO API] Backend fetch error:', fetchError);
      const err = fetchError as { name?: string; message?: string; code?: string };

      if (err.name === 'AbortError') {
        return NextResponse.json({ 
          error: 'Video compilation timed out. The video is still being processed - please wait and refresh.',
          timeout: true
        }, { status: 504 });
      }
      
      // Check if backend is unreachable
      if (err.message?.includes('ECONNREFUSED') || err.code === 'ECONNREFUSED') {
        console.error('[VIDEO API] Backend is not reachable on port 8000');
        return NextResponse.json({ 
          error: 'Backend API is not reachable. Please ensure the FastAPI server is running on port 8000.',
          unreachable: true
        }, { status: 503 });
      }
      
      throw fetchError;
    }
    
    const text = await resp.text();
    
    let data: unknown;
    try { 
      data = JSON.parse(text); 
    } catch { 
      data = { raw: text }; 
    }
    
    return NextResponse.json(data, { status: resp.status });
  } catch (e: unknown) {
    console.error('[VIDEO API] Error:', e);
    if (e instanceof Error) {
      console.error('[VIDEO API] Error stack:', e.stack);
    }
    return NextResponse.json({ 
      error: e instanceof Error ? e.message : 'Failed to compile video',
      details: String(e)
    }, { status: 500 });
  }
}
