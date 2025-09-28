"use client";
import { useCallback } from 'react';
import { useVideoStore } from '@/lib/store';
import * as imagesApi from '@/lib/images/api';

export function useImageGeneration() {
  const scenes = useVideoStore(s => s.scenes);
  const images = useVideoStore(s => s.images);
  const prompts = useVideoStore(s => s.scenePrompts);
  const generating = useVideoStore(s => s.generating);
  const currentScene = useVideoStore(s => s.currentScene);
  const setImagesState = useVideoStore(s => s.setImagesState);

  const generateAll = useCallback(async () => {
    if (scenes.length === 0) return;
    const map = new Map(prompts.map(p => [p.scene_number, p]));
    const allReady = scenes.every(sc => map.get(sc.scene_number)?.status === 'ready' && map.get(sc.scene_number)?.prompt);
    if (!allReady) return;

    setImagesState({ generating: true });

    for (let i = 0; i < scenes.length; i++) {
      const sc = scenes[i];
      const sp = map.get(sc.scene_number);
      const scenePrompt = sp?.prompt ?? '';
      const existing = images.find(img => img.scene_number === sc.scene_number);
      if (existing?.status === 'completed') continue;

      setImagesState({ currentScene: sc.scene_number });

      if (!existing) {
        setImagesState(s => ({ images: [...s.images, { scene_number: sc.scene_number, prompt: scenePrompt, status: 'pending' }] }));
      }
      setImagesState(s => ({ images: s.images.map(img => img.scene_number === sc.scene_number ? { ...img, status: 'generating' } : img) }));

      try {
        const result = await imagesApi.generateImage(scenePrompt, sc.scene_number);
        setImagesState(s => ({ images: s.images.map(img => img.scene_number === sc.scene_number ? { ...img, status: 'completed', image_url: result.image_url } : img) }));
      } catch {
        setImagesState(s => ({ images: s.images.map(img => img.scene_number === sc.scene_number ? { ...img, status: 'failed', error: 'Generation failed' } : img) }));
      }

      await new Promise(r => setTimeout(r, 1000));
    }

    setImagesState({ currentScene: null, generating: false });
  }, [scenes, prompts, images, setImagesState]);

  const generateOne = useCallback(async (sceneNumber: number) => {
    const sc = scenes.find(s => s.scene_number === sceneNumber);
    if (!sc) return;
    const sp = prompts.find(p => p.scene_number === sceneNumber);
    const scenePrompt = sp?.prompt ?? '';
    if (!scenePrompt) return;

    setImagesState({ currentScene: sceneNumber });

    let existing = images.find(img => img.scene_number === sceneNumber);
    if (!existing) {
      const newImage = { scene_number: sceneNumber, prompt: scenePrompt, status: 'pending' as const };
      setImagesState(s => ({ images: [...s.images, newImage] }));
      existing = newImage;
    }

    setImagesState(s => ({ images: s.images.map(img => img.scene_number === sceneNumber ? { ...img, status: 'generating' } : img) }));

    try {
      const result = await imagesApi.generateImage(existing.prompt, sceneNumber);
      setImagesState(s => ({ images: s.images.map(img => img.scene_number === sceneNumber ? { ...img, status: 'completed', image_url: result.image_url } : img) }));
    } catch {
      setImagesState(s => ({ images: s.images.map(img => img.scene_number === sceneNumber ? { ...img, status: 'failed', error: 'Generation failed' } : img) }));
    } finally {
      setImagesState({ currentScene: null });
    }
  }, [scenes, prompts, images, setImagesState]);

  const completedImages = images.filter(i => i.status === 'completed').length;
  const totalImages = images.length;
  const progress = totalImages > 0 ? completedImages / totalImages : 0;

  return { generating, currentScene, progress, generateAll, generateOne };
}


