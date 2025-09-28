export type Scene = {
  scene_number: number;
  text: string;
  description: string;
};

export type ScenePrompt = {
  scene_number: number;
  prompt: string | null;
  status: 'loading' | 'ready' | 'error';
};

export type ImageGeneration = {
  scene_number: number;
  prompt: string;
  status: 'pending' | 'generating' | 'completed' | 'failed';
  image_url?: string;
  error?: string;
};


