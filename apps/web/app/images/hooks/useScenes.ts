"use client";
import { useEffect, useRef } from 'react';
import { useVideoStore } from '@/lib/store';
import { parseScriptIntoScenes } from '@/lib/images/parseScenes';

export function useScenes() {
  const hydrated = useVideoStore(s => s.hydrated);
  const generating = useVideoStore(s => s.generating);
  const scenes = useVideoStore(s => s.scenes);
  const originalScript = useVideoStore(s => s.editableScript);
  const setImagesState = useVideoStore(s => s.setImagesState);
  const didResetRef = useRef(false);

  useEffect(() => {
    if (!hydrated) return;
    
    // One-time reset on initial arrival to images page
    if (!didResetRef.current) {
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
      } else if (scenes.length > 0) {
        // Keep parsed scenes but clear volatile generations/prompts
        setImagesState({
          images: [],
          scenePrompts: [],
          generating: false,
          currentScene: null
        });
      }
      didResetRef.current = true;
    }

    // Clean up any stale "generating" statuses from previous sessions
    if (generating) {
      setImagesState({ generating: false, currentScene: null });
    }
  }, [hydrated, generating, scenes.length, originalScript, setImagesState]);

  return { scenes };
}


