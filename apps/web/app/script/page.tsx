"use client";
import React, { useState, useEffect, useCallback, useMemo } from "react";
import { useRouter } from "next/navigation";
import { sanitizeScriptForVoiceover } from "@/lib/sanitize";
import { TitleBar } from "./ui/TitleBar";
import { WordCountModal } from "./ui/WordCountModal";
import { ContextModal } from "./ui/ContextModal";
import { StyleModal } from "./ui/StyleModal";

type ScriptResponse = { text?: string; error?: string; mock?: boolean };

export default function ScriptPage() {
  const [topic, setTopic] = useState("");
  const [style, setStyle] = useState("");
  const [mode, setMode] = useState<"script" | "outline">("script");
  const [temperature, setTemperature] = useState<number>(0.7);
  const [wordCount, setWordCount] = useState<number>(500);
  const [selection, setSelection] = useState<string>("");
  const [showWordModal, setShowWordModal] = useState(false);
  const [showContextModal, setShowContextModal] = useState(false);
  const [showStyleModal, setShowStyleModal] = useState(false);
  const [extraContext, setExtraContext] = useState("");

  const [imageCount, setImageCount] = useState(10);
  const [videoLength, setVideoLength] = useState<string>("1:00");
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
        body: JSON.stringify({
          topic,
          style_name: style || undefined,
          image_count: imageCount,
          mode,
          temperature,
          word_count: wordCount,
          selection: mode === "script" ? undefined : selection || undefined,
          context_mode: extraContext ? "web" : "default",
          web_data: extraContext || undefined,
        }),
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

  useEffect(() => {
    // Simple image count based on video length
    const lengthToImages: { [key: string]: number } = {
      "0:30": 5,
      "1:00": 10,
      "2:00": 20,
      "3:00": 30
    };
    setImageCount(lengthToImages[videoLength] || 10);
  }, [videoLength]);

  const sanitizedScript = useMemo(() => sanitizeScriptForVoiceover(editableScript), [editableScript]);

  const goToVoiceover = () => {
    try {
      localStorage.setItem("tubeai_script", sanitizedScript); // For voiceover (sanitized)
      localStorage.setItem("tubeai_original_script", editableScript); // For images (original with scenes)
      localStorage.setItem("tubeai_from_script", "true"); // Track navigation source
    } catch {}
    window.location.href = "/voiceover";
  };

  return (
    <main className="min-h-screen bg-slate-50">
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-4xl font-bold text-center mb-8 text-slate-900">Enter Video Title</h1>
        <form onSubmit={onSubmit} className="max-w-4xl mx-auto space-y-4">
          <TitleBar
            topic={topic}
            setTopic={setTopic}
            wordCount={wordCount}
            onOpenWordModal={() => setShowWordModal(true)}
            onOpenContextModal={() => setShowContextModal(true)}
            onOpenStyleModal={() => setShowStyleModal(true)}
            loading={loading}
            canSubmit={!!topic.trim()}
          />
          <div className="text-sm text-slate-500 pl-4">
            Credits remaining: 0  |  Estimated script credits: 0
          </div>
        </form>
      </div>

      {error && (
        <div className="max-w-4xl mx-auto mt-6">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-700 text-sm">{error}</p>
          </div>
        </div>
      )}
      
      {result?.text && (
        <div className="max-w-4xl mx-auto mt-8 space-y-6">
          {result.mock && (
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
              <p className="text-amber-700 text-sm">Mock fallback (no API key detected)</p>
            </div>
          )}
          
          <div className="bg-white rounded-lg border border-slate-200 p-6 shadow-sm">
            <label className="block text-sm font-medium text-slate-700 mb-3">
              Edit script
            </label>
            <textarea
              className="w-full rounded-lg border border-slate-300 p-4 text-slate-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-colors resize-none"
              rows={15}
              value={editableScript}
              onChange={(e) => setEditableScript(e.target.value)}
              placeholder="Your generated script will appear here..."
            />
            
            <div className="mt-6 flex justify-end">
              <button
                onClick={goToVoiceover}
                className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-lg font-semibold transition-all duration-200 hover:transform hover:-translate-y-0.5 hover:shadow-lg"
              >
                Use for Voiceover →
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modals */}
      <WordCountModal
        open={showWordModal}
        wordCount={wordCount}
        onClose={() => setShowWordModal(false)}
        onSave={(wc: number) => { setWordCount(wc); setShowWordModal(false); }}
      />
      <ContextModal
        open={showContextModal}
        value={extraContext}
        onClose={() => setShowContextModal(false)}
        onSave={(txt: string) => { setExtraContext(txt); setShowContextModal(false); }}
      />
      <StyleModal
        open={showStyleModal}
        onClose={() => setShowStyleModal(false)}
        onCreate={(name: string) => { setStyle(name); setShowStyleModal(false); }}
      />
    </main>
  );
}


