'use client';
import React, { Suspense } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { createClient } from '@/lib/supabase/client';

const getErrorMessage = (error: unknown, fallback: string) => {
  if (error instanceof Error) {
    return error.message;
  }
  return fallback;
};

// Video player component that handles both data URLs and file URLs
function VideoPlayer({ 
  videoDataUrl, 
  projectId, 
  onRecompile 
}: { 
  videoDataUrl: string; 
  projectId: string | null;
  onRecompile?: () => void;
}) {
  const [blobUrl, setBlobUrl] = React.useState<string | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const videoRef = React.useRef<HTMLVideoElement>(null);

  React.useEffect(() => {
    if (!videoDataUrl) return;

    // If it's already a regular URL (http, https, or relative path), use it directly
    if (videoDataUrl.startsWith('http://') || 
        videoDataUrl.startsWith('https://') || 
        videoDataUrl.startsWith('/')) {
      setBlobUrl(videoDataUrl);
      return;
    }

    // Convert data URL to blob URL for better browser performance
    const convertToBlob = async () => {
      try {
        
        // Extract base64 data from data URL
        const base64Match = videoDataUrl.match(/^data:video\/mp4;base64,(.+)$/);
        if (!base64Match) {
          throw new Error(`Invalid video data URL format. Expected data:video/mp4;base64,... but got: ${videoDataUrl.substring(0, 50)}...`);
        }

        const base64Data = base64Match[1];

        // Validate base64 string
        if (base64Data.length === 0) {
          throw new Error('Base64 data is empty');
        }

        // Check if base64 is valid (basic check)
        try {
          atob(base64Data.substring(0, Math.min(100, base64Data.length)));
        } catch (e) {
          throw new Error(`Invalid base64 data: ${e}`);
        }

        // Convert base64 to binary in chunks to avoid memory issues
        const binaryString = atob(base64Data);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
          bytes[i] = binaryString.charCodeAt(i);
        }

        // Verify MP4 file signature (should start with ftyp box at offset 4)
        if (bytes.length < 8) {
          throw new Error('Video file is too small to be valid');
        }
        
        // MP4 files: [4-byte box size][4-byte box type='ftyp']
        const boxSize = (bytes[0] << 24) | (bytes[1] << 16) | (bytes[2] << 8) | bytes[3];
        const boxType = String.fromCharCode(bytes[4], bytes[5], bytes[6], bytes[7]);
        
        
        // Validate MP4 structure
        if (boxType !== 'ftyp' && bytes.length > 20) {
          // Check if ftyp appears later (sometimes moov comes first before faststart)
          const ftypIndex = Array.from(bytes.slice(0, 100)).findIndex((_, i) => 
            bytes[i] === 0x66 && bytes[i+1] === 0x74 && bytes[i+2] === 0x79 && bytes[i+3] === 0x70
          );
          if (ftypIndex === -1 || ftypIndex > 20) {
            console.error('[VIDEO] Invalid MP4: ftyp box not found in first 100 bytes');
            throw new Error('Video file does not appear to be a valid MP4 format. File may be corrupted.');
          } else {
            console.warn('[VIDEO] Warning: ftyp box found at offset', ftypIndex, '- faststart may not have been applied');
          }
        } else if (boxType === 'ftyp') {
        }
        
        // Check file size matches first box size (basic validation)
        if (boxSize > bytes.length && boxSize < 1000000) {
          console.warn('[VIDEO] Warning: First box size', boxSize, 'exceeds file size', bytes.length);
        }

        // Create blob and blob URL
        const blob = new Blob([bytes], { type: 'video/mp4' });
        const url = URL.createObjectURL(blob);
        
        setBlobUrl(url);

        // Cleanup blob URL on unmount
        return () => {
          if (url) {
            URL.revokeObjectURL(url);
          }
        };
      } catch (e: unknown) {
        console.error('[VIDEO] Error converting to blob URL:', e);
        if (e instanceof Error) {
          console.error('[VIDEO] Error stack:', e.stack);
        }
        setError(getErrorMessage(e, 'Failed to load video'));
        // Fallback to data URL if blob conversion fails
        setBlobUrl(videoDataUrl);
      }
    };

    convertToBlob();
  }, [videoDataUrl]);

  // Additional validation: check if blob URL is valid
  React.useEffect(() => {
    if (!blobUrl) return;
    
    // Try to fetch the blob to verify it's accessible
    fetch(blobUrl)
      .then(res => {
        if (!res.ok) {
          console.error('[VIDEO] Blob fetch failed:', res.status, res.statusText);
          setError('Video blob is not accessible');
        } else {
        }
        return res.blob();
      })
      .then(blob => {
        if (blob.size === 0) {
          setError('Video file appears to be empty');
        }
      })
      .catch(e => {
        console.error('[VIDEO] Error validating blob:', e);
      });
  }, [blobUrl]);

  const handleDownload = () => {
    if (blobUrl) {
      const a = document.createElement('a');
      a.href = blobUrl;
      a.download = `video-${projectId || 'download'}.mp4`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    }
  };

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-700 text-sm font-semibold mb-2">Error loading video: {error}</p>
        <p className="text-red-600 text-xs mb-3">
          This video may have been compiled with older settings that aren&apos;t compatible with your browser.
          Try compiling a new video with the updated settings.
        </p>
        <p className="text-red-600 text-xs mb-4">Trying fallback method...</p>
        <video
          ref={videoRef}
          controls
          className="w-full rounded-lg mt-4"
          src={videoDataUrl}
          onError={(e) => {
            console.error('[VIDEO] Fallback video element error:', e);
            const videoEl = e.currentTarget;
            const error = videoEl.error;
            if (error) {
              console.error('[VIDEO] Error code:', error.code);
              console.error('[VIDEO] Error message:', error.message);
            }
            setError(`Video failed to load. Error: ${error?.message || 'Unknown error'}. The video file may be corrupted or in an unsupported format. Please try compiling a new video.`);
          }}
          onLoadedMetadata={() => {
            setError(null); // Clear error if fallback works
          }}
        >
          Your browser does not support the video tag.
        </video>
        <div className="mt-4 flex flex-wrap gap-3">
          {onRecompile && (
            <button
              onClick={onRecompile}
              className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors inline-flex items-center space-x-2"
            >
              <span>Rebuild</span>
              <span>Recompile Video with New Settings</span>
            </button>
          )}
          {videoDataUrl && (
            <a
              href={videoDataUrl}
              download={`video-${projectId || 'download'}.mp4`}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors inline-flex items-center space-x-2"
            >
              <span>Download</span>
              <span>Try Downloading Video Instead</span>
            </a>
          )}
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="mb-4">
        {blobUrl ? (
          <video
            ref={videoRef}
            controls
            controlsList="nodownload"
            className="w-full rounded-lg"
            src={blobUrl}
            preload="auto"
            onError={(e) => {
              const videoEl = e.currentTarget;
              const error = videoEl.error;
              console.error('[VIDEO] Video element error:', error);
              console.error('[VIDEO] Error code:', error?.code);
              console.error('[VIDEO] Error message:', error?.message);
              
              let errorMsg = 'Video failed to play. ';
              if (error) {
                switch (error.code) {
                  case MediaError.MEDIA_ERR_ABORTED:
                    errorMsg += 'Playback was aborted.';
                    break;
                  case MediaError.MEDIA_ERR_NETWORK:
                    errorMsg += 'Network error occurred.';
                    break;
                  case MediaError.MEDIA_ERR_DECODE:
                    errorMsg += 'Video decoding failed. The file may be corrupted or use an unsupported codec.';
                    break;
                  case MediaError.MEDIA_ERR_SRC_NOT_SUPPORTED:
                    errorMsg += 'Video format not supported by your browser.';
                    break;
                  default:
                    errorMsg += `Error code: ${error.code}`;
                }
              }
              setError(errorMsg);
            }}
            onLoadedMetadata={() => {
              const video = videoRef.current;
              if (video) {
              }
            }}
            onCanPlay={() => {
            }}
            onLoadedData={() => {
              // Intentionally left minimal: metadata and buffering handlers maintain playback stability.
            }}
            onProgress={() => {
              // Enable seeking as video buffers
              const video = videoRef.current;
              if (video && video.buffered.length > 0) {
                const bufferedEnd = video.buffered.end(video.buffered.length - 1);
                const duration = video.duration;
                if (bufferedEnd > 0 && duration > 0) {
                  const bufferedPercent = (bufferedEnd / duration) * 100;
                  if (bufferedPercent > 10) {
                    // Once 10% is buffered, seeking should work
                  }
                }
              }
            }}
          >
            Your browser does not support the video tag.
          </video>
        ) : (
          <div className="w-full aspect-video bg-slate-200 rounded-lg flex items-center justify-center">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-slate-600">Loading video...</p>
            </div>
          </div>
        )}
      </div>
      <div className="flex justify-center">
        <button
          onClick={handleDownload}
          disabled={!blobUrl}
          className="bg-green-600 hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed text-white px-6 py-3 rounded-lg font-semibold transition-colors inline-flex items-center space-x-2"
        >
          <span>Download</span>
          <span>Download Video</span>
        </button>
      </div>
    </>
  );
}

type Video = {
  id: string;
  project_id: string;
  video_data_url?: string;
  video_url?: string;
  status: string;
  created_at?: string;
};

export default function VideoPage() {
  return (
    <Suspense
      fallback={(
        <main className="min-h-screen bg-slate-50">
          <div className="container mx-auto px-4 py-8">
            <div className="max-w-6xl mx-auto">
              <div className="bg-white rounded-lg border border-slate-200 p-8 text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                <p className="mt-4 text-slate-600">Loading video...</p>
              </div>
            </div>
          </div>
        </main>
      )}
    >
      <VideoPageContent />
    </Suspense>
  );
}

function VideoPageContent() {
  const searchParams = useSearchParams();
  const supabase = React.useMemo(() => createClient(), []);
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
            // Use video_data_url if available (old format), otherwise use video_url (new format)
            let videoUrl = videoData.video.video_data_url;
            
            if (!videoUrl && videoData.video.video_url) {
              // New format: use Next.js API route to proxy the video file
              videoUrl = `/api/video/file/${videoData.video.id}`;
            }
            
            if (videoUrl) {
              setVideo({
                ...videoData.video,
                video_data_url: videoUrl
              });
            } else {
            }
          }
        }

        setLoading(false);
      } catch (e: unknown) {
        console.error('Error loading video page:', e);
        setError(getErrorMessage(e, 'Failed to load page'));
        setLoading(false);
      }
    }
    load();
  }, [searchParams, supabase]);

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


      // Video compilation can take a while, so set a longer timeout
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 300000); // 5 minutes timeout
      
      const resp = await fetch('/api/video/compile', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({ project_id: projectId }),
        signal: controller.signal,
      }).catch((fetchError) => {
        clearTimeout(timeoutId);
        console.error('[VIDEO] Fetch error:', fetchError);
        
        if (fetchError.name === 'AbortError') {
          throw new Error('Video compilation timed out. Please try again or check if the backend is processing your request.');
        }
        
        // Check if backend is reachable
        if (fetchError.message.includes('Failed to fetch') || fetchError.message.includes('ECONNREFUSED')) {
          throw new Error('Could not connect to the backend API. Please make sure the FastAPI server is running on port 8000.');
        }
        
        throw new Error(`Network error: ${fetchError.message}`);
      });
      
      clearTimeout(timeoutId);

      const responseText = await resp.text();
      
      if (!resp.ok) {
        let errorMsg = responseText;
        try {
          const errorJson = JSON.parse(responseText);
          errorMsg = errorJson.error || errorJson.detail || responseText;
        } catch {}
        throw new Error(errorMsg || `HTTP ${resp.status}`);
      }

      const data = JSON.parse(responseText);
      if (data.success && data.video_id) {
        // Fetch the video data separately since it's too large to return in compile response
        const videoFetchRes = await fetch(`/api/video/project/${projectId}`, {
          headers: { Authorization: `Bearer ${session.access_token}` },
          cache: 'no-store'
        });
        
        if (!videoFetchRes.ok) {
          throw new Error('Video compiled but failed to fetch video data');
        }
        
        const videoData = await videoFetchRes.json();
        if (videoData.video) {
          // Use video_data_url if available (old format), otherwise use video_url (new format)
          let videoUrl = videoData.video.video_data_url;
          
          if (!videoUrl && videoData.video.video_url) {
            // New format: use Next.js API route to proxy the video file
            videoUrl = `/api/video/file/${data.video_id}`;
          }
          
          if (videoUrl) {
            setVideo({
              id: data.video_id,
              project_id: projectId,
              video_data_url: videoUrl,
              video_url: videoData.video.video_url,
              status: 'completed',
            });
          } else {
            throw new Error('Video compiled but video URL not found');
          }
        } else {
          throw new Error('Video compiled but video data not found');
        }
      } else {
        throw new Error('Video compilation failed');
      }
    } catch (e: unknown) {
      console.error('[VIDEO] Error compiling video:', e);
      setError(getErrorMessage(e, 'Failed to compile video. Check the browser console for details.'));
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
            <h1 className="text-3xl font-bold text-slate-900 mb-6">Video Compilation</h1>
            <div className="bg-white rounded-lg border border-slate-200 p-8 text-center">
              <div className="text-5xl mb-4">Video</div>
              <h2 className="text-xl font-semibold text-slate-900 mb-2">No Project Selected</h2>
              <p className="text-slate-600 mb-6">
                To compile a video, please continue from the images page.
              </p>
              <Link
                href="/"
                className="inline-block bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors"
              >
                Go to Home
              </Link>
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
          <h1 className="text-3xl font-bold text-slate-900 mb-6">Video Compilation</h1>

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

              {/* Compile button - show if no video or video has no URL */}
              {(!video || !video.video_data_url) && (
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
                  <div className="flex items-center justify-between mb-4">
                    <h2 className="text-lg font-semibold text-slate-900">Compiled Video</h2>
                    <button
                      onClick={onCompile}
                      disabled={compiling || !hasScript || !hasVoiceover || !hasImages}
                      className="bg-purple-600 hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors inline-flex items-center space-x-2"
                    >
                      <span>Rebuild</span>
                      <span>{compiling ? 'Recompiling...' : 'Recompile Video'}</span>
                    </button>
                  </div>
                  <VideoPlayer 
                    videoDataUrl={video.video_data_url} 
                    projectId={projectId}
                    onRecompile={onCompile}
                  />
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </main>
  );
}
