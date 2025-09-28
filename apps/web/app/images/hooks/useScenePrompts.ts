"use client";
import { useEffect } from 'react';
import { useVideoStore } from '@/lib/store';
import * as imagesApi from '@/lib/images/api';

export function useScenePrompts() {
  const hydrated = useVideoStore(s => s.hydrated);
  const scenes = useVideoStore(s => s.scenes);
  const prompts = useVideoStore(s => s.scenePrompts);
  const setImagesState = useVideoStore(s => s.setImagesState);

  useEffect(() => {
    if (!hydrated || scenes.length === 0) return;
    const map = new Map(prompts.map(p => [p.scene_number, p]));
    const needs = scenes.some(s => !map.has(s.scene_number));
    if (!needs) return;

    setImagesState(() => ({
      scenePrompts: scenes.map(sc => map.get(sc.scene_number) ?? ({
        scene_number: sc.scene_number, prompt: null, status: 'loading' as const
      }))
    }));

    (async () => {
      await Promise.allSettled(scenes.map(async sc => {
        try {
          const prompt = await imagesApi.generatePrompt(sc.text, sc.scene_number);
          setImagesState(prev => ({
            scenePrompts: prev.scenePrompts.map(p =>
              p.scene_number === sc.scene_number
                ? { ...p, prompt, status: 'ready' as const }
                : p
            )
          }));
        } catch {
          setImagesState(prev => ({
            scenePrompts: prev.scenePrompts.map(p =>
              p.scene_number === sc.scene_number
                ? { ...p, status: 'error' as const }
                : p
            )
          }));
        }
      }));
    })();
  }, [hydrated, scenes, prompts, setImagesState]);

  const promptsReady =
    scenes.length > 0 &&
    prompts.length === scenes.length &&
    prompts.every(p => p.status === 'ready' && p.prompt);

  return { prompts, promptsReady };
}


