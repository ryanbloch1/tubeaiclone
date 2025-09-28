import type { Scene } from './types';

export function parseScriptIntoScenes(script: string): Scene[] {
  const lines = script.split('\n');
  const scenes: Scene[] = [];
  let currentScene: Scene | null = null;

  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) continue;

    const sceneMatch = trimmed.match(/^Scene\s+(\d+)/i);
    if (sceneMatch) {
      if (currentScene) scenes.push(currentScene);
      currentScene = {
        scene_number: parseInt(sceneMatch[1]),
        text: trimmed,
        description: trimmed
      };
    } else if (currentScene) {
      currentScene.text += '\n' + trimmed;
    }
  }

  if (currentScene) scenes.push(currentScene);
  return scenes;
}


