import { API_BASE } from "./config";

export type HealthResponse = {
  status: string;
  queue?: string;
  redis_url?: string;
  redis_configured?: boolean;
  redis_connected?: boolean;
};

export async function getHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE}/health`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Health check failed: ${res.status}`);
  return res.json();
}

export async function generateVoiceoverSync(script: string, filename?: string): Promise<Blob> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 60_000);
  try {
    // Only call local Next.js TTS route (prefers ElevenLabs if configured, falls back to HF)
    const resp = await fetch(`/api/voiceover/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ script, filename: filename || "voiceover.wav" }),
      signal: controller.signal,
    });
    if (!resp.ok) {
      const errText = await resp.text().catch(() => "");
      throw new Error(`Sync generation failed: ${resp.status} ${errText}`);
    }
    return resp.blob();
  } finally {
    clearTimeout(timeoutId);
  }
}

export type EnqueueResponse = { job_id: string; status: string };

export async function createVoiceoverJob(script: string): Promise<EnqueueResponse>{
  const res = await fetch(`${API_BASE}/voiceovers`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ script }),
  });
  if (!res.ok) throw new Error(`Enqueue failed: ${res.status}`);
  return res.json();
}

export type JobStatus = {
  job_id: string;
  status: "queued" | "started" | "finished" | "failed" | string;
  result?: { output_path?: string };
  signed_url?: string;
  error?: string;
};

export async function getVoiceoverStatus(jobId: string): Promise<JobStatus> {
  const res = await fetch(`${API_BASE}/voiceovers/${jobId}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Status fetch failed: ${res.status}`);
  return res.json();
}


