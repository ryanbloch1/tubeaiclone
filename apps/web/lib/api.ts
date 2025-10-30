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

export async function generateVoiceoverSync(
  script: string,
  filename?: string,
  opts?: { projectId?: string; scriptId?: string; voice_id?: string; model_id?: string; format?: 'wav' | 'mp3' }
): Promise<{ blob: Blob; audioDataUrl: string; voiceoverId: string }> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 60_000);
  try {
    // Only call local Next.js TTS route (prefers ElevenLabs if configured, falls back to HF)
    const resp = await fetch(`/api/voiceover/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        script,
        filename: filename || "voiceover.wav",
        project_id: opts?.projectId,
        script_id: opts?.scriptId,
        voice_id: opts?.voice_id,
        model_id: opts?.model_id,
        format: opts?.format,
      }),
      signal: controller.signal,
    });
    if (!resp.ok) {
      const errText = await resp.text().catch(() => "");
      throw new Error(`Sync generation failed: ${resp.status} ${errText}`);
    }
    
    const data = await resp.json();
    if (!data.audio_blob || !data.audio_data_url) {
      throw new Error('Invalid response format');
    }
    
    // Convert base64 back to blob
    const base64 = data.audio_blob;
    const binaryString = atob(base64);
    const bytes = new Uint8Array(binaryString.length);
    for (let i = 0; i < binaryString.length; i++) {
      bytes[i] = binaryString.charCodeAt(i);
    }
    const blob = new Blob([bytes], { type: 'audio/wav' });
    
    return {
      blob,
      audioDataUrl: data.audio_data_url,
      voiceoverId: data.voiceover_id
    };
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


