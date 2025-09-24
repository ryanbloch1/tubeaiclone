"use client";
import React from "react";
import { useRouter } from "next/navigation";
import { TitleBar } from "./ui/TitleBar";
import { WordCountModal } from "./ui/WordCountModal";
import { ContextModal } from "./ui/ContextModal";
import { StyleModal } from "./ui/StyleModal";
import { useVideoStore } from "@/lib/store";

type ScriptResponse = { text?: string; error?: string; mock?: boolean };

export default function ScriptPage() {
  const router = useRouter();
  const setScriptState = useVideoStore(s => s.setScriptState);
  const topic = useVideoStore(s => s.topic);
  const style = useVideoStore(s => s.style);
  const mode = useVideoStore(s => s.mode);
  const temperature = useVideoStore(s => s.temperature);
  const wordCount = useVideoStore(s => s.wordCount);
  const selection = useVideoStore(s => s.selection);
  const extraContext = useVideoStore(s => s.extraContext);
  const imageCount = useVideoStore(s => s.imageCount);
  const videoLength = useVideoStore(s => s.videoLength);
  const editableScript = useVideoStore(s => s.editableScript);

  const [showWordModal, setShowWordModal] = React.useState(false);
  const [showContextModal, setShowContextModal] = React.useState(false);
  const [showStyleModal, setShowStyleModal] = React.useState(false);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [result, setResult] = React.useState<ScriptResponse | null>(null);
  const goingToVoiceoverRef = React.useRef(false);

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
      setScriptState({ editableScript: data.text || "" });
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to generate";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => {
    const lengthToImages: { [key: string]: number } = {
      "0:30": 5,
      "1:00": 10,
      "2:00": 20,
      "3:00": 30
    };
    const next = lengthToImages[videoLength] || 10;
    if (next !== imageCount) setScriptState({ imageCount: next });
  }, [videoLength, imageCount, setScriptState]);

  // Clear script when navigating away from this page (but not when going to voiceover)
  React.useEffect(() => {
    return () => {
      // Only clear if we're not going to voiceover page
      if (!goingToVoiceoverRef.current) {
        setScriptState({ editableScript: "" });
      }
    };
  }, [setScriptState]);


  const goToVoiceover = () => {
    goingToVoiceoverRef.current = true;
    router.push("/voiceover");
  };

  return (
    <main className="min-h-screen bg-slate-50">
      <div className="container mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-8">
          <button
            onClick={() => router.push("/")}
            className="bg-slate-100 hover:bg-slate-200 text-slate-700 px-4 py-2 rounded-lg font-medium transition-colors flex items-center space-x-2"
          >
            <span>←</span>
            <span>Back to Home</span>
          </button>
          <h1 className="text-4xl font-bold text-slate-900">Enter Video Title</h1>
          <div className="w-32"></div> {/* Spacer for centering */}
        </div>
        <form onSubmit={onSubmit} className="max-w-4xl mx-auto space-y-4">
          <TitleBar
            topic={topic}
            setTopic={(v: string) => setScriptState({ topic: v })}
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
              className="w-full rounded-lg border border-slate-300 p-4 text-white bg-slate-800 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-colors resize-none"
              rows={15}
              value={editableScript}
              onChange={(e) => setScriptState({ editableScript: e.target.value })}
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
        onSave={(wc: number) => { setScriptState({ wordCount: wc }); setShowWordModal(false); }}
      />
      <ContextModal
        open={showContextModal}
        value={extraContext}
        onClose={() => setShowContextModal(false)}
        onSave={(txt: string) => { setScriptState({ extraContext: txt }); setShowContextModal(false); }}
      />
      <StyleModal
        open={showStyleModal}
        onClose={() => setShowStyleModal(false)}
        onCreate={(name: string) => { setScriptState({ style: name }); setShowStyleModal(false); }}
      />
    </main>
  );
}


