"use client";
import { useEffect, useState, useMemo } from "react";
import { sanitizeScriptForVoiceover } from "@/lib/sanitize";

type Scene = {
  scene_number: number;
  text: string;
  description: string;
};

type ImageGeneration = {
  scene_number: number;
  prompt: string;
  status: 'pending' | 'generating' | 'completed' | 'failed';
  image_url?: string;
  error?: string;
};

export default function ImagesPage() {
  const [rawScript, setRawScript] = useState("");
  const [scenes, setScenes] = useState<Scene[]>([]);
  const [images, setImages] = useState<ImageGeneration[]>([]);
  const [generating, setGenerating] = useState(false);
  const [currentScene, setCurrentScene] = useState<number | null>(null);
  const [cameFromVoiceover, setCameFromVoiceover] = useState(false);

  useEffect(() => {
    try {
      // Use original script (with scene markers) for image generation
      const originalScript = localStorage.getItem("tubeai_original_script");
      const sanitizedScript = localStorage.getItem("tubeai_script");
      const fromVoiceover = localStorage.getItem("tubeai_from_voiceover") === "true";
      
      // Prefer original script for scene parsing, fallback to sanitized
      const scriptToUse = originalScript || sanitizedScript;
      
      if (scriptToUse) {
        setRawScript(scriptToUse);
        // Parse scenes from script (should have Scene 1, Scene 2, etc.)
        const parsedScenes = parseScriptIntoScenes(scriptToUse);
        setScenes(parsedScenes);
        // Initialize image generation states
        setImages(parsedScenes.map(scene => ({
          scene_number: scene.scene_number,
          prompt: generateScenePrompt(scene.text),
          status: 'pending'
        })));
      }
      setCameFromVoiceover(fromVoiceover);
      localStorage.removeItem("tubeai_from_voiceover");
    } catch {}
  }, []);

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

  const generateScenePrompt = (sceneText: string): string => {
    // Extract key visual elements from scene text
    const cleanText = sceneText.toLowerCase();
    
    if (cleanText.includes('pyramid') || cleanText.includes('egypt')) {
      return "Ancient Egyptian pyramids at sunset, mysterious and majestic, cinematic lighting, professional photography";
    }
    if (cleanText.includes('alien') || cleanText.includes('ufo')) {
      return "Mysterious UFO lights in the sky, ancient monuments below, cinematic sci-fi atmosphere";
    }
    if (cleanText.includes('desert') || cleanText.includes('sand')) {
      return "Vast desert landscape with ancient ruins, golden sand dunes, dramatic lighting";
    }
    
    // Default prompt based on scene number
    return "Professional video scene, cinematic composition, high quality, dramatic lighting, YouTube thumbnail style";
  };

  const generateAllImages = async () => {
    if (scenes.length === 0) return;
    
    setGenerating(true);
    
    // Process scenes one by one
    for (let i = 0; i < scenes.length; i++) {
      const scene = scenes[i];
      setCurrentScene(scene.scene_number);
      
      // Update status to generating
      setImages(prev => prev.map(img => 
        img.scene_number === scene.scene_number 
          ? { ...img, status: 'generating' }
          : img
      ));

      try {
        // Simulate API call to your image generation endpoint
        const response = await fetch('/api/images/generate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            prompt: images.find(img => img.scene_number === scene.scene_number)?.prompt,
            scene_number: scene.scene_number
          })
        });

        if (response.ok) {
          const result = await response.json();
          setImages(prev => prev.map(img =>
            img.scene_number === scene.scene_number
              ? { ...img, status: 'completed', image_url: result.image_url }
              : img
          ));
        } else {
          throw new Error('Generation failed');
        }
      } catch (error) {
        setImages(prev => prev.map(img =>
          img.scene_number === scene.scene_number
            ? { ...img, status: 'failed', error: 'Generation failed' }
            : img
        ));
      }

      // Small delay between generations
      await new Promise(resolve => setTimeout(resolve, 1000));
    }

    setCurrentScene(null);
    setGenerating(false);
  };

  const script = useMemo(() => sanitizeScriptForVoiceover(rawScript), [rawScript]);
  const completedImages = images.filter(img => img.status === 'completed').length;
  const totalImages = images.length;

  return (
    <main className="min-h-screen bg-slate-50">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-6xl mx-auto">
          <h1 className="text-4xl font-bold text-center mb-8 text-slate-900">
            🎬 Scene Image Generation
          </h1>

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

                {!generating && completedImages === 0 && (
                  <button
                    onClick={generateAllImages}
                    disabled={scenes.length === 0}
                    className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-8 py-4 rounded-lg font-semibold transition-all duration-200 hover:transform hover:-translate-y-0.5 hover:shadow-lg flex items-center justify-center space-x-2"
                  >
                    <span>🎨</span>
                    <span>Generate All Scene Images</span>
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
                {images.map((image, index) => {
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
                            <p className="text-slate-700 text-sm bg-blue-50 p-3 rounded border border-blue-200">
                              {image.prompt}
                            </p>
                          </div>
                        </div>

                        {/* Image Preview */}
                        <div className="w-64 flex-shrink-0">
                          <div className="aspect-square bg-slate-100 rounded-lg border-2 border-dashed border-slate-300 flex items-center justify-center">
                            {image.status === 'completed' && image.image_url ? (
                              <img 
                                src={image.image_url} 
                                alt={`Scene ${image.scene_number}`}
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
                })}
              </div>
            </>
          )}
        </div>
      </div>
    </main>
  );
}
