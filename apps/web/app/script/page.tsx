"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from 'next/navigation';
import { useAuth } from '@/components/auth/AuthProvider';
import { AuthGuard } from '@/components/auth/AuthGuard';
import { TitleBar } from "./ui/TitleBar";
import { WordCountModal } from "./ui/WordCountModal";
import { ContextModal } from "./ui/ContextModal";
import { StyleModal } from "./ui/StyleModal";

type ScriptResponse = { 
  script?: string; 
  scriptId?: string;
  projectId?: string;
  error?: string; 
  mock?: boolean 
};

export default function ScriptPage() {
  return (
    <AuthGuard>
      <ScriptPageContent />
    </AuthGuard>
  );
}

function ScriptPageContent() {
  const router = useRouter();
  const { session } = useAuth();
  
  // Form state
  const [topic, setTopic] = useState('');
  const [style, setStyle] = useState('');
  const [mode, setMode] = useState<'script' | 'outline' | 'rewrite'>('script');
  const [temperature, setTemperature] = useState(0.7);
  const [wordCount, setWordCount] = useState(500);
  const [selection, setSelection] = useState('');
  const [extraContext, setExtraContext] = useState('');
  const [imageCount, setImageCount] = useState(10);
  const [videoLength, setVideoLength] = useState('1:00');
  const [editableScript, setEditableScript] = useState('');

  // UI state
  const [showWordModal, setShowWordModal] = useState(false);
  const [showContextModal, setShowContextModal] = useState(false);
  const [showStyleModal, setShowStyleModal] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ScriptResponse | null>(null);
  const [projectId, setProjectId] = useState<string | null>(null);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setResult(null);
    setLoading(true);
    
    try {
      const response = await fetch("/api/script/generate", {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Authorization": `Bearer ${session?.access_token}`
        },
        body: JSON.stringify({
          topic,
          style: style || undefined,
          mode,
          temperature,
          wordCount,
          selection: mode === "script" ? undefined : selection || undefined,
          extraContext: extraContext || undefined,
          imageCount,
          videoLength,
          projectId
        }),
      });

      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || `HTTP ${response.status}`);
      }
      
      setResult(data);
      setProjectId(data.projectId);
      setEditableScript(data.script || "");
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to generate";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  // Update image count when video length changes
  useEffect(() => {
    const lengthToImages: { [key: string]: number } = {
      "0:30": 5,
      "1:00": 10,
      "2:00": 20,
      "3:00": 30
    };
    const next = lengthToImages[videoLength] || 10;
    if (next !== imageCount) {
      setImageCount(next);
    }
  }, [videoLength, imageCount]);

  const goToVoiceover = () => {
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
      
      {result?.script && (
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