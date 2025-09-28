export async function generatePrompt(scene_text: string, scene_number: number): Promise<string> {
  const res = await fetch('/api/images/prompt', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ scene_text, scene_number })
  });
  if (!res.ok) {
    throw new Error('Prompt generation failed');
  }
  const json = await res.json();
  return json.prompt as string;
}

export async function generateImage(prompt: string, scene_number: number): Promise<{ image_url: string; scene_number: number; }>{
  const res = await fetch('/api/images/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt, scene_number })
  });
  if (!res.ok) {
    throw new Error('Image generation failed');
  }
  return await res.json();
}


