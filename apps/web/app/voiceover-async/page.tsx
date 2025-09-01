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
    <main className="min-h-screen bg-slate-50">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-slate-900 mb-2">
              🎙️ Asynchronous Voice Generation
            </h1>
            <p className="text-slate-600">
              Queue your voice generation for high-quality processing
            </p>
          </div>
          
          <div className="bg-white rounded-lg border border-slate-200 p-6 shadow-sm mb-6">
            <form onSubmit={enqueue} className="space-y-6">
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
                    <span className="bg-purple-100 text-purple-800 px-2 py-1 rounded text-xs font-medium">
                      Queue-based
                    </span>
                  </div>
                  <div className="text-xs text-slate-500">
                    Higher quality • Longer processing time
                  </div>
                </div>
                
                <button
                  type="submit"
                  disabled={loading || !script.trim()}
                  className="bg-purple-600 hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed text-white px-8 py-3 rounded-lg font-semibold transition-all duration-200 hover:transform hover:-translate-y-0.5 hover:shadow-lg flex items-center space-x-2"
                >
                  {loading ? (
                    <>
                      <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
                      <span>Enqueuing...</span>
                    </>
                  ) : (
                    <>
                      <span>📤</span>
                      <span>Add to Queue</span>
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

          {jobId && (
            <div className="bg-white rounded-lg border border-slate-200 p-6 shadow-sm">
              <h3 className="text-lg font-semibold text-slate-900 mb-4 flex items-center">
                <span className="mr-2">📋</span>
                Job Status
              </h3>
              
              <div className="space-y-4">
                <div className="bg-slate-50 rounded-lg p-4">
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <p className="text-sm text-slate-600 mb-1">Job ID</p>
                      <p className="font-mono text-sm text-slate-900 bg-white px-2 py-1 rounded border">
                        {jobId}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-slate-600 mb-1">Status</p>
                      <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                        status?.status === 'finished' ? 'bg-green-100 text-green-800' :
                        status?.status === 'failed' ? 'bg-red-100 text-red-800' :
                        status?.status === 'processing' ? 'bg-blue-100 text-blue-800' :
                        'bg-yellow-100 text-yellow-800'
                      }`}>
                        {status?.status === 'finished' && '✅ '}
                        {status?.status === 'failed' && '❌ '}
                        {status?.status === 'processing' && '⏳ '}
                        {(status?.status === 'pending' || !status?.status) && '⏳ '}
                        {status?.status || 'pending'}
                      </span>
                    </div>
                  </div>
                  
                  {status?.status === 'processing' && (
                    <div className="mb-3">
                      <div className="w-full bg-blue-200 rounded-full h-2">
                        <div className="bg-blue-600 h-2 rounded-full animate-pulse w-3/4"></div>
                      </div>
                      <p className="text-xs text-slate-500 mt-1">Processing your voice generation...</p>
                    </div>
                  )}
                </div>
                
                {signedUrl && (
                  <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                    <h4 className="font-medium text-green-900 mb-3 flex items-center">
                      <span className="mr-2">🎉</span>
                      Voice Generation Complete!
                    </h4>
                    <div className="flex justify-between items-center">
                      <div className="text-sm text-green-700">
                        Your high-quality voiceover is ready for download
                      </div>
                      <div className="flex space-x-3">
                        <a
                          href={signedUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg font-medium transition-colors flex items-center space-x-2"
                        >
                          <span>📥</span>
                          <span>Download WAV</span>
                        </a>
                        <button className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors flex items-center space-x-2">
                          <span>🎬</span>
                          <span>Continue to Video</span>
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}


