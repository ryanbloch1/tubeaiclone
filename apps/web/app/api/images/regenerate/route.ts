import { NextRequest, NextResponse } from 'next/server';
import { API_BASE } from '@/lib/config';

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const auth = req.headers.get('authorization') || '';
    const resp = await fetch(`${API_BASE}/api/images/regenerate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: auth,
      },
      body: JSON.stringify(body),
    });
    const text = await resp.text();
    let data: unknown;
    try { data = JSON.parse(text); } catch { data = { raw: text }; }
    return NextResponse.json(data, { status: resp.status });
  } catch (e: unknown) {
    const message = e instanceof Error ? e.message : 'Failed to regenerate image';
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
