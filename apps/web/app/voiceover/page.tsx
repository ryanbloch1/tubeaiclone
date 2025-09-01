"use client";
import { useEffect, useMemo, useState } from "react";
import { generateVoiceoverSync } from "@/lib/api";
import { sanitizeScriptForVoiceover } from "@/lib/sanitize";

export default function VoiceoverPage() {
  const [rawScript, setRawScript] = useState("");
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [cameFromScript, setCameFromScript] = useState(false);

  useEffect(() => {
    try {
      const cached = localStorage.getItem("tubeai_script");
      const fromScript = localStorage.getItem("tubeai_from_script") === "true";
      if (cached) setRawScript(cached);
      setCameFromScript(fromScript);
      // Clear the navigation flag
      localStorage.removeItem("tubeai_from_script");
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
    <main className="min-h-screen bg-slate-50">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-4xl font-bold text-center mb-8 text-slate-900">
            🎙️ Voice Generation
          </h1>
          
          {cameFromScript && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
              <div className="flex items-center">
                <span className="text-green-600 mr-2">✅</span>
                <p className="text-green-700 text-sm">
                  Script loaded successfully! Ready to generate your voiceover.
                </p>
              </div>
            </div>
          )}
          
          <div className="bg-white rounded-lg border border-slate-200 p-6 shadow-sm mb-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-slate-900">Script Preview</h2>
              <span className="text-sm text-slate-500">
                {script.length} characters
              </span>
            </div>
            
            <form onSubmit={onGenerate} className="space-y-6">
              <div>
                <textarea
                  className="w-full rounded-lg border border-slate-300 p-4 text-slate-900 bg-slate-50 resize-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-colors"
                  rows={12}
                  value={script}
                  readOnly
                  placeholder="Your script will appear here from the previous step..."
                />
                <p className="text-sm text-slate-500 mt-2">
                  This script was loaded from your previous generation. 
                  <a href="/script" className="text-blue-600 hover:text-blue-700 ml-1">
                    Generate a new script →
                  </a>
                </p>
              </div>
              
              <div className="flex justify-between items-center">
                <div className="flex items-center space-x-4">
                  <div className="flex items-center space-x-2">
                    <span className="text-sm text-slate-600">Voice:</span>
                    <select className="border border-slate-300 rounded-lg px-3 py-2 text-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-colors">
                      <option>Default (System)</option>
                      <option>Professional Male</option>
                      <option>Professional Female</option>
                    </select>
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
                      <span>🎵</span>
                      <span>Generate Voiceover</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
              <p className="text-red-700 text-sm">{error}</p>
            </div>
          )}

          {audioUrl && (
            <div className="bg-white rounded-lg border border-slate-200 p-6 shadow-sm">
              <h3 className="text-lg font-semibold text-slate-900 mb-4 flex items-center">
                <span className="mr-2">✅</span>
                Voiceover Generated Successfully
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
                  <div className="text-sm text-slate-600">
                    Ready to use in your video project
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
                                            <button 
                          onClick={() => {
                            // Pass both sanitized script (for voiceover) and original script (for images)
                            localStorage.setItem("tubeai_from_voiceover", "true");
                            window.location.href = "/images";
                          }}
                          className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg font-medium transition-colors flex items-center space-x-2"
                        >
                          <span>🎨</span>
                          <span>Continue to Images</span>
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


