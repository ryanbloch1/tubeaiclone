"use client";
import React, { useCallback } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { useVideoStore } from "@/lib/store";

// Simple debounce utility for prompt edits
function debounce<T extends (...args: never[]) => void>(fn: T, delay: number) {
  let timer: ReturnType<typeof setTimeout> | null = null;
  return (...args: Parameters<T>) => {
    if (timer) clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
}

type Scene = {
  scene_number: number;
  text: string;
  description: string;
};


export default function ImagesPage() {
  const router = useRouter();
  const hydrated = useVideoStore(s => s.hydrated);
  const setImagesState = useVideoStore(s => s.setImagesState);
  const cameFromVoiceover = useVideoStore(s => s.cameFromVoiceover);
  const originalScript = useVideoStore(s => s.editableScript); // use original full script
  const scenes = useVideoStore(s => s.scenes);
  const images = useVideoStore(s => s.images);
  const generating = useVideoStore(s => s.generating);
  const currentScene = useVideoStore(s => s.currentScene);

  // Generate image prompt using Gemini API
  const generateScenePrompt = useCallback(async (sceneText: string, sceneNumber: number): Promise<string> => {
    try {
      const response = await fetch('/api/images/prompt', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          scene_text: sceneText,
          scene_number: sceneNumber
        })
      });

      if (response.ok) {
        const result = await response.json();
        return result.prompt;
      } else {
        throw new Error('Failed to generate prompt');
      }
    } catch (error) {
      console.error('Error generating prompt:', error);
      // Fallback to simple prompt
      return `cinematic shot of ${sceneText.slice(0, 100)}... professional documentary style, high quality`;
    }
  }, []);

  // Initialize scenes from the stored script on first hydrated mount
  // Only create scenes, NOT placeholder images - images are created only when generation starts
  React.useEffect(() => {
    if (!hydrated) return;
    
    // Always ensure generating state is false when page loads
    if (generating) {
      setImagesState({ generating: false, currentScene: null });
    }
    
    // Only parse scenes if we don't have them yet
    if (scenes.length === 0 && originalScript && originalScript.trim().length > 0) {
      const parsedScenes = parseScriptIntoScenes(originalScript);
      setImagesState({
        scenes: parsedScenes,
        images: [], // Start with empty images array - no placeholders!
        cameFromVoiceover: true,
        generating: false,
        currentScene: null
      });
    }
    
    // Clean up any stale "generating" statuses from a previous session/navigation
    if (images.some((img) => img.status === 'generating')) {
      setImagesState((s) => ({
        images: s.images.map((img) =>
          img.status === 'generating' ? { ...img, status: 'pending' } : img
        ),
      }));
    }
  }, [hydrated, originalScript, scenes.length, setImagesState, generating, images]);

  const parseScriptIntoScenes = (script: string): Scene[] => {
    const lines = script.split('\n');
    const scenes: Scene[] = [];
    let currentScene: Scene | null = null;

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed) continue;

      // Check for scene markers
      const sceneMatch = trimmed.match(/^Scene\s+(\d+)/i);
      if (sceneMatch) {
        // Save previous scene
        if (currentScene) {
          scenes.push(currentScene);
        }
        // Start new scene
        currentScene = {
          scene_number: parseInt(sceneMatch[1]),
          text: trimmed,
          description: trimmed
        };
      } else if (currentScene) {
        // Add to current scene
        currentScene.text += '\n' + trimmed;
      }
    }

    // Add final scene
    if (currentScene) {
      scenes.push(currentScene);
    }

    return scenes;
  };

  const generateAllImages = async () => {
    if (scenes.length === 0) return;
    
    setImagesState({ generating: true });
    
    // Process scenes sequentially, one at a time
    for (let i = 0; i < scenes.length; i++) {
      const scene = scenes[i];
      
      // Skip if already completed
      const existingImage = images.find(img => img.scene_number === scene.scene_number);
      if (existingImage?.status === 'completed') {
        continue;
      }
      
      setImagesState({ currentScene: scene.scene_number });
      
      // Create image entry if it doesn't exist
      let imageEntry = existingImage;
      if (!imageEntry) {
        // Generate prompt using Gemini API
        const prompt = await generateScenePrompt(scene.text, scene.scene_number);
        imageEntry = {
          scene_number: scene.scene_number,
          prompt: prompt,
          status: 'pending' as const
        };
        
        setImagesState((s) => ({
          images: [...s.images, imageEntry!]
        }));
      }
      
      // Update status to generating
      setImagesState((s) => ({
        images: s.images.map((img) =>
          img.scene_number === scene.scene_number
            ? { ...img, status: 'generating' }
            : img
        ),
      }));

      try {
        const response = await fetch('/api/images/generate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            prompt: imageEntry.prompt,
            scene_number: scene.scene_number
          })
        });

        if (response.ok) {
          const result = await response.json();
          setImagesState((s) => ({
            images: s.images.map((img) =>
              img.scene_number === scene.scene_number
                ? { ...img, status: 'completed', image_url: result.image_url }
                : img
            ),
          }));
        } else {
          throw new Error('Generation failed');
        }
      } catch {
        setImagesState((s) => ({
          images: s.images.map((img) =>
            img.scene_number === scene.scene_number
              ? { ...img, status: 'failed', error: 'Generation failed' }
              : img
          ),
        }));
      }

      // Small delay between generations to show progress
      await new Promise(resolve => setTimeout(resolve, 1000));
    }

    setImagesState({ currentScene: null, generating: false });
  };

  // Generate a single scene image on demand
  const generateSingleImage = async (sceneNumber: number) => {
    const scene = scenes.find(s => s.scene_number === sceneNumber);
    if (!scene) return;
    
    setImagesState({ currentScene: sceneNumber });
    
    // Create image entry if it doesn't exist
    let existingImage = images.find(img => img.scene_number === sceneNumber);
    if (!existingImage) {
      // Generate prompt using Gemini API
      const prompt = await generateScenePrompt(scene.text, sceneNumber);
      const newImage = {
        scene_number: sceneNumber,
        prompt: prompt,
        status: 'pending' as const
      };
      setImagesState((s) => ({
        images: [...s.images, newImage]
      }));
      existingImage = newImage;
    }
    
    // Update status to generating
    setImagesState((s) => ({
      images: s.images.map((img) =>
        img.scene_number === sceneNumber ? { ...img, status: 'generating' } : img
      ),
    }));
    
    try {
      const response = await fetch('/api/images/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: existingImage.prompt,
          scene_number: sceneNumber
        })
      });
      if (response.ok) {
        const result = await response.json();
        setImagesState((s) => ({
          images: s.images.map((img) =>
            img.scene_number === sceneNumber
              ? { ...img, status: 'completed', image_url: result.image_url }
              : img
          ),
        }));
      } else {
        throw new Error('Generation failed');
      }
    } catch {
      setImagesState((s) => ({
        images: s.images.map((img) =>
          img.scene_number === sceneNumber
            ? { ...img, status: 'failed', error: 'Generation failed' }
            : img
        ),
      }));
    } finally {
      setImagesState({ currentScene: null });
    }
  };

  // Debounced prompt setter to reduce write frequency
  const debouncedSetPrompt = React.useMemo(
    () =>
      debounce((sceneNumber: number, value: string) => {
        setImagesState((s) => ({
          images: s.images.map((img) =>
            img.scene_number === sceneNumber ? { ...img, prompt: value } : img
          ),
        }));
      }, 400),
    [setImagesState]
  );

  const completedImages = images.filter(img => img.status === 'completed').length;
  const pendingOrFailed = images.filter(img => img.status === 'pending' || img.status === 'failed').length;
  const totalImages = images.length;

  return (
    <main className="min-h-screen bg-slate-50">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-6xl mx-auto">
          <div className="flex items-center justify-between mb-8">
            <button
              onClick={() => router.push("/voiceover")}
              className="bg-slate-100 hover:bg-slate-200 text-slate-700 px-4 py-2 rounded-lg font-medium transition-colors flex items-center space-x-2"
            >
              <span>←</span>
              <span>Back to Voiceover</span>
            </button>
            <h1 className="text-4xl font-bold text-slate-900">
              🎬 Scene Image Generation
            </h1>
            <div className="w-40"></div> {/* Spacer for centering */}
          </div>

          {cameFromVoiceover && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
              <div className="flex items-center">
                <span className="text-green-600 mr-2">✅</span>
                <p className="text-green-700 text-sm">
                  Script loaded successfully! Ready to generate scene images.
                </p>
              </div>
            </div>
          )}

          {scenes.length === 0 ? (
            <div className="bg-white rounded-lg border border-slate-200 p-8 text-center shadow-sm">
              <div className="text-6xl mb-4">🎭</div>
              <h2 className="text-xl font-semibold text-slate-900 mb-2">No Script Loaded</h2>
              <p className="text-slate-600 mb-4">
                You need a script to generate scene images. Start by creating a script first.
              </p>
              <a 
                href="/script" 
                className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors"
              >
                Generate Script
              </a>
            </div>
          ) : (
            <>
              {/* Generation Control */}
              <div className="bg-white rounded-lg border border-slate-200 p-6 shadow-sm mb-6">
                <div className="flex justify-between items-center mb-4">
                  <div>
                    <h2 className="text-xl font-semibold text-slate-900">
                      Scene Analysis Complete
                    </h2>
                    <p className="text-slate-600 text-sm">
                      Found {scenes.length} scenes ready for image generation
                    </p>
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-bold text-blue-600">
                      {completedImages}/{totalImages}
                    </div>
                    <div className="text-sm text-slate-500">Images Ready</div>
                  </div>
                </div>

                {!generating && pendingOrFailed > 0 && (
                  <button
                    onClick={generateAllImages}
                    disabled={scenes.length === 0}
                    className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-8 py-4 rounded-lg font-semibold transition-all duration-200 hover:transform hover:-translate-y-0.5 hover:shadow-lg flex items-center justify-center space-x-2"
                  >
                    <span>🎨</span>
                    <span>{completedImages > 0 ? 'Generate Remaining Images' : 'Generate All Scene Images'}</span>
                  </button>
                )}

                {generating && (
                  <div className="text-center">
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                      <div className="flex items-center justify-center space-x-3">
                        <div className="animate-spin h-6 w-6 border-2 border-blue-600 border-t-transparent rounded-full"></div>
                        <span className="text-blue-700 font-medium">
                          Generating Scene {currentScene} Images...
                        </span>
                      </div>
                      <div className="mt-3 w-full bg-blue-200 rounded-full h-2">
                        <div 
                          className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${(completedImages / totalImages) * 100}%` }}
                        ></div>
                      </div>
                    </div>
                  </div>
                )}

                {completedImages === totalImages && totalImages > 0 && (
                  <div className="text-center">
                    <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                      <div className="flex items-center justify-center space-x-2 mb-3">
                        <span className="text-green-600 text-2xl">🎉</span>
                        <span className="text-green-700 font-semibold">
                          All Scene Images Generated!
                        </span>
                      </div>
                      <button className="bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors flex items-center space-x-2 mx-auto">
                        <span>🎬</span>
                        <span>Assemble Video</span>
                      </button>
                    </div>
                  </div>
                )}
              </div>

              {/* Scene Images Grid */}
              <div className="grid gap-6">
                {images.length > 0 ? (
                  // Show scenes that have image entries (generated or in progress)
                  images.map((image) => {
                    const scene = scenes.find(s => s.scene_number === image.scene_number);
                    return (
                      <div key={image.scene_number} className="bg-white rounded-lg border border-slate-200 p-6 shadow-sm">
                        <div className="flex gap-6">
                          {/* Scene Content */}
                          <div className="flex-1">
                            <div className="flex items-center justify-between mb-3">
                              <h3 className="text-lg font-semibold text-slate-900">
                                Scene {image.scene_number}
                              </h3>
                              <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                                image.status === 'completed' ? 'bg-green-100 text-green-800' :
                                image.status === 'generating' ? 'bg-blue-100 text-blue-800' :
                                image.status === 'failed' ? 'bg-red-100 text-red-800' :
                                'bg-gray-100 text-gray-800'
                              }`}>
                                {image.status === 'completed' && '✅ '}
                                {image.status === 'generating' && '⏳ '}
                                {image.status === 'failed' && '❌ '}
                                {image.status === 'pending' && '⏳ '}
                                {image.status}
                              </span>
                            </div>
                            
                            <div className="mb-4">
                              <p className="text-sm text-slate-600 mb-2">Scene Text:</p>
                              <p className="text-slate-800 text-sm bg-slate-50 p-3 rounded border">
                                {scene?.text.split('\n').slice(0, 3).join(' ') || 'No text available'}
                              </p>
                            </div>

                            <div className="mb-4">
                              <p className="text-sm text-slate-600 mb-2">Generated Prompt:</p>
                              <textarea
                                className="w-full rounded-lg border border-blue-200 bg-blue-50 p-3 text-slate-800 text-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-colors resize-y"
                                rows={3}
                                value={image.prompt}
                                onChange={(e) => {
                                  const value = e.target.value;
                                  // Update UI immediately for responsiveness
                                  setImagesState((s) => ({
                                    images: s.images.map((img) =>
                                      img.scene_number === image.scene_number
                                        ? { ...img, prompt: value }
                                        : img
                                    ),
                                  }));
                                  // Debounced persistence update
                                  debouncedSetPrompt(image.scene_number, value);
                                }}
                              />
                              <p className="text-xs text-slate-500 mt-1">You can edit the prompt before generation to fine-tune the image.</p>
                              <div className="mt-2 flex justify-end">
                                <button
                                  onClick={() => generateSingleImage(image.scene_number)}
                                  disabled={image.status === 'generating'}
                                  className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-4 py-2 rounded-md text-sm"
                                >
                                  Generate This Scene
                                </button>
                              </div>
                            </div>
                          </div>

                          {/* Image Preview */}
                          <div className="w-64 flex-shrink-0">
                            <div className="aspect-square bg-slate-100 rounded-lg border-2 border-dashed border-slate-300 flex items-center justify-center">
                              {image.status === 'completed' && image.image_url ? (
                                <Image 
                                  src={image.image_url} 
                                  alt={`Scene ${image.scene_number}`}
                                  width={256}
                                  height={256}
                                  className="w-full h-full object-cover rounded-lg"
                                />
                              ) : image.status === 'generating' ? (
                                <div className="text-center">
                                  <div className="animate-spin h-8 w-8 border-2 border-blue-600 border-t-transparent rounded-full mx-auto mb-2"></div>
                                  <p className="text-slate-500 text-sm">Generating...</p>
                                </div>
                              ) : image.status === 'failed' ? (
                                <div className="text-center text-red-500">
                                  <div className="text-2xl mb-2">❌</div>
                                  <p className="text-sm">Generation Failed</p>
                                </div>
                              ) : (
                                <div className="text-center text-slate-400">
                                  <div className="text-4xl mb-2">🎨</div>
                                  <p className="text-sm">Awaiting Generation</p>
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    );
                  })
                ) : (
                  // Show scenes ready for generation (no image entries yet)
                  scenes.map((scene) => (
                    <div key={scene.scene_number} className="bg-white rounded-lg border border-slate-200 p-6 shadow-sm">
                      <div className="flex gap-6">
                        {/* Scene Content */}
                        <div className="flex-1">
                          <div className="flex items-center justify-between mb-3">
                            <h3 className="text-lg font-semibold text-slate-900">
                              Scene {scene.scene_number}
                            </h3>
                            <span className="px-3 py-1 rounded-full text-sm font-medium bg-gray-100 text-gray-800">
                              Ready to Generate
                            </span>
                          </div>
                          
                          <div className="mb-4">
                            <p className="text-sm text-slate-600 mb-2">Scene Text:</p>
                            <p className="text-slate-800 text-sm bg-slate-50 p-3 rounded border">
                              {scene.text.split('\n').slice(0, 3).join(' ') || 'No text available'}
                            </p>
                          </div>

                          <div className="mb-4">
                            <p className="text-sm text-slate-600 mb-2">Preview Generated Prompt:</p>
                            <div className="w-full rounded-lg border border-slate-200 bg-slate-50 p-3 text-slate-600 text-sm">
                              {generateScenePrompt(scene.text, scene.scene_number)}
                            </div>
                            <p className="text-xs text-slate-500 mt-1">This prompt will be generated when you start image generation.</p>
                            <div className="mt-2 flex justify-end">
                              <button
                                onClick={() => generateSingleImage(scene.scene_number)}
                                disabled={generating}
                                className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-4 py-2 rounded-md text-sm"
                              >
                                Generate This Scene
                              </button>
                            </div>
                          </div>
                        </div>

                        {/* Placeholder for Image Preview */}
                        <div className="w-64 flex-shrink-0">
                          <div className="aspect-square bg-slate-100 rounded-lg border-2 border-dashed border-slate-300 flex items-center justify-center">
                            <div className="text-center text-slate-400">
                              <div className="text-4xl mb-2">🎨</div>
                              <p className="text-sm">Ready for Generation</p>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </main>
  );
}
