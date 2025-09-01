"use client";
import { useEffect, useState } from "react";
import { generateVoiceoverSync } from "@/lib/api";

export default function VoiceoverSyncPage() {
  const [script, setScript] = useState("");
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    try {
      const cached = localStorage.getItem("tubeai_script");
      if (cached) setScript(cached);
    } catch {}
  }, []);

  const onSubmit = async (e: React.FormEvent) => {
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
    <main className="min-h-screen bg-slate-50">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-slate-900 mb-2">
              🎙️ Synchronous Voice Generation
            </h1>
            <p className="text-slate-600">
              Real-time voice generation with immediate results
            </p>
          </div>
          
          <div className="bg-white rounded-lg border border-slate-200 p-6 shadow-sm mb-6">
            <form onSubmit={onSubmit} className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-3">
                  Script Content
                </label>
                <textarea
                  className="w-full rounded-lg border border-slate-300 p-4 text-slate-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-colors resize-none"
                  rows={10}
                  placeholder="Enter your script here or it will auto-load from your previous generation..."
                  value={script}
                  onChange={(e) => setScript(e.target.value)}
                />
                <div className="flex justify-between items-center mt-2">
                  <span className="text-sm text-slate-500">
                    {script.length} characters
                  </span>
                  <button 
                    type="button"
                    onClick={() => setScript("")}
                    className="text-sm text-slate-400 hover:text-slate-600 transition-colors"
                  >
                    Clear
                  </button>
                </div>
              </div>
              
              <div className="flex justify-between items-center pt-4 border-t border-slate-200">
                <div className="flex items-center space-x-4">
                  <div className="flex items-center space-x-2">
                    <span className="text-sm text-slate-600">Processing:</span>
                    <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs font-medium">
                      Real-time
                    </span>
                  </div>
                </div>
                
                <button
                  type="submit"
                  disabled={loading || !script.trim()}
                  className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-white px-8 py-3 rounded-lg font-semibold transition-all duration-200 hover:transform hover:-translate-y-0.5 hover:shadow-lg flex items-center space-x-2"
                >
                  {loading ? (
                    <>
                      <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
                      <span>Generating...</span>
                    </>
                  ) : (
                    <>
                      <span>⚡</span>
                      <span>Generate Now</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
              <div className="flex items-center">
                <span className="text-red-600 mr-2">❌</span>
                <p className="text-red-700 text-sm">{error}</p>
              </div>
            </div>
          )}

          {audioUrl && (
            <div className="bg-white rounded-lg border border-slate-200 p-6 shadow-sm">
              <h3 className="text-lg font-semibold text-slate-900 mb-4 flex items-center">
                <span className="mr-2">✅</span>
                Voice Generated Successfully
              </h3>
              
              <div className="space-y-4">
                <div className="bg-slate-50 rounded-lg p-4">
                  <audio 
                    controls 
                    src={audioUrl} 
                    className="w-full h-12"
                    style={{
                      backgroundColor: 'transparent',
                      borderRadius: '8px'
                    }}
                  />
                </div>
                
                <div className="flex justify-between items-center">
                  <div className="text-sm text-slate-600 flex items-center space-x-2">
                    <span>⚡</span>
                    <span>Generated in real-time</span>
                  </div>
                  <div className="flex space-x-3">
                    <a
                      href={audioUrl}
                      download="voiceover.wav"
                      className="bg-slate-100 hover:bg-slate-200 text-slate-700 px-4 py-2 rounded-lg font-medium transition-colors flex items-center space-x-2"
                    >
                      <span>📥</span>
                      <span>Download WAV</span>
                    </a>
                    <button className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg font-medium transition-colors flex items-center space-x-2">
                      <span>🎬</span>
                      <span>Continue to Video</span>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}


