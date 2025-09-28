"use client";
import React from "react";
import { useRouter } from "next/navigation";
import { useVideoStore } from "@/lib/store";
import GenerationControls from "./components/GenerationControls";
import SceneCard from "./components/SceneCard";
import { useScenes } from "./hooks/useScenes";
import { useScenePrompts } from "./hooks/useScenePrompts";
import { useImageGeneration } from "./hooks/useImageGeneration";

// Presentation-only: logic lives in hooks; this file composes UI


export default function ImagesPage() {
  const router = useRouter();
  const setImagesState = useVideoStore(s => s.setImagesState);
  const cameFromVoiceover = useVideoStore(s => s.cameFromVoiceover);
  const scenes = useVideoStore(s => s.scenes);
  const images = useVideoStore(s => s.images);
  // Wire hooks: all side effects and API calls are in hooks
  useScenes();
  const { prompts, promptsReady } = useScenePrompts();
  const { generating, currentScene, progress, generateAll, generateOne } = useImageGeneration();

  // derived counts handled by hooks/components as needed

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
              <GenerationControls
                scenesCount={scenes.length}
                readyCount={prompts.filter(p=>p.status==='ready').length}
                promptsReady={promptsReady}
                generating={generating}
                currentScene={currentScene}
                progress={progress}
                onGenerateAll={generateAll}
              />

              {/* Scene Images Grid */}
              <div className="grid gap-6">
                {images.length > 0 ? (
                  images.map((image) => {
                    const scene = scenes.find(s => s.scene_number === image.scene_number);
                    const sp = prompts.find(p => p.scene_number === image.scene_number);
                    return (
                      <SceneCard
                        key={image.scene_number}
                        sceneNumber={image.scene_number}
                        sceneText={scene?.text || ''}
                        promptState={sp}
                        imageState={image}
                        onChangePrompt={(value) => setImagesState(s => ({
                          scenePrompts: s.scenePrompts.map(p => p.scene_number === image.scene_number ? { ...p, prompt: value, status: 'ready' } : p),
                          images: s.images.map(img => img.scene_number === image.scene_number ? { ...img, prompt: value } : img),
                        }))}
                        onGenerate={() => generateOne(image.scene_number)}
                        disabled={image.status === 'generating'}
                      />
                    );
                  })
                ) : (
                  scenes.map((scene) => {
                    const sp = prompts.find(p => p.scene_number === scene.scene_number);
                    return (
                      <SceneCard
                        key={scene.scene_number}
                        sceneNumber={scene.scene_number}
                        sceneText={scene.text}
                        promptState={sp}
                        imageState={undefined}
                        onChangePrompt={(value) => setImagesState(s => ({
                          scenePrompts: s.scenePrompts.map(p => p.scene_number === scene.scene_number ? { ...p, prompt: value, status: 'ready' } : p),
                        }))}
                        onGenerate={() => generateOne(scene.scene_number)}
                        disabled={generating || !(sp?.status === 'ready' && sp?.prompt)}
                      />
                    );
                  })
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </main>
  );
}
