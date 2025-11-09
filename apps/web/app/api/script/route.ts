import { GoogleGenerativeAI } from '@google/generative-ai';
import { NextRequest, NextResponse } from 'next/server';

type ReqBody = {
  topic: string;
  style_name?: string;
  image_count?: number;
  context_mode?: 'default' | 'video' | 'web';
  transcript?: string;
  web_data?: string;
  mode?: 'script' | 'outline' | 'rewrite';
  temperature?: number;
  word_count?: number;
  selection?: string; // for rewrite
};

export async function POST(req: NextRequest) {
  try {
    const body = (await req.json()) as ReqBody;
    const topic = body.topic?.trim().slice(0, 200); // Cap topic length
    if (!topic) {
      return NextResponse.json({ error: 'topic is required' }, { status: 400 });
    }

    const apiKey = process.env.GEMINI_API_KEY || process.env.GOOGLE_API_KEY;
    console.log(
      'API Key being used (first 5 chars):',
      apiKey ? apiKey.substring(0, 5) : 'N/A'
    );

    // Get mode and image count early for logging
    const imageCount = Math.max(1, Math.min(20, body.image_count ?? 10));
    const mode = (body.mode || 'script') as 'script' | 'outline' | 'rewrite';

    console.log(
      `Generating ${mode} for topic: "${topic}" (${imageCount} scenes)`
    );

    if (
      !apiKey ||
      apiKey === 'your_api_key_here' ||
      apiKey === 'YOUR_KEY_HERE'
    ) {
      // Fallback mock
      return NextResponse.json({
        text:
          `GENERATED SCRIPT FOR: ${topic}\n\n` +
          Array.from(
            { length: imageCount },
            (_, i) => `Scene ${i + 1} (0:00-0:30):\nContent about ${topic}.`
          ).join('\n\n'),
        mock: true,
        mode,
        imageCount,
      });
    }

    const genAI = new GoogleGenerativeAI(apiKey);
    const temperature = Math.max(
      0,
      Math.min(1, Number(body.temperature ?? 0.7))
    );

    // System instruction for model behavior
    const baseInstructions =
      'You are a professional YouTube scriptwriter and video director. Your task is to create engaging, visual, and well-structured content.';

    const model = genAI.getGenerativeModel({
      model: 'gemini-2.5-flash',
      systemInstruction: baseInstructions,
      generationConfig: { temperature },
    });

    const approxWords =
      body.word_count && body.word_count > 50 ? body.word_count : undefined;
    const perSceneWords = approxWords
      ? Math.max(25, Math.round(approxWords / Math.max(1, imageCount)))
      : 50;

    let prompt = '';

    if (mode === 'outline') {
      prompt = `Generate a structured outline for a YouTube video titled: "${topic}".

**CORE REQUIREMENTS:**
- Deliver exactly ${imageCount} distinct scene headings.
- Each heading must be a concise, hook-driven title for the scene (3-8 words).
- Focus on visual and narrative progression.

**FORMAT:**
Return ONLY a numbered list. Do not use markdown. Example:
1. The Shocking Discovery That Started It All
2. Ancient Tools and How They Were Used
3. The Secret Chamber Revealed

**TOPIC:** ${topic}
`;
    } else if (mode === 'rewrite' && (body.selection || '').trim()) {
      const selection = (body.selection || '').slice(0, 4000);
      prompt = `Rewrite the following passage from a YouTube script to improve its clarity, flow, and engagement, while strictly preserving its core meaning and factual content.

**CONTEXT:**
- Video Title: "${topic}"
${body.style_name ? `- Desired Style/Tone: "${body.style_name}"\n` : ''}
**REWRITE INSTRUCTIONS:**
- Enhance readability and pacing for a spoken-word format.
- Maintain the original length and intent.
- Ensure the language is vivid and visual.

**PASSAGE TO REWRITE:**
"""
${selection}
"""

**OUTPUT:**
Return only the rewritten text, without any additional commentary or labels.`;
    } else {
      // "script" mode (default)
      prompt = `Write a complete YouTube video script based on the title: "${topic}".

**VIDEO SPECIFICATIONS:**
- Target Audience: General audience (4th-grade reading level)
- Tone: Curiosity-driven, educational, and YouTube-safe.
- Number of Scenes: ${imageCount}
${approxWords ? `- Approximate Total Word Count: ${approxWords}\n` : ''}

**CONTENT REQUIREMENTS:**
1.  **Narration-First:** Provide substantive, speakable narration for each scene (2–4 sentences, ~${perSceneWords} words). Put ONLY speakable text in the "Content/Narration" field—no camera directions or stage notes there.
2.  **Concise Visuals:** Keep the "Visuals" line to one short sentence describing the key shot(s).
3.  **Narrative Flow:** Ensure a logical and engaging progression from one scene to the next (e.g., Introduction -> Problem -> Discovery -> Solution -> Conclusion).
4.  **Depth:** Explore the topic substantively. Do not just repeat the title; provide valuable information and storytelling.

**SCENE STRUCTURE:**
For each of the ${imageCount} scenes, provide the following structure:
---
Scene [Number] ([Start Time]-[End Time]): [A catchy, 3-5 word title for the scene]
**Content/Narration:** [2–4 sentences of speakable narration (~${perSceneWords} words), clear, conversational, and free of stage directions.]
**Visuals:** [One brief sentence describing the key shot(s).]
---

**CRITICAL:**
- Start IMMEDIATELY with "Scene 1" - do NOT include any introduction, explanation, or meta-commentary before the scenes.
- Do NOT write phrases like "Okay, here's a YouTube script" or "Here's a script designed to be..." 
- Begin directly with the first scene's narration content.
- The script should start with the actual narration that will be spoken, not any commentary about the script.

**TOPIC:** ${topic}
`;
    }

    // Add additional context if provided
    if (body.style_name) {
      prompt += `\n\nUse the style: ${body.style_name}.`;
    }
    if (body.context_mode === 'video' && body.transcript) {
      prompt += `\n\nUse this transcript for structure inspiration: ${body.transcript.slice(
        0,
        500
      )}...`;
    }
    if (body.context_mode === 'web' && body.web_data) {
      prompt += `\n\nUse these facts: ${body.web_data.slice(0, 500)}...`;
    }

    console.log('Prompt sent to Gemini API:', prompt.substring(0, 200) + '...');
    const result = await model.generateContent(prompt);
    let text = result.response.text();
    console.log(
      'Text response from Gemini API (first 200 chars):',
      text.substring(0, 200) + '...'
    );
    
    // Strip any intro text before the first Scene
    // Find the first occurrence of "Scene 1" or "Scene 1:" (case insensitive)
    const sceneMatch = text.match(/(Scene\s+1[\s:])/i);
    if (sceneMatch && sceneMatch.index !== undefined && sceneMatch.index > 0) {
      // Remove everything before the first Scene
      text = text.substring(sceneMatch.index);
      console.log('Removed intro text, script now starts with:', text.substring(0, 50) + '...');
    }

    return NextResponse.json({
      text,
      mode,
      imageCount,
    });
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : 'Unknown error';
    console.error('Error in script generation API:', msg);
    return NextResponse.json({ error: msg }, { status: 500 });
  }
}
