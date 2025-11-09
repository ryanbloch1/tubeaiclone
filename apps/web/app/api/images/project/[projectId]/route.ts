import { NextRequest, NextResponse } from 'next/server';

export async function GET(
  _req: NextRequest,
  { params }: { params: Promise<{ projectId: string }> }
) {
  try {
    const { projectId } = await params;
    const auth = _req.headers.get('authorization') || '';
    const resp = await fetch(`http://127.0.0.1:8000/api/images/project/${projectId}`, {
      headers: { Authorization: auth },
      cache: 'no-store'
    });
    const text = await resp.text();
    let data: any;
    try { data = JSON.parse(text); } catch { data = { raw: text }; }
    return NextResponse.json(data, { status: resp.status });
  } catch (e: any) {
    return NextResponse.json({ error: e?.message || 'Failed to fetch images' }, { status: 500 });
  }
}



