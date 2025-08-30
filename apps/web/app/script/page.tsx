"use client";
import { useEffect, useMemo, useState } from "react";
import { imageCountForVideoLength, sanitizeScriptForVoiceover, type VideoLengthOption } from "@/lib/sanitize";

type ScriptResponse = { text?: string; error?: string; mock?: boolean };

export default function ScriptPage() {
  const [topic, setTopic] = useState("");
  const [style, setStyle] = useState("");
  const [imageCount, setImageCount] = useState(10);
  const [videoLength, setVideoLength] = useState<VideoLengthOption>("1:00");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ScriptResponse | null>(null);
  const [editableScript, setEditableScript] = useState<string>("");

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setResult(null);
    setLoading(true);
    try {
      const res = await fetch("/api/script", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic, style_name: style, image_count: imageCount }),
      });
      const data = (await res.json()) as ScriptResponse;
      if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
      setResult(data);
      setEditableScript(data.text || "");
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to generate";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  // Keep imageCount in sync with selected video length
  useEffect(() => {
    setImageCount(imageCountForVideoLength(videoLength));
  }, [videoLength]);

  const sanitizedScript = useMemo(() => sanitizeScriptForVoiceover(editableScript), [editableScript]);

  const goToVoiceover = () => {
    try {
      localStorage.setItem("tubeai_script", sanitizedScript);
    } catch {}
    window.location.href = "/voiceover";
  };

  return (
    <div className="mx-auto max-w-3xl p-6 space-y-6">
      <h1 className="text-2xl font-semibold">Script Generation</h1>
      <form onSubmit={onSubmit} className="space-y-4">
        <input
          className="w-full rounded border p-3"
          placeholder="Topic (title)"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
        />
        <div className="flex gap-3">
          <input
            className="flex-1 rounded border p-3"
            placeholder="Style (optional)"
            value={style}
            onChange={(e) => setStyle(e.target.value)}
          />
          <select
            className="w-40 rounded border p-3"
            value={videoLength}
            onChange={(e) => setVideoLength(e.target.value as VideoLengthOption)}
          >
            <option value="0:30">0:30</option>
            <option value="1:00">1:00</option>
            <option value="2:00">2:00</option>
            <option value="3:00">3:00</option>
            <option value="5:00">5:00</option>
            <option value="10:00">10:00</option>
          </select>
          <input
            type="number"
            min={1}
            max={20}
            className="w-28 rounded border p-3"
            value={imageCount}
            onChange={(e) => setImageCount(parseInt(e.target.value || "10", 10))}
            title="Scenes (auto-set by length, but editable)"
          />
        </div>
        <button
          type="submit"
          disabled={loading || !topic.trim()}
          className="rounded bg-black px-4 py-2 text-white disabled:opacity-50"
        >
          {loading ? "Generating..." : "Generate"}
        </button>
      </form>
      {error && <p className="text-red-600">{error}</p>}
      {result?.text && (
        <div className="space-y-3">
          {result.mock && <p className="text-sm text-gray-500">Mock fallback (no API key detected)</p>}
          <label className="text-sm text-gray-600">Edit script</label>
          <textarea
            className="w-full rounded border p-3"
            rows={16}
            value={editableScript}
            onChange={(e) => setEditableScript(e.target.value)}
          />
          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              className="rounded bg-blue-600 px-4 py-2 text-white"
              onClick={goToVoiceover}
            >
              Use for Voiceover
            </button>
          </div>
        </div>
      )}
    </div>
  );
}


