import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
  try {
    console.log('[VIDEO API] Compile request received');
    const body = await req.json();
    const auth = req.headers.get('authorization') || '';
    
    // Debug logging
    console.log('[VIDEO API] Auth header present:', !!auth);
    console.log('[VIDEO API] Auth header length:', auth.length);
    console.log('[VIDEO API] Project ID:', body.project_id);
    
    if (!auth) {
      console.log('[VIDEO API] No auth header, returning 401');
      return NextResponse.json({ error: 'No authorization header provided' }, { status: 401 });
    }
    
    console.log('[VIDEO API] Forwarding request to backend...');
    const resp = await fetch('http://127.0.0.1:8000/api/video/compile', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: auth,
      },
      body: JSON.stringify(body),
    }).catch((fetchError) => {
      console.error('[VIDEO API] Backend fetch error:', fetchError);
      throw fetchError;
    });
    
    console.log('[VIDEO API] Backend response status:', resp.status);
    const text = await resp.text();
    console.log('[VIDEO API] Backend response length:', text.length);
    
    let data: any;
    try { 
      data = JSON.parse(text); 
    } catch { 
      console.log('[VIDEO API] Failed to parse JSON, returning raw text');
      data = { raw: text }; 
    }
    
    console.log('[VIDEO API] Returning response to client');
    return NextResponse.json(data, { status: resp.status });
  } catch (e: any) {
    console.error('[VIDEO API] Error:', e);
    console.error('[VIDEO API] Error stack:', e.stack);
    return NextResponse.json({ 
      error: e?.message || 'Failed to compile video',
      details: String(e)
    }, { status: 500 });
  }
}

