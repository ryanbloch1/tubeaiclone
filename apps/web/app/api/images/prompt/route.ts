import { NextRequest, NextResponse } from "next/server";
import { GoogleGenerativeAI } from "@google/generative-ai";

type PromptRequest = {
  scene_text: string;
  scene_number: number;
};

export async function POST(request: NextRequest) {
  try {
    const body = (await request.json()) as PromptRequest;
    const { scene_text, scene_number } = body;
    
    if (!scene_text?.trim()) {
      return NextResponse.json(
        { error: 'scene_text is required' },
        { status: 400 }
      );
    }

    const apiKey = process.env.GEMINI_API_KEY || process.env.GOOGLE_API_KEY;
    
    if (!apiKey || apiKey === 'your_api_key_here' || apiKey === 'YOUR_KEY_HERE') {
      // Fallback mock prompt
      return NextResponse.json({
        prompt: `cinematic shot of ${scene_text.slice(0, 100)}... professional documentary style, high quality, detailed`,
        scene_number,
        mock: true
      });
    }

    const genAI = new GoogleGenerativeAI(apiKey);
    const model = genAI.getGenerativeModel({
      model: 'gemini-1.5-flash',
      systemInstruction: `You are an expert at creating detailed, visual prompts for AI image generation. Your job is to convert scene descriptions into compelling image generation prompts that will create high-quality, cinematic images suitable for video content.

Guidelines:
- Focus on visual, cinematic elements (lighting, camera angles, composition)
- Include specific technical details (lens type, lighting, style)
- Make prompts detailed but concise (under 200 characters)
- Use professional photography/videography terminology
- Ensure prompts are suitable for AI image generation models
- Avoid text, words, or readable content in images
- Focus on the visual essence and mood of the scene`,
    });

    const prompt = `Convert this scene description into a detailed image generation prompt:

Scene ${scene_number}: ${scene_text}

Create a cinematic, visual prompt that captures the essence of this scene for AI image generation. Focus on:
- Visual composition and framing
- Lighting and atmosphere  
- Camera angle and perspective
- Style and mood
- Any relevant visual details

Keep it under 200 characters and make it highly visual.`;

    console.log(`Generating image prompt for Scene ${scene_number}:`, scene_text.substring(0, 100) + '...');
    
    const result = await model.generateContent(prompt);
    const generatedPrompt = result.response.text().trim();
    
    console.log(`Generated prompt:`, generatedPrompt);

    return NextResponse.json({
      prompt: generatedPrompt,
      scene_number,
      mock: false
    });

  } catch (error) {
    console.error('Error generating image prompt:', error);
    const msg = error instanceof Error ? error.message : 'Unknown error';
    return NextResponse.json({ error: msg }, { status: 500 });
  }
}
