"""
AI service for script generation.

Prefers Groq (LLaMA models, free tier) when a GROQ_API_KEY is
configured, and falls back to Google Gemini (if configured) or a mock
script for local development.
"""

import os
import re
from typing import Optional, Literal

# Load environment variables from .env file
try:
    from dotenv import find_dotenv, load_dotenv
    load_dotenv(find_dotenv(), override=True)
except ImportError:
    # python-dotenv not installed
    pass
except Exception as e:
    print(f"Warning: Error loading .env file: {e}")

try:
    import httpx
except ImportError:  # pragma: no cover - httpx should be installed via requirements
    httpx = None


GROQ_PLACEHOLDER_KEYS = {'', 'your_api_key_here', 'YOUR_KEY_HERE'}


async def generate_script_with_gemini(
    topic: str,
    style_name: Optional[str] = None,
    mode: Literal['script', 'outline', 'rewrite'] = 'script',
    temperature: float = 0.7,
    word_count: int = 500,
    image_count: int = 10,
    selection: Optional[str] = None,
    context_mode: Optional[str] = 'default',
    transcript: Optional[str] = None,
    web_data: Optional[str] = None
) -> str:
    """
    Generate script content using Groq (preferred, free) or Google Gemini.
    """
    prompt = build_prompt(
        topic=topic,
        mode=mode,
        image_count=image_count,
        word_count=word_count,
        style_name=style_name,
        selection=selection,
        context_mode=context_mode,
        transcript=transcript,
        web_data=web_data
    )
    
    # Try Groq first (free tier, no credit card required)
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key and groq_key not in GROQ_PLACEHOLDER_KEYS:
        try:
            text = await _generate_with_groq(
                api_key=groq_key,
                prompt=prompt,
                temperature=temperature,
                max_tokens=_estimate_max_tokens(word_count, mode),
            )
            return _strip_intro_to_first_scene(text)
        except Exception as e:
            print(f"Groq generation error: {str(e)} - falling back to Gemini/mock.")
    
    # Fallback to Gemini if configured
    try:
        text = await _generate_with_gemini_sdk(
            prompt=prompt,
            temperature=temperature
        )
        if text:
            return _strip_intro_to_first_scene(text)
    except Exception as e:
        print(f"Gemini SDK fallback error: {str(e)}")
    
    # Last resort: mock data for local development
    return generate_mock_script(topic, image_count, mode)


async def _generate_with_groq(
    api_key: str,
    prompt: str,
    temperature: float,
    max_tokens: int,
) -> str:
    """Call Groq's chat completion endpoint (free tier, no credit card required)."""
    if httpx is None:
        raise Exception("httpx is not installed; cannot call Groq API.")
    
    # Groq offers free LLaMA models - using LLaMA 3.1 8B which is fast and free
    groq_model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    api_url = "https://api.groq.com/openai/v1/chat/completions"
    
    payload = {
        "model": groq_model,
        "temperature": float(max(0.0, min(1.0, temperature))),
        "max_tokens": max_tokens,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a professional YouTube scriptwriter and video director. "
                    "Your task is to create engaging, visual, and well-structured content."
                )
            },
            {"role": "user", "content": prompt}
        ]
    }
    
    timeout = httpx.Timeout(60.0, connect=10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(
            api_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json=payload
        )
        
        if response.status_code >= 400:
            try:
                detail = response.json()
            except Exception:
                detail = response.text
            raise Exception(f"Groq API error {response.status_code}: {detail}")
        
        data = response.json()
        choices = data.get("choices", [])
        if not choices:
            raise Exception("Groq API returned no choices")
        
        message = choices[0].get("message") or {}
        content = message.get("content", "")
        
        if not content:
            raise Exception("Groq API returned empty content")
        
        return content


async def _generate_with_gemini_sdk(prompt: str, temperature: float) -> Optional[str]:
    """Use Google Gemini SDK if configured."""
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key or api_key in GROQ_PLACEHOLDER_KEYS:
        return None
    
    try:
        from google import generativeai as genai
    except ImportError:
        return None
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name='gemini-2.0-flash-exp',
        system_instruction="You are a professional YouTube scriptwriter and video director. Your task is to create engaging, visual, and well-structured content.",
        generation_config={
            "temperature": float(max(0.0, min(1.0, temperature))),
            "max_output_tokens": 8192,
        }
    )
    
    response = model.generate_content(prompt)
    return getattr(response, "text", None)


def build_prompt(
    topic: str,
    mode: str,
    image_count: int,
    word_count: int,
    style_name: Optional[str] = None,
    selection: Optional[str] = None,
    context_mode: Optional[str] = 'default',
    transcript: Optional[str] = None,
    web_data: Optional[str] = None
) -> str:
    """Build the appropriate prompt based on mode."""
    
    per_scene_words = max(25, round(word_count / max(1, image_count)))
    
    if mode == 'outline':
        prompt = f"""Generate a structured outline for a YouTube video titled: "{topic}".

**CORE REQUIREMENTS:**
- Deliver exactly {image_count} distinct scene headings.
- Each heading must be a concise, hook-driven title for the scene (3-8 words).
- Focus on visual and narrative progression.

**FORMAT:**
Return ONLY a numbered list. Do not use markdown. Example:
1. The Shocking Discovery That Started It All
2. Ancient Tools and How They Were Used
3. The Secret Chamber Revealed

**TOPIC:** {topic}
"""
    
    elif mode == 'rewrite' and selection:
        prompt = f"""Rewrite the following passage from a YouTube script to improve its clarity, flow, and engagement, while strictly preserving its core meaning and factual content.

**CONTEXT:**
- Video Title: "{topic}"
{f'- Desired Style/Tone: "{style_name}"' if style_name else ''}

**REWRITE INSTRUCTIONS:**
- Enhance readability and pacing for a spoken-word format.
- Maintain the original length and intent.
- Ensure the language is vivid and visual.

**PASSAGE TO REWRITE:**
\"\"\"
{selection[:4000]}
\"\"\"

**OUTPUT:**
Return only the rewritten text, without any additional commentary or labels."""
    
    else:  # 'script' mode (default)
        prompt = f"""Write a complete YouTube video script based on the title: "{topic}".

**VIDEO SPECIFICATIONS:**
- Target Audience: General audience (4th-grade reading level)
- Tone: Curiosity-driven, educational, and YouTube-safe.
- Number of Scenes: {image_count}
{f'- Approximate Total Word Count: {word_count}' if word_count else ''}

**EXACT FORMAT REQUIRED:**
You MUST follow this exact format for EVERY scene. Do not deviate:

Scene 1 (0:00-0:30): [Scene Title Here]
**Content/Narration:** [2-4 sentences of speakable narration, ~{per_scene_words} words]
**Visuals:** [One brief sentence describing the key shot]

Scene 2 (0:30-1:00): [Scene Title Here]
**Content/Narration:** [2-4 sentences of speakable narration, ~{per_scene_words} words]
**Visuals:** [One brief sentence describing the key shot]

[Continue for all {image_count} scenes...]

**CRITICAL FORMATTING RULES:**
1. Start IMMEDIATELY with "Scene 1" - NO introduction, NO explanation, NO meta-commentary
2. Each scene MUST have this EXACT structure:
   - Line 1: "Scene X (time-time): Title"
   - Line 2: "**Content/Narration:** [narration text]"
   - Line 3: "**Visuals:** [visual description]"
   - Empty line between scenes
3. Use double asterisks ** around "Content/Narration:" and "Visuals:"
4. Do NOT write any text before "Scene 1"
5. Do NOT write any conclusion or summary after the last scene
6. The narration text should be speakable, conversational, and free of stage directions

**CONTENT REQUIREMENTS:**
- Provide substantive, speakable narration for each scene (2–4 sentences, ~{per_scene_words} words)
- Keep visuals to one short sentence describing the key shot(s)
- Ensure logical progression from one scene to the next
- Explore the topic substantively with valuable information

**TOPIC:** {topic}
"""
    
    # Add style
    if style_name:
        prompt += f"\n\nUse the style: {style_name}."
    
    # Add context
    if context_mode == 'video' and transcript:
        prompt += f"\n\nUse this transcript for structure inspiration: {transcript[:500]}..."
    if context_mode == 'web' and web_data:
        prompt += f"\n\nUse these facts: {web_data[:500]}..."
    
    return prompt


def generate_mock_script(topic: str, image_count: int, mode: str) -> str:
    """Generate mock script for development/testing."""
    if mode == 'outline':
        return '\n'.join([
            f"{i+1}. Scene {i+1}: {topic} - Part {i+1}"
            for i in range(image_count)
        ])
    else:
        return f"GENERATED SCRIPT FOR: {topic}\n\n" + '\n\n'.join([
            f"Scene {i+1} (0:00-0:30):\nContent about {topic} for scene {i+1}."
            for i in range(image_count)
        ])


def _strip_intro_to_first_scene(text: str) -> str:
    """Ensure script starts at Scene 1 and has proper Scene structure."""
    if not text:
        return text
    
    # Find first Scene marker
    scene_match = re.search(r'Scene\s+1[\s:]', text, re.IGNORECASE)
    if scene_match:
        scene_index = scene_match.start()
        if scene_index > 0:
            text = text[scene_index:]
            print(f'Removed intro text, script now starts with: {text[:50]}...')
    
    # Validate that we have Scene structure
    scene_count = len(re.findall(r'Scene\s+\d+', text, re.IGNORECASE))
    if scene_count == 0:
        print('⚠️  WARNING: No Scene markers found in generated script!')
        print(f'First 200 chars: {text[:200]}')
    else:
        print(f'✓ Found {scene_count} Scene markers in generated script')
    
    return text.strip()


def _estimate_max_tokens(word_count: int, mode: str) -> int:
    """Rough estimate of tokens required for Groq completions."""
    if mode == 'outline':
        return 1024
    approx_tokens = max(512, int(word_count * 1.5))
    return min(4096, approx_tokens)

