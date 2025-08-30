"use client";
import { useState, useEffect } from "react";
import { createVoiceoverJob, getVoiceoverStatus, type JobStatus } from "@/lib/api";

export default function VoiceoverAsyncPage() {
  const [script, setScript] = useState("");
  const [jobId, setJobId] = useState<string | null>(null);
  const [status, setStatus] = useState<JobStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    try {
      const cached = localStorage.getItem("tubeai_script");
      if (cached) setScript(cached);
    } catch {}
  }, []);

  const enqueue = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setStatus(null);
    setJobId(null);
    setLoading(true);
    try {
      const res = await createVoiceoverJob(script);
      setJobId(res.job_id);
      setStatus({ job_id: res.job_id, status: res.status });
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to enqueue";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!jobId) return;
    let active = true;
    const id = setInterval(async () => {
      try {
        const s = await getVoiceoverStatus(jobId);
        if (!active) return;
        setStatus(s);
        if (s.status === "finished" || s.status === "failed") {
          clearInterval(id);
        }
      } catch {
        // ignore transient errors
      }
    }, 2500);
    return () => {
      active = false;
      clearInterval(id);
    };
  }, [jobId]);

  const signedUrl: string | undefined = status?.signed_url;

  return (
    <div className="mx-auto max-w-3xl p-6 space-y-6">
      <h1 className="text-2xl font-semibold">Asynchronous Voiceover</h1>
      <form onSubmit={enqueue} className="space-y-4">
        <textarea
          className="w-full rounded border p-3"
          rows={8}
          placeholder="Enter script..."
          value={script}
          onChange={(e) => setScript(e.target.value)}
        />
        <button
          type="submit"
          disabled={loading || !script.trim()}
          className="rounded bg-black px-4 py-2 text-white disabled:opacity-50"
        >
          {loading ? "Enqueuing..." : "Enqueue"}
        </button>
      </form>

      {error && <p className="text-red-600">{error}</p>}

      {jobId && (
        <div className="space-y-2">
          <p className="text-sm text-gray-600">Job: {jobId}</p>
          <p className="font-medium">Status: {status?.status || "pending"}</p>
          {signedUrl && (
            <a className="text-blue-600 underline" href={signedUrl} target="_blank">Download WAV</a>
          )}
        </div>
      )}
    </div>
  );
}


