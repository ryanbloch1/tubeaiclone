"""
Gemini AI service for script generation
"""

import os
from typing import Optional, Literal


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
    Generate script content using Google Gemini API.
    
    Args:
        topic: Video topic/title
        style_name: Optional style/tone
        mode: 'script', 'outline', or 'rewrite'
        temperature: Creativity level (0.0-1.0)
        word_count: Target word count
        image_count: Number of scenes
        selection: Text to rewrite (for rewrite mode)
        context_mode: Context type ('default', 'video', 'web')
        transcript: Optional video transcript
        web_data: Optional web research data
        
    Returns:
        Generated script content
        
    Raises:
        Exception: If generation fails
    """
    try:
        # Import Google AI SDK
        from google import generativeai as genai
        
        # Configure API
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key or api_key in ['your_api_key_here', 'YOUR_KEY_HERE']:
            # Return mock data for development
            return generate_mock_script(topic, image_count, mode)
        
        genai.configure(api_key=api_key)
        
        # Create model with system instructions
        model = genai.GenerativeModel(
            model_name='gemini-2.0-flash-exp',
            system_instruction="You are a professional YouTube scriptwriter and video director. Your task is to create engaging, visual, and well-structured content.",
            generation_config={
                "temperature": temperature,
                "max_output_tokens": 8192,
            }
        )
        
        # Build prompt based on mode
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
        
        # Generate content
        response = model.generate_content(prompt)
        text = response.text
        
        # Strip any intro text before the first Scene
        # Find the first occurrence of "Scene 1" or "Scene 1:" (case insensitive)
        import re
        scene_match = re.search(r'Scene\s+1[\s:]', text, re.IGNORECASE)
        if scene_match:
            scene_index = scene_match.start()
            if scene_index > 0:
                # Remove everything before the first Scene
                text = text[scene_index:]
                print(f'Removed intro text, script now starts with: {text[:50]}...')
        
        return text
        
    except ImportError:
        # Fallback if google-generativeai not installed
        return generate_mock_script(topic, image_count, mode)
    except Exception as e:
        print(f"Gemini generation error: {str(e)}")
        raise Exception(f"Failed to generate script: {str(e)}")


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

**CONTENT REQUIREMENTS:**
1.  **Narration-First:** Provide substantive, speakable narration for each scene (2–4 sentences, ~{per_scene_words} words). Put ONLY speakable text in the "Content/Narration" field—no camera directions or stage notes there.
2.  **Concise Visuals:** Keep the "Visuals" line to one short sentence describing the key shot(s).
3.  **Narrative Flow:** Ensure a logical and engaging progression from one scene to the next (e.g., Introduction -> Problem -> Discovery -> Solution -> Conclusion).
4.  **Depth:** Explore the topic substantively. Do not just repeat the title; provide valuable information and storytelling.

**SCENE STRUCTURE:**
For each of the {image_count} scenes, provide the following structure:
---
Scene [Number] ([Start Time]-[End Time]): [A catchy, 3-5 word title for the scene]
**Content/Narration:** [2–4 sentences of speakable narration (~{per_scene_words} words), clear, conversational, and free of stage directions.]
**Visuals:** [One brief sentence describing the key shot(s).]
---

**CRITICAL:**
- Start IMMEDIATELY with "Scene 1" - do NOT include any introduction, explanation, or meta-commentary before the scenes.
- Do NOT write phrases like "Okay, here's a YouTube script" or "Here's a script designed to be..." 
- Begin directly with the first scene's narration content.
- The script should start with the actual narration that will be spoken, not any commentary about the script.

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

