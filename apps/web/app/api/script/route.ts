import { NextRequest, NextResponse } from "next/server";
import { GoogleGenerativeAI } from "@google/generative-ai";

type ReqBody = {
  topic: string;
  style_name?: string;
  image_count?: number;
  context_mode?: "default" | "video" | "web";
  transcript?: string;
  web_data?: string;
  mode?: "script" | "outline" | "rewrite";
  temperature?: number;
  word_count?: number;
  selection?: string; // for rewrite
};

export async function POST(req: NextRequest) {
  try {
    const body = (await req.json()) as ReqBody;
    const topic = body.topic?.trim();
    if (!topic) {
      return NextResponse.json({ error: "topic is required" }, { status: 400 });
    }

    const apiKey = process.env.GEMINI_API_KEY || process.env.GOOGLE_API_KEY;
    console.log("API Key being used (first 5 chars):", apiKey ? apiKey.substring(0, 5) : "N/A");

    if (!apiKey || apiKey === "your_api_key_here" || apiKey === "YOUR_KEY_HERE") {
      // Fallback mock (mirrors Python fallback)
      const t = topic;
      const scenes = body.image_count ?? 10;
      return NextResponse.json({
        text: `GENERATED SCRIPT FOR: ${t}\n\n` +
          Array.from({ length: scenes }, (_, i) =>
            `Scene ${i + 1} (0:00-0:30):\nContent about ${t}.`
          ).join("\n\n"),
        mock: true,
      });
    }

    const genAI = new GoogleGenerativeAI(apiKey);
    const temperature = Math.max(0, Math.min(1, Number(body.temperature ?? 0.7)));
    const model = genAI.getGenerativeModel({
      model: "gemini-1.5-flash",
      generationConfig: { temperature },
    });

    const imageCount = Math.max(1, Math.min(20, body.image_count ?? 10));

    const mode = (body.mode || "script") as "script" | "outline" | "rewrite";

    // Word count guidance
    const approxWords = body.word_count && body.word_count > 50 ? body.word_count : undefined;

    let prompt = "";
    if (mode === "outline") {
      prompt = `Create a YouTube video outline for the title: '${topic}'.\n\n` +
        `Return exactly ${imageCount} scene headings only (no full paragraphs).\n` +
        `Format one per line like: Scene 1: <short hooky title>.`;
    } else if (mode === "rewrite" && (body.selection || "").trim()) {
      const selection = (body.selection || "").slice(0, 4000);
      prompt = `Rewrite the following passage from a YouTube script titled '${topic}'.\n` +
        `Keep meaning, improve clarity and flow, match the existing style${body.style_name ? ` ('${body.style_name}')` : ""}.\n` +
        `Return rewritten text only, same approximate length.\n\n` +
        `Passage:\n${selection}`;
    } else {
      prompt = `Write a YouTube video script for the title: '${topic}'.\n\n` +
        `Requirements:\n` +
        `- Break into ${imageCount} scenes\n` +
        `- Use 4th grade reading level\n` +
        `- Be curiosity-driven and YouTube-safe\n` +
        `- Each scene should be engaging and informative\n` +
        `- Write about the actual topic, not just repeat the title\n` +
        (approxWords ? `- Target around ${approxWords} words total\n` : "") +
        `\nFormat each scene like this:\n` +
        `Scene 1 (0:00-0:30): [content]\n` +
        `Scene 2 (0:30-1:00): [content]\n` +
        `etc.\n\n` +
        `Make it engaging and educational!`;
    }

    if (body.style_name) {
      prompt += `\n\nUse the style: ${body.style_name}.`;
    }
    if (body.context_mode === "video" && body.transcript) {
      prompt += `\n\nUse this transcript for structure inspiration: ${body.transcript.slice(0, 500)}...`;
    }
    if (body.context_mode === "web" && body.web_data) {
      prompt += `\n\nUse these facts: ${body.web_data.slice(0, 500)}...`;
    }

    console.log("Prompt sent to Gemini API:", prompt.substring(0, 200) + "...");
    const result = await model.generateContent(prompt);
    const text = result.response.text();
    console.log("Text response from Gemini API (first 200 chars):", text.substring(0, 200) + "...");
    return NextResponse.json({ text });
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : "Unknown error";
    console.error("Error in script generation API:", msg);
    return NextResponse.json({ error: msg }, { status: 500 });
  }
}


