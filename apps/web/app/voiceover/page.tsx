"use client";
import { useEffect, useMemo, useState } from "react";
import { generateVoiceoverSync } from "@/lib/api";
import { sanitizeScriptForVoiceover } from "@/lib/sanitize";

export default function VoiceoverPage() {
  const [rawScript, setRawScript] = useState("");
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    try {
      const cached = localStorage.getItem("tubeai_script");
      if (cached) setRawScript(cached);
    } catch {}
  }, []);

  const script = useMemo(() => sanitizeScriptForVoiceover(rawScript), [rawScript]);

  const onGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setAudioUrl(null);
    setLoading(true);
    try {
      const blob = await generateVoiceoverSync(script, "voiceover.wav");
      const url = URL.createObjectURL(blob);
      setAudioUrl(url);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to generate";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-3xl p-6 space-y-6">
      <h1 className="text-2xl font-semibold">Voiceover</h1>
      <form onSubmit={onGenerate} className="space-y-4">
        <textarea
          className="w-full rounded border border-gray-700 bg-transparent text-white p-3"
          rows={12}
          value={script}
          readOnly
        />
        <button
          type="submit"
          disabled={loading || !script.trim()}
          className="rounded bg-black px-4 py-2 text-white disabled:opacity-50"
        >
          {loading ? "Generating..." : "Generate Voiceover"}
        </button>
      </form>
      {error && <p className="text-red-600">{error}</p>}
      {audioUrl && (
        <div className="space-y-2">
          <audio controls src={audioUrl} className="w-full" />
          <a className="text-blue-600 underline" href={audioUrl} download="voiceover.wav">Download WAV</a>
        </div>
      )}
    </div>
  );
}


