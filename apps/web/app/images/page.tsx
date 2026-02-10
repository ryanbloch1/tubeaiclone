'use client';
import React, { Suspense } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { useSearchParams, useRouter } from 'next/navigation';
import { createClient } from '@/lib/supabase/client';

type DbImage = {
  id: string;
  scene_id?: string;
  image_data_url?: string | null;
  prompt?: string;
  styled_prompt?: string;
  scene_number?: number;
  status?: string;
  source_type?: 'generated' | 'uploaded';
  created_at?: string
};

const getErrorMessage = (error: unknown, fallback: string) => {
  if (error instanceof Error) {
    return error.message;
  }
  return fallback;
};

export default function ImagesPage() {
  return (
    <Suspense
      fallback={(
        <main className="min-h-screen bg-slate-50">
          <div className="container mx-auto px-4 py-8">
            <div className="max-w-6xl mx-auto">
              <div className="bg-white rounded-lg border border-slate-200 p-8 text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                <p className="mt-4 text-slate-600">Loading images...</p>
              </div>
            </div>
          </div>
        </main>
      )}
    >
      <ImagesPageContent />
    </Suspense>
  );
}

function ImagesPageContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const supabase = React.useMemo(() => createClient(), []);
  const [projectId, setProjectId] = React.useState<string | null>(null);
  const [scriptId, setScriptId] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState<boolean>(true);
  const [error, setError] = React.useState<string | null>(null);
  const [images, setImages] = React.useState<DbImage[]>([]);
  const [generating, setGenerating] = React.useState<boolean>(false);
  const [regeneratingIds, setRegeneratingIds] = React.useState<Set<string>>(new Set());
  const [additionalPrompts, setAdditionalPrompts] = React.useState<Record<string, string>>({});
  const [expandedIds, setExpandedIds] = React.useState<Set<string>>(new Set());
  const [styleName, setStyleName] = React.useState<string | null>(null);
  const [expectedSceneCount, setExpectedSceneCount] = React.useState<number | null>(null);
  const [originalBasePrompts, setOriginalBasePrompts] = React.useState<Record<string, string>>({});
  const [uploadingScenes, setUploadingScenes] = React.useState<Set<number>>(new Set());

  React.useEffect(() => {
    const pid = searchParams.get('projectId');
    setProjectId(pid);
    async function load() {
      if (!pid) {
        setLoading(false);
        setError('No project ID provided');
        return;
      }
      // When (re)loading the page, ensure we are in a "loading from DB" state,
      // not a "generating" state. This prevents tiles from saying "Generating..."
      // when we're just fetching existing images.
      setGenerating(false);
      setLoading(true);
      setError(null);
      try {
        const { data: { session } } = await supabase.auth.getSession();
        if (!session) {
          setLoading(false);
          setError('Not authenticated');
          return;
        }

        // Fetch project + script
        const projRes = await fetch(`/api/projects/${pid}`, {
          headers: { Authorization: `Bearer ${session.access_token}` },
          cache: 'no-store'
        });
        if (projRes.ok) {
          const data = await projRes.json();
          const script = data?.script;
          const project = data?.project;
          if (project?.style) {
            setStyleName(project.style);
          } else {
            setStyleName('Photorealistic');
          }
          if (script?.id) {
            setScriptId(script.id);
            // Parse script to count scenes
            const scriptText = script.edited_script || script.raw_script || '';
            if (scriptText) {
              const sceneMatches = scriptText.match(/^Scene\s+\d+/gim);
              const sceneCount = sceneMatches ? sceneMatches.length : 0;
              setExpectedSceneCount(sceneCount > 0 ? sceneCount : null);
            }
          }
        } else {
          console.error('Failed to load project:', projRes.status, await projRes.text().catch(() => ''));
        }

        // Fetch images
        const imgRes = await fetch(`/api/images/project/${pid}`, {
          headers: { Authorization: `Bearer ${session.access_token}` },
          cache: 'no-store'
        });
        if (!imgRes.ok) {
          const errorText = await imgRes.text().catch(() => 'Unknown error');
          console.error('Failed to load images:', imgRes.status, errorText);
          setError(`Failed to load images: ${imgRes.status}`);
          setLoading(false);
          return;
        }
        const imgData = await imgRes.json();
        
        // Defensive check: ensure images is an array
        const fetchedImages = Array.isArray(imgData.images) ? imgData.images : [];
        
        // Filter out images without image_data_url (incomplete images)
        const validImages = fetchedImages.filter((img: DbImage) => img.image_data_url);
        
        // Set images state first
        setImages(validImages);
        
        if (validImages.length > 0) {
          // Store original base prompts for each image
          const basePrompts: Record<string, string> = {};
          validImages.forEach((img: DbImage) => {
            if (img.id && img.styled_prompt) {
              basePrompts[img.id] = img.styled_prompt;
            }
          });
          setOriginalBasePrompts(prev => ({ ...prev, ...basePrompts }));
          
          // Set additional prompts state
          setAdditionalPrompts(prev => {
            const next = { ...prev };
            validImages.forEach((img: DbImage) => {
              if (img.id && !(img.id in next)) {
                next[img.id] = '';
              }
            });
            return next;
          });
        }
        
        // Set loading to false after images state is set
        // React will batch these updates, but this ensures images are set before loading completes
        setLoading(false);
      } catch (e: unknown) {
        console.error('Error loading images page:', e);
        setError(getErrorMessage(e, 'Failed to load page'));
        setLoading(false);
      }
    }
    load();
  }, [searchParams, supabase]);

  const onUploadPhoto = async (sceneNumber: number, file: File) => {
    try {
      setUploadingScenes(prev => new Set(prev).add(sceneNumber));
      setError(null);
      
      const { data: { session } } = await supabase.auth.getSession();
      if (!session || !projectId) {
        setError('Not authenticated or no project ID');
        return;
      }

      // Convert file to base64
      const reader = new FileReader();
      reader.onloadend = async () => {
        try {
          const base64Data = (reader.result as string).split(',')[1]; // Remove data:image/...;base64, prefix
          
          const resp = await fetch('/api/images/upload', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              Authorization: `Bearer ${session.access_token}`,
            },
            body: JSON.stringify({
              project_id: projectId,
              scene_number: sceneNumber,
              image_data: base64Data,
              image_filename: file.name,
            }),
          });

          if (!resp.ok) {
            const errorData = await resp.json().catch(() => ({ error: 'Upload failed' }));
            throw new Error(errorData.error || `HTTP ${resp.status}`);
          }

          await resp.json();
          
          // Reload images to show the uploaded photo
          const imgRes = await fetch(`/api/images/project/${projectId}`, {
            headers: { Authorization: `Bearer ${session.access_token}` },
            cache: 'no-store'
          });
          
          if (imgRes.ok) {
            const imgData = await imgRes.json();
            const fetchedImages = Array.isArray(imgData.images) ? imgData.images : [];
            const validImages = fetchedImages.filter((img: DbImage) => img.image_data_url);
            setImages(validImages);
            
            // Update original base prompts for new images
            const basePrompts: Record<string, string> = {};
            validImages.forEach((img: DbImage) => {
              if (img.id && img.styled_prompt) {
                basePrompts[img.id] = img.styled_prompt;
              }
            });
            setOriginalBasePrompts(prev => ({ ...prev, ...basePrompts }));
          }
          
        } catch (e: unknown) {
          console.error('Error uploading photo:', e);
          setError(getErrorMessage(e, 'Failed to upload photo'));
        } finally {
          setUploadingScenes(prev => {
            const next = new Set(prev);
            next.delete(sceneNumber);
            return next;
          });
        }
      };
      
      reader.readAsDataURL(file);
      
    } catch (e: unknown) {
      console.error('Error setting up photo upload:', e);
      setError(getErrorMessage(e, 'Failed to upload photo'));
      setUploadingScenes(prev => {
        const next = new Set(prev);
        next.delete(sceneNumber);
        return next;
      });
    }
  };

  const onRegenerateImage = async (imageId: string, promptOverride?: string) => {
    try {
      setRegeneratingIds(prev => new Set(prev).add(imageId));
      setError(null);
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) {
        setError('Not authenticated');
        return;
      }

      const resp = await fetch('/api/images/regenerate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${session.access_token}` },
        body: JSON.stringify({ image_id: imageId, prompt: promptOverride })
      });

      const responseText = await resp.text();
      if (!resp.ok) {
        let errorMsg = responseText;
        try {
          const errorJson = JSON.parse(responseText);
          errorMsg = errorJson.error || errorJson.detail || responseText;
        } catch { }
        throw new Error(errorMsg || `HTTP ${resp.status}`);
      }

      const data = JSON.parse(responseText);
      const updatedImage = data.image;

      // Update the image in the list (preserve original base prompt to prevent duplication)
      // Always use the stored original base prompt, never update it from backend response
      const originalBase = originalBasePrompts[imageId];
      if (!originalBase && updatedImage.styled_prompt) {
        // First time seeing this image - store its base prompt
        setOriginalBasePrompts(prev => ({
          ...prev,
          [imageId]: updatedImage.styled_prompt
        }));
      }

      setImages(prev => prev.map(img => {
        if (img.id !== imageId) return img;
        return {
          ...img,
          ...updatedImage,
          prompt: img.prompt, // keep narration display
          styled_prompt: originalBase || img.styled_prompt || updatedImage.styled_prompt // always use original, never update
        };
      }));

      // Clear the additional prompt for this image after successful regeneration
      setAdditionalPrompts(prev => {
        const next = { ...prev };
        delete next[imageId];
        return next;
      });
    } catch (e: unknown) {
      console.error('Error regenerating image:', e);
      setError(getErrorMessage(e, 'Failed to regenerate image'));
    } finally {
      setRegeneratingIds(prev => {
        const newSet = new Set(prev);
        newSet.delete(imageId);
        return newSet;
      });
    }
  };

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const onGenerate = async () => {
    try {
      setGenerating(true);
      setError(null);
      // Clear existing images when starting new generation
      // New images will replace them as they stream in
      setImages([]);

      // Parse script to get scene count if not already known
      if (!expectedSceneCount && scriptId) {
        const { data: { session } } = await supabase.auth.getSession();
        if (session) {
          const projRes = await fetch(`/api/projects/${projectId}`, {
            headers: { Authorization: `Bearer ${session.access_token}` },
            cache: 'no-store'
          });
          if (projRes.ok) {
            const data = await projRes.json();
            const script = data?.script;
            const scriptText = script?.edited_script || script?.raw_script || '';
            if (scriptText) {
              const sceneMatches = scriptText.match(/^Scene\s+\d+/gim);
              const sceneCount = sceneMatches ? sceneMatches.length : 0;
              setExpectedSceneCount(sceneCount > 0 ? sceneCount : null);
            }
            const project = data?.project;
            if (project?.style) {
              setStyleName(project.style);
            }
          }
        }
      }

      const { data: { session } } = await supabase.auth.getSession();
      if (!session || !projectId) {
        setError('Not authenticated or no project ID');
        setGenerating(false);
        return;
      }
      if (!scriptId) {
        setError('No script found. Please generate a script first.');
        setGenerating(false);
        return;
      }


      // Use fetch with streaming response
      const resp = await fetch('/api/images/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${session.access_token}`,
          Accept: 'text/event-stream'
        },
        body: JSON.stringify({
          project_id: projectId,
          script_id: scriptId,
          style_name: styleName || 'Photorealistic'
        })
      });

      if (!resp.ok) {
        const errorText = await resp.text();
        let errorMsg = errorText;
        try {
          const errorJson = JSON.parse(errorText);
          errorMsg = errorJson.error || errorJson.detail || errorText;
        } catch { }
        throw new Error(errorMsg || `HTTP ${resp.status}`);
      }

      // Read streaming response
      const reader = resp.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('No response body');
      }

      let buffer = '';
      const newImages: DbImage[] = [];

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // Keep incomplete line in buffer

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.type === 'image' && data.image) {
                // Add image to list and update UI (replace loader with actual image)
                newImages.push(data.image);
                setImages([...newImages]); // Update state with new image
              } else if (data.type === 'complete') {
                // Generation complete - use final list from server
                setImages(data.images || newImages);
                setExpectedSceneCount(null); // Clear expected count

                // Update project status
                try {
                  await fetch(`/api/projects/${projectId}`, {
                    method: 'PUT',
                    headers: {
                      'Content-Type': 'application/json',
                      Authorization: `Bearer ${(await supabase.auth.getSession()).data.session?.access_token}`
                    },
                    body: JSON.stringify({ status: 'images' })
                  });
                } catch (e) {
                  console.warn('Failed to update project status:', e);
                }
              }
            } catch (e) {
              console.warn('Failed to parse SSE data:', e, line);
            }
          }
        }
      }

      if (newImages.length === 0) {
        throw new Error('No images generated');
      }

    } catch (e: unknown) {
      console.error('Error generating images:', e);
      setError(getErrorMessage(e, 'Failed to generate images. Check the browser console for details.'));
    } finally {
      setGenerating(false);
    }
  };

  // Show helpful message if no project ID
  if (!projectId && !loading) {
    return (
      <main className="min-h-screen bg-slate-50">
        <div className="container mx-auto px-4 py-8">
          <div className="max-w-6xl mx-auto">
            <h1 className="text-3xl font-bold text-slate-900 mb-6">Images</h1>
            <div className="bg-white rounded-lg border border-slate-200 p-8 text-center">
              <div className="text-5xl mb-4">Image</div>
              <h2 className="text-xl font-semibold text-slate-900 mb-2">No Project Selected</h2>
              <p className="text-slate-600 mb-6">
                To generate images, please start or continue a project from the home page.
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
          <h1 className="text-3xl font-bold text-slate-900 mb-6">📸 Property Photos</h1>

          {!loading && (
            <div className="bg-white rounded-lg border border-slate-200 p-6 shadow-sm mb-6">
              <h2 className="text-lg font-semibold text-slate-900 mb-2">
                Upload photos for each scene
              </h2>
              <p className="text-slate-600 text-sm">
                This tool now relies on your own property photos. Click on any scene card below to upload a photo that will be used in the final video.
              </p>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
              <p className="text-red-700 text-sm">{error}</p>
            </div>
          )}

          {loading ? (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {Array.from({ length: 8 }).map((_, i) => (
                <div key={i} className="aspect-video bg-slate-200 animate-pulse rounded" />
              ))}
            </div>
          ) : !loading && images.length === 0 ? (
            <div className="text-center py-16 bg-white border border-dashed border-slate-300 rounded-lg">
              <div className="text-5xl mb-3">Image</div>
              <h3 className="text-lg font-semibold text-slate-900 mb-2">No photos yet</h3>
              <p className="text-slate-600 mb-2">
                Upload at least one photo for each scene in your script. These photos will be used when compiling the final video.
              </p>
              <p className="text-slate-500 text-sm">
                Use the &quot;Upload Photo&quot; button on each scene card below once scenes appear here.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {/* Show loader tiles for expected scenes, then replace with actual images */}
              {Array.from({ length: expectedSceneCount || images.length || 8 }).map((_, index) => {
                const sceneNumber = index + 1;
                const image = images.find(img => img.scene_number === sceneNumber);

                return (
                  <div key={image?.id || `loader-${sceneNumber}`} className="bg-white border border-slate-200 rounded-lg overflow-hidden shadow-sm relative group">
                    {(() => {
                      if (image?.image_data_url) {
                        return (
                          <Image
                            src={image.image_data_url}
                            alt={image.prompt || `Scene ${image.scene_number || sceneNumber}`}
                            width={1280}
                            height={720}
                            unoptimized
                            className="w-full h-auto"
                          />
                        );
                      }
                      if (generating) {
                        return (
                          <div className="aspect-video bg-slate-100 flex items-center justify-center">
                            <div className="flex flex-col items-center gap-2">
                              <div className="h-8 w-8 rounded-full border-4 border-slate-200 border-t-blue-500 animate-spin" />
                              <div className="text-slate-400 text-xs">Scene {sceneNumber}</div>
                              <div className="text-slate-400 text-xs">Generating…</div>
                            </div>
                          </div>
                        );
                      }
                      return (
                        <div className="aspect-video bg-slate-200 animate-pulse flex items-center justify-center">
                          <div className="text-center">
                            <div className="text-slate-400 text-xs mb-1">Scene {sceneNumber}</div>
                            <div className="text-slate-400 text-xs">Loading…</div>
                          </div>
                        </div>
                      );
                    })()}
                    {/* Upload/Regenerate buttons - shows on hover when image exists */}
                    {image?.image_data_url && (
                      <div className="absolute top-2 right-2 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                        <label className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-3 py-1.5 rounded-lg text-xs font-medium cursor-pointer disabled:cursor-not-allowed">
                          Upload Photo
                          <input
                            type="file"
                            accept="image/*"
                            className="hidden"
                            onChange={(e) => {
                              const file = e.target.files?.[0];
                              if (file && image.scene_number) {
                                onUploadPhoto(image.scene_number, file);
                              }
                            }}
                            disabled={uploadingScenes.has(image.scene_number || 0)}
                          />
                        </label>
                        <button
                          onClick={() => {
                            const basePrompt = originalBasePrompts[image.id] || image.styled_prompt || 'Photorealistic cinematic lighting, ultra-detailed.';
                            const addition = additionalPrompts[image.id] || '';
                            const combinedPrompt = [basePrompt, addition.trim()].filter(Boolean).join(' ');
                            onRegenerateImage(image.id, combinedPrompt || basePrompt);
                          }}
                          disabled={regeneratingIds.has(image.id)}
                          className="bg-black/70 hover:bg-black/90 disabled:opacity-50 text-white px-3 py-1.5 rounded-lg text-xs font-medium disabled:cursor-not-allowed"
                          title="Regenerate this image"
                        >
                          {regeneratingIds.has(image.id) ? 'Generating...' : 'Regenerate'}
                        </button>
                      </div>
                    )}
                    {/* Upload button for scenes without images */}
                    {!image?.image_data_url && !generating && (
                      <label className="absolute inset-0 flex items-center justify-center bg-slate-900/50 hover:bg-slate-900/70 text-white cursor-pointer opacity-0 group-hover:opacity-100 transition-opacity">
                        <div className="text-center">
                          <div className="text-2xl mb-1">Upload</div>
                          <div className="text-xs font-medium">Upload Photo</div>
                        </div>
                        <input
                          type="file"
                          accept="image/*"
                          className="hidden"
                          onChange={(e) => {
                            const file = e.target.files?.[0];
                            if (file) {
                              onUploadPhoto(sceneNumber, file);
                            }
                          }}
                          disabled={uploadingScenes.has(sceneNumber)}
                        />
                      </label>
                    )}
                    {uploadingScenes.has(sceneNumber) && (
                      <div className="absolute inset-0 flex items-center justify-center bg-slate-900/70 text-white">
                        <div className="text-center">
                          <div className="h-8 w-8 rounded-full border-4 border-white/30 border-t-white animate-spin mx-auto mb-2" />
                          <div className="text-xs">Uploading...</div>
                        </div>
                      </div>
                    )}
                    {(image?.scene_number || image?.prompt) && (
                      <div className="p-2 bg-slate-50 border-t border-slate-200">
                        {image.scene_number && (
                          <div className="flex items-center justify-between mb-1">
                            <div className="text-xs font-semibold text-slate-600">Scene {image.scene_number}</div>
                            {image.source_type === 'uploaded' && (
                              <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full font-medium">
                                Uploaded
                              </span>
                            )}
                            {image.source_type === 'generated' && (
                              <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full font-medium">
                                🤖 AI Generated
                              </span>
                            )}
                          </div>
                        )}
                        <button
                          type="button"
                          onClick={() => {
                            setExpandedIds(prev => {
                              const next = new Set(prev);
                              if (image?.id) {
                                if (next.has(image.id)) {
                                  next.delete(image.id);
                                } else {
                                  next.add(image.id);
                                }
                              }
                              return next;
                            });
                          }}
                          className="text-xs text-blue-600 hover:text-blue-700 font-medium mb-2"
                        >
                          {expandedIds.has(image?.id || '') ? 'Hide prompt editor' : 'Edit prompt details'}
                        </button>
                        {expandedIds.has(image?.id || '') && image?.id && (
                          <div className="space-y-2">
                            <div className="text-xs text-slate-500">
                              Base prompt:
                              <div className="mt-1 text-slate-600 bg-white border border-slate-200 rounded p-2">
                                {originalBasePrompts[image.id] || image.styled_prompt || 'Photorealistic cinematic lighting, ultra-detailed.'}
                              </div>
                            </div>
                            <textarea
                              className="w-full text-xs border border-black rounded-lg px-2 py-2 bg-white text-black resize-y focus:border-black focus:ring-2 focus:ring-black focus:ring-opacity-20 transition"
                              rows={3}
                              value={additionalPrompts[image.id] ?? ''}
                              onChange={(e) => {
                                const val = e.target.value;
                                setAdditionalPrompts(prev => ({
                                  ...prev,
                                  [image.id]: val
                                }));
                              }}
                              placeholder="Add more details to guide the regenerated image..."
                            />
                            <button
                              type="button"
                              onClick={() => {
                                const basePrompt = originalBasePrompts[image.id] || image.styled_prompt || 'Photorealistic cinematic lighting, ultra-detailed.';
                                const addition = additionalPrompts[image.id] || '';
                                const combinedPrompt = [basePrompt, addition.trim()].filter(Boolean).join(' ');
                                onRegenerateImage(image.id, combinedPrompt || basePrompt);
                              }}
                              disabled={regeneratingIds.has(image.id)}
                              className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors"
                            >
                              {regeneratingIds.has(image.id) ? 'Regenerating...' : 'Apply & Regenerate'}
                            </button>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}

          {/* Continue to Video button */}
          {images.length > 0 && !generating && (
            <div className="mt-6 flex justify-center">
              <button
                onClick={() => {
                  if (projectId) {
                    router.push(`/video?projectId=${projectId}`);
                  } else {
                    router.push('/video');
                  }
                }}
                className="bg-purple-600 hover:bg-purple-700 text-white px-8 py-3 rounded-lg font-semibold transition-colors flex items-center space-x-2"
              >
                <span>Video</span>
                <span>Continue to Video Compilation</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
