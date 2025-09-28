"use client";
import { useEffect } from 'react';
import { useVideoStore } from '@/lib/store';
import { parseScriptIntoScenes } from '@/lib/images/parseScenes';

export function useScenes() {
  const hydrated = useVideoStore(s => s.hydrated);
  const generating = useVideoStore(s => s.generating);
  const scenes = useVideoStore(s => s.scenes);
  const originalScript = useVideoStore(s => s.editableScript);
  const images = useVideoStore(s => s.images);
  const setImagesState = useVideoStore(s => s.setImagesState);

  useEffect(() => {
    if (!hydrated) return;
    if (generating) setImagesState({ generating: false, currentScene: null });
    if (scenes.length === 0 && originalScript && originalScript.trim().length > 0) {
      const parsed = parseScriptIntoScenes(originalScript);
      setImagesState({
        scenes: parsed,
        images: [],
        scenePrompts: [],
        cameFromVoiceover: true,
        generating: false,
        currentScene: null
      });
    }
    if (images.some((img) => img.status === 'generating')) {
      setImagesState((s) => ({
        images: s.images.map((img) => img.status === 'generating' ? { ...img, status: 'pending' } : img)
      }));
    }
  }, [hydrated, generating, scenes.length, originalScript, images, setImagesState]);

  return { scenes };
}


