'use client';
import { generateVoiceoverSync } from '@/lib/api';
import { sanitizeScriptForVoiceover } from '@/lib/sanitize';
import React, { Suspense, useMemo } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { createClient } from '@/lib/supabase/client';

export default function VoiceoverPage() {
  return (
    <Suspense
      fallback={(
        <main className="min-h-screen bg-slate-50">
          <div className="container mx-auto px-4 py-8">
            <div className="max-w-4xl mx-auto">
              <div className="bg-white rounded-lg border border-slate-200 p-8 text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                <p className="mt-4 text-slate-600">Loading voiceover...</p>
              </div>
            </div>
          </div>
        </main>
      )}
    >
      <VoiceoverPageContent />
    </Suspense>
  );
}

function VoiceoverPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const supabase = React.useMemo(() => createClient(), []);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [hasGeneratedVoiceover, setHasGeneratedVoiceover] = React.useState(false);
  const [editedScript, setEditedScript] = React.useState('');
  const [rawScript, setRawScript] = React.useState<string>('');
  const [audioUrl, setAudioUrl] = React.useState<string | null>(null);
  const [audioDataUrl, setAudioDataUrl] = React.useState<string | null>(null);
  const [audioReady, setAudioReady] = React.useState<boolean>(false);
  const [loadingExisting, setLoadingExisting] = React.useState<boolean>(true);
  const [projectId, setProjectId] = React.useState<string | null>(null);
  const [scriptId, setScriptId] = React.useState<string | null>(null);
  const [cameFromScript, setCameFromScript] = React.useState<boolean>(false);

  // Load script and existing voiceovers by projectId from URL
  React.useEffect(() => {
    const pid = searchParams.get('projectId');
    setProjectId(pid);
    async function load() {
      if (!pid) return;
      setLoadingExisting(true);
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) return;
      
      // Load project and script data
      const res = await fetch(`/api/projects/${pid}`, {
        headers: { 'Authorization': `Bearer ${session.access_token}` }
      });
      if (!res.ok) return;
      const data = await res.json();
      const script = data?.script;
      if (script) {
        setScriptId(script.id);
        const content = script.edited_script || script.raw_script || '';
        setRawScript(content);
        setCameFromScript(!!content.trim());
      }

      // Load existing voiceovers for this project
      try {
        const voiceoversRes = await fetch(`/api/voiceover/project/${pid}`, {
          headers: { 'Authorization': `Bearer ${session.access_token}` }
        });
        if (voiceoversRes.ok) {
          const voiceoversData = await voiceoversRes.json();
          const voiceovers = voiceoversData.voiceovers || [];
          
          // If there are existing voiceovers, load the most recent one
          if (voiceovers.length > 0) {
            const latestVoiceover = voiceovers[0]; // Already sorted by created_at desc
            if (latestVoiceover.audio_data_url) {
              setAudioDataUrl(latestVoiceover.audio_data_url);
              setHasGeneratedVoiceover(true);
              setAudioReady(false);
            }
          }
        }
      } catch (error) {
        console.error('Failed to load existing voiceovers:', error);
        // Don't show error to user, just continue without existing voiceover
      } finally {
        setLoadingExisting(false);
      }
    }
    load();
  }, [searchParams, supabase]);

  // Note: Do NOT prefill editedScript with raw on load.
  // Showing sanitized by default avoids confusing unsanitized content on arrival.
  // Also, do NOT auto-save edits back to store here; only save on explicit action.

  // Always compute sanitized from the latest raw + any local edits
  const sanitizedScript = useMemo(
    () => sanitizeScriptForVoiceover((editedScript || rawScript) || ''),
    [editedScript, rawScript]
  );
  // Display sanitized by default; switch to edited text once user types
  const displayScript = (editedScript.length > 0 ? editedScript : sanitizedScript) || '';
  
  // For voiceover generation, always use the sanitized version
  const scriptForVoiceover = sanitizedScript;

  // Debug logging (can be removed in production)
  React.useEffect(() => {
  }, [rawScript, editedScript, sanitizedScript]);
  const audioSrc: string | undefined = (audioUrl ?? undefined) || (audioDataUrl ?? undefined);

  const onGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setHasGeneratedVoiceover(false);
    setAudioUrl(null);
    setAudioReady(false);
    setLoading(true);
    try {
      const textForTts = scriptForVoiceover?.trim() ?? '';
      const result = await generateVoiceoverSync(textForTts, 'voiceover.wav', { projectId: projectId || undefined, scriptId: scriptId || undefined, voice_id: 'default', model_id: 'system_tts' });
      
      const url = URL.createObjectURL(result.blob);
      setAudioUrl(url);
      setAudioDataUrl(result.audioDataUrl);
      setHasGeneratedVoiceover(true);

      // Update project current_step to 'voiceover' after successful generation
      if (projectId) {
        const { data: { session } } = await supabase.auth.getSession();
        if (session) {
          await fetch(`/api/projects/${projectId}`, {
            method: 'PUT',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${session.access_token}`
            },
            body: JSON.stringify({
              status: 'voiceover'
            })
          });
        }
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to generate';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-slate-50">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          <div className="mb-6 flex items-center justify-between">
            <div className="flex items-center space-x-4">
              {projectId && (
                <button
                  onClick={() => router.push(`/script?projectId=${projectId}`)}
                  className="text-slate-600 hover:text-slate-900 text-sm font-medium flex items-center space-x-1 transition-colors"
                >
                  <span>←</span>
                  <span>Edit Script</span>
                </button>
              )}
              <button
                onClick={() => router.push('/')}
                className="text-slate-600 hover:text-slate-900 text-sm font-medium flex items-center space-x-1 transition-colors"
              >
                <span>Projects</span>
                <span>Projects</span>
              </button>
            </div>
          </div>

          <h1 className="text-3xl font-bold text-slate-900 mb-8 text-center">🎙️ Voice Generation</h1>

          {cameFromScript && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
              <div className="flex items-center">
                <span className="text-green-600 mr-2">Done</span>
                <p className="text-green-700 text-sm">
                  Script loaded successfully! Ready to generate your voiceover.
                </p>
              </div>
            </div>
          )}

          <div className="bg-white rounded-lg border border-slate-200 p-6 shadow-sm mb-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-slate-900">
                Script Preview
              </h2>
            </div>

            <form onSubmit={onGenerate} className="space-y-6">
              <div>
                <textarea
                  className="w-full rounded-lg border border-black p-4 text-black bg-white resize-none focus:border-black focus:ring-2 focus:ring-black focus:ring-opacity-20 transition-colors"
                  rows={12}
                  value={displayScript}
                  onChange={(e) => setEditedScript(e.target.value)}
                  placeholder="Type your script here or it will appear from the previous step..."
                />
                <p className="text-sm text-slate-500 mt-2">
                  {displayScript.trim().length === 0 ? (
                    <span className="text-red-600">
                      No script text found. Type your script above or generate one on the previous page.
                    </span>
                  ) : (
                    <>You can edit this script directly. The sanitized version will be used for voiceover generation.</>
                  )}
                  <Link
                    href="/script"
                    className="text-blue-600 hover:text-blue-700 ml-1"
                  >
                    Generate a new script →
                  </Link>
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
                  disabled={loading || !displayScript.trim()}
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

          {(loadingExisting || (hasGeneratedVoiceover && audioSrc && !audioReady)) && (
            <div className="bg-white rounded-lg border border-slate-200 p-6 shadow-sm mb-4">
              <h3 className="text-lg font-semibold text-slate-900 mb-4 flex items-center">
                <div className="animate-spin h-4 w-4 border-2 border-slate-700 border-t-transparent rounded-full mr-2"></div>
                Preparing your voiceover...
              </h3>
              <div className="w-full h-12 rounded-lg bg-slate-100 animate-pulse" />
              <p className="text-sm text-slate-500 mt-3">This can take a few seconds the first time while audio loads.</p>
            </div>
          )}

          {hasGeneratedVoiceover && audioSrc && (
            <div className="bg-white rounded-lg border border-slate-200 p-6 shadow-sm">
              <h3 className="text-lg font-semibold text-slate-900 mb-4 flex items-center">
                {audioReady ? <span className="mr-2">Done</span> : <div className="animate-spin h-4 w-4 border-2 border-slate-700 border-t-transparent rounded-full mr-2"></div>}
                {audioReady ? 'Voiceover Ready' : 'Loading audio...'}
              </h3>

              <div className="space-y-4">
                <div className="bg-slate-50 rounded-lg p-4">
                  <audio
                    controls
                    src={audioSrc}
                    className="w-full h-12"
                    style={{
                      backgroundColor: 'transparent',
                      borderRadius: '8px',
                    }}
                    onCanPlayThrough={() => setAudioReady(true)}
                  />
                </div>

                <div className="flex justify-between items-center">
                  <div className="text-sm text-slate-600">
                    Ready to use in your video project
                  </div>
                  <div className="flex space-x-3">
                    <a
                      href={audioSrc}
                      download="voiceover.wav"
                      className="bg-slate-100 hover:bg-slate-200 text-slate-700 px-4 py-2 rounded-lg font-medium transition-colors flex items-center space-x-2"
                    >
                      <span>📥</span>
                      <span>Download WAV</span>
                    </a>
                    <button
                      onClick={() => {
                        if (projectId) {
                          router.push(`/images?projectId=${projectId}`);
                        } else {
                          router.push('/images');
                        }
                      }}
                      className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg font-medium transition-colors flex items-center space-x-2"
                    >
                      <span>Images</span>
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
