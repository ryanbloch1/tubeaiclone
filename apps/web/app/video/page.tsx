'use client';
import React from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { createClient } from '@/lib/supabase/client';

type Video = {
  id: string;
  project_id: string;
  video_data_url?: string;
  video_url?: string;
  status: string;
  created_at?: string;
};

export default function VideoPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const supabase = createClient();
  const [projectId, setProjectId] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState<boolean>(true);
  const [error, setError] = React.useState<string | null>(null);
  const [compiling, setCompiling] = React.useState<boolean>(false);
  const [video, setVideo] = React.useState<Video | null>(null);
  const [hasScript, setHasScript] = React.useState<boolean>(false);
  const [hasVoiceover, setHasVoiceover] = React.useState<boolean>(false);
  const [hasImages, setHasImages] = React.useState<boolean>(false);

  React.useEffect(() => {
    const pid = searchParams.get('projectId');
    setProjectId(pid);
    async function load() {
      if (!pid) {
        setLoading(false);
        setError('No project ID provided');
        return;
      }
      setLoading(true);
      setError(null);
      try {
        const { data: { session } } = await supabase.auth.getSession();
        if (!session) {
          setLoading(false);
          setError('Not authenticated');
          return;
        }

        // Fetch project data
        const projRes = await fetch(`/api/projects/${pid}`, {
          headers: { Authorization: `Bearer ${session.access_token}` },
          cache: 'no-store'
        });
        if (!projRes.ok) {
          setLoading(false);
          setError('Failed to load project');
          return;
        }

        const data = await projRes.json();
        const script = data?.script;
        setHasScript(!!script);

        // Check for voiceover
        const voiceoverRes = await fetch(`/api/voiceover/project/${pid}`, {
          headers: { Authorization: `Bearer ${session.access_token}` },
          cache: 'no-store'
        });
        if (voiceoverRes.ok) {
          const voiceoverData = await voiceoverRes.json();
          setHasVoiceover(voiceoverData.voiceovers && voiceoverData.voiceovers.length > 0);
        }

        // Check for images
        const imagesRes = await fetch(`/api/images/project/${pid}`, {
          headers: { Authorization: `Bearer ${session.access_token}` },
          cache: 'no-store'
        });
        if (imagesRes.ok) {
          const imagesData = await imagesRes.json();
          setHasImages(imagesData.images && imagesData.images.length > 0);
        }

        // Check for existing video
        const videoRes = await fetch(`/api/video/project/${pid}`, {
          headers: { Authorization: `Bearer ${session.access_token}` },
          cache: 'no-store'
        });
        if (videoRes.ok) {
          const videoData = await videoRes.json();
          if (videoData.video) {
            setVideo(videoData.video);
          }
        }

        setLoading(false);
      } catch (e: any) {
        console.error('Error loading video page:', e);
        setError(e?.message || 'Failed to load page');
        setLoading(false);
      }
    }
    load();
  }, [searchParams]);

  const onCompile = async () => {
    try {
      setCompiling(true);
      setError(null);
      const { data: { session } } = await supabase.auth.getSession();
      if (!session || !projectId) {
        setError('Not authenticated or no project ID');
        setCompiling(false);
        return;
      }

      console.log('[VIDEO] Starting compilation request...');
      console.log('[VIDEO] Project ID:', projectId);
      console.log('[VIDEO] Has session:', !!session);
      console.log('[VIDEO] Token length:', session.access_token?.length || 0);

      const resp = await fetch('/api/video/compile', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({ project_id: projectId }),
      }).catch((fetchError) => {
        console.error('[VIDEO] Fetch error:', fetchError);
        throw new Error(`Network error: ${fetchError.message}`);
      });

      console.log('[VIDEO] Response status:', resp.status);
      const responseText = await resp.text();
      console.log('[VIDEO] Response text length:', responseText.length);
      
      if (!resp.ok) {
        let errorMsg = responseText;
        try {
          const errorJson = JSON.parse(responseText);
          errorMsg = errorJson.error || errorJson.detail || responseText;
        } catch {}
        throw new Error(errorMsg || `HTTP ${resp.status}`);
      }

      const data = JSON.parse(responseText);
      if (data.success && data.video_data_url) {
        setVideo({
          id: data.video_id,
          project_id: projectId,
          video_data_url: data.video_data_url,
          status: 'completed',
        });
      } else {
        throw new Error('Video compilation failed');
      }
    } catch (e: any) {
      console.error('[VIDEO] Error compiling video:', e);
      setError(e?.message || 'Failed to compile video. Check the browser console for details.');
    } finally {
      setCompiling(false);
    }
  };

  // Show helpful message if no project ID
  if (!projectId && !loading) {
    return (
      <main className="min-h-screen bg-slate-50">
        <div className="container mx-auto px-4 py-8">
          <div className="max-w-6xl mx-auto">
            <h1 className="text-3xl font-bold text-slate-900 mb-6">🎬 Video Compilation</h1>
            <div className="bg-white rounded-lg border border-slate-200 p-8 text-center">
              <div className="text-5xl mb-4">🎥</div>
              <h2 className="text-xl font-semibold text-slate-900 mb-2">No Project Selected</h2>
              <p className="text-slate-600 mb-6">
                To compile a video, please continue from the images page.
              </p>
              <a
                href="/"
                className="inline-block bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors"
              >
                Go to Home
              </a>
            </div>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-slate-50">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-6xl mx-auto">
          <h1 className="text-3xl font-bold text-slate-900 mb-6">🎬 Video Compilation</h1>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
              <p className="text-red-700 text-sm">{error}</p>
            </div>
          )}

          {loading ? (
            <div className="bg-white rounded-lg border border-slate-200 p-8 text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-4 text-slate-600">Loading...</p>
            </div>
          ) : (
            <>
              {/* Requirements checklist */}
              <div className="bg-white rounded-lg border border-slate-200 p-6 shadow-sm mb-6">
                <h2 className="text-lg font-semibold text-slate-900 mb-4">Requirements</h2>
                <div className="space-y-2">
                  <div className={`flex items-center space-x-2 ${hasScript ? 'text-green-600' : 'text-red-600'}`}>
                    <span>{hasScript ? '✓' : '✗'}</span>
                    <span>Script generated</span>
                  </div>
                  <div className={`flex items-center space-x-2 ${hasVoiceover ? 'text-green-600' : 'text-red-600'}`}>
                    <span>{hasVoiceover ? '✓' : '✗'}</span>
                    <span>Voiceover generated</span>
                  </div>
                  <div className={`flex items-center space-x-2 ${hasImages ? 'text-green-600' : 'text-red-600'}`}>
                    <span>{hasImages ? '✓' : '✗'}</span>
                    <span>Images generated</span>
                  </div>
                </div>
              </div>

              {/* Compile button */}
              {!video && (
                <div className="bg-white rounded-lg border border-slate-200 p-6 shadow-sm mb-6">
                  <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                    <div className="flex-1">
                      <h2 className="text-lg font-semibold text-slate-900 mb-2">Compile Video</h2>
                      <p className="text-slate-600 text-sm">
                        Combine your script, voiceover, and images into a final MP4 video with fade transitions.
                      </p>
                    </div>
                    <button
                      onClick={onCompile}
                      disabled={compiling || !hasScript || !hasVoiceover || !hasImages}
                      className="bg-purple-600 hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed text-white px-6 py-3 rounded-lg font-semibold transition-colors whitespace-nowrap"
                    >
                      {compiling ? 'Compiling...' : 'Compile Video'}
                    </button>
                  </div>
                </div>
              )}

              {/* Video preview */}
              {video && video.video_data_url && (
                <div className="bg-white rounded-lg border border-slate-200 p-6 shadow-sm">
                  <h2 className="text-lg font-semibold text-slate-900 mb-4">Compiled Video</h2>
                  <div className="mb-4">
                    <video
                      controls
                      className="w-full rounded-lg"
                      src={video.video_data_url}
                    >
                      Your browser does not support the video tag.
                    </video>
                  </div>
                  <div className="flex justify-center">
                    <a
                      href={video.video_data_url}
                      download={`video-${projectId}.mp4`}
                      className="bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors inline-flex items-center space-x-2"
                    >
                      <span>⬇️</span>
                      <span>Download Video</span>
                    </a>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </main>
  );
}

