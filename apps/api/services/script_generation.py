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
    web_data: Optional[str] = None,
    # Real estate fields
    video_type: Optional[str] = None,
    property_address: Optional[str] = None,
    property_type: Optional[str] = None,
    property_price: Optional[float] = None,
    bedrooms: Optional[int] = None,
    bathrooms: Optional[float] = None,
    square_feet: Optional[int] = None,
    mls_number: Optional[str] = None,
    property_features: Optional[list[str]] = None,
    # Photo-grounding
    photos: Optional[list[dict]] = None,
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
        web_data=web_data,
        # Real estate fields
        video_type=video_type,
        property_address=property_address,
        property_type=property_type,
        property_price=property_price,
        bedrooms=bedrooms,
        bathrooms=bathrooms,
        square_feet=square_feet,
        mls_number=mls_number,
        property_features=property_features,
        photos=photos,
    )
    
    # Try Groq first (free tier, no credit card required)
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key and groq_key not in GROQ_PLACEHOLDER_KEYS:
        try:
            text = await _generate_with_groq(
                api_key=groq_key,
                prompt=prompt,
                temperature=temperature,
                max_tokens=_estimate_max_tokens(word_count, mode, image_count),
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
    web_data: Optional[str] = None,
    # Real estate fields
    video_type: Optional[str] = None,
    property_address: Optional[str] = None,
    property_type: Optional[str] = None,
    property_price: Optional[float] = None,
    bedrooms: Optional[int] = None,
    bathrooms: Optional[float] = None,
    square_feet: Optional[int] = None,
    mls_number: Optional[str] = None,
    property_features: Optional[list[str]] = None,
    # Photo-grounding
    photos: Optional[list[dict]] = None,
) -> str:
    """Build the appropriate prompt based on mode."""
    
    per_scene_words = max(25, round(word_count / max(1, image_count)))
    
    # Build real estate context string if real estate data is provided
    real_estate_context = ""
    if video_type:
        if video_type == 'listing' and (property_address or property_type or property_price):
            # Property listing video
            property_details = []
            if property_address:
                property_details.append(f"located at {property_address}")
            if property_type:
                property_details.append(f"a {property_type.replace('_', ' ')}")
            if bedrooms is not None and bathrooms is not None:
                property_details.append(f"{bedrooms} bedrooms and {bathrooms} bathrooms")
            if square_feet:
                property_details.append(f"{square_feet:,} square metres")
            if property_price:
                property_details.append(f"priced at R{property_price:,.0f}")
            if property_features:
                features_str = ", ".join([f.replace('_', ' ') for f in property_features])
                property_details.append(f"featuring {features_str}")
            
            real_estate_context = f"\n\n**PROPERTY DETAILS:**\n" + "\n".join([f"- {detail}" for detail in property_details])
            if mls_number:
                real_estate_context += f"\n- MLS Number: {mls_number}"
        
        elif video_type == 'neighborhood_guide' and property_address:
            # Extract neighborhood/city from address
            address_parts = property_address.split(',')
            neighborhood = address_parts[0].strip() if len(address_parts) > 0 else property_address
            real_estate_context = f"\n\n**NEIGHBORHOOD:** {neighborhood}"
        
        elif video_type == 'market_update' and property_address:
            # Extract area from address
            address_parts = property_address.split(',')
            area = address_parts[-1].strip() if len(address_parts) > 1 else property_address
            real_estate_context = f"\n\n**MARKET AREA:** {area}"

    # Build a human-readable list of analysed photos for photo-grounded scripts
    photos_block = ""
    if photos:
        photo_lines = []
        for idx, p in enumerate(photos, start=1):
            scene_type = (p.get("scene_type") or "scene").replace("_", " ")
            caption = p.get("caption") or ""
            features_list = p.get("features") or []
            features = ", ".join(features_list)
            line = f"{idx}. [{scene_type}] {caption}"
            if features:
                line += f" | key features: {features}"
            photo_lines.append(line)
        photos_block = "\n".join(photo_lines)
        # Debug logging
        print(f"[SCRIPT_PROMPT] Using {len(photos)} photos for grounding:")
        for idx, p in enumerate(photos[:3], start=1):  # Log first 3
            print(f"  Photo {idx}: scene_type={p.get('scene_type')}, caption={p.get('caption')[:50]}...")
        if len(photos) > 3:
            print(f"  ... and {len(photos) - 3} more photos")
    
    if mode == 'outline':
        prompt = f"""Generate a structured outline for a YouTube video titled: "{topic}".

**CORE REQUIREMENTS:**
- Deliver exactly {image_count} distinct scene headings.
- Each heading must be a concise, hook-driven title for the scene (3-8 words).
- Focus on visual and narrative progression.
{real_estate_context}

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
        # Real estate-specific prompt templates
        if video_type == 'listing' and (property_address or property_type):
            # Property listing video script
            property_desc = []
            if property_address:
                property_desc.append(property_address)
            if property_type:
                property_desc.append(f"{property_type.replace('_', ' ')}")
            if bedrooms is not None and bathrooms is not None:
                property_desc.append(f"{bedrooms}BR/{bathrooms}BA")
            if property_price:
                property_desc.append(f"R{property_price:,.0f}")
            
            property_summary = " ".join(property_desc)
            features_list = ", ".join([f.replace('_', ' ') for f in property_features]) if property_features else "modern amenities"

            # If we have analysed photos, ground the script in those photos instead
            if photos and photos_block:
                # Build property intro with address - clean it up
                property_intro = property_address or property_summary or topic
                if not property_intro or len(property_intro.strip()) < 3:
                    property_intro = "this property"
                else:
                    # Clean up address - remove any trailing duplicates
                    property_intro = property_intro.strip()
                    # Remove common duplications like "Street Street" or "Gardens Gardens"
                    words = property_intro.split()
                    if len(words) > 1 and words[-1].lower() == words[-2].lower():
                        property_intro = " ".join(words[:-1])
                
                # Calculate time per scene (30 seconds per scene)
                def get_time_range(scene_num: int, total: int) -> str:
                    start_sec = (scene_num - 1) * 30
                    end_sec = scene_num * 30
                    start_min = start_sec // 60
                    start_sec_remainder = start_sec % 60
                    end_min = end_sec // 60
                    end_sec_remainder = end_sec % 60
                    return f"{start_min}:{start_sec_remainder:02d}-{end_min}:{end_sec_remainder:02d}"
                
                # Build allowed features list from property details
                allowed_features = []
                if property_features:
                    allowed_features.extend([f.replace('_', ' ') for f in property_features])
                if bedrooms is not None:
                    allowed_features.append(f"{bedrooms} bedrooms")
                if bathrooms is not None:
                    allowed_features.append(f"{bathrooms} bathrooms")
                if square_feet:
                    allowed_features.append(f"{square_feet} square metres")
                allowed_features_str = ", ".join(allowed_features) if allowed_features else "none specified"
                
                prompt = f"""You are a South African real-estate video scriptwriter. Generate a COMPLETE property listing video script with ALL {len(photos)} scenes in one response.

**PROPERTY INFORMATION:**
Address: {property_intro}
{real_estate_context}

**ALLOWED PROPERTY FEATURES (ONLY mention these if they appear in photos):**
{allowed_features_str}

**PHOTOS PROVIDED ({len(photos)} photos in exact order):**
{photos_block}

**YOUR TASK:**
Generate ALL {len(photos)} scenes NOW. Write one scene per photo, in the exact order listed above. Each scene must describe the PROPERTY STRUCTURE and PERMANENT FEATURES visible in that photo.

**OUTPUT FORMAT - Generate ALL scenes immediately (NO Visuals line, NO notes at the end):**

Scene 1 ({get_time_range(1, len(photos))}): [Title based on Photo 1's scene_type and caption]
**Content/Narration:** [2-4 sentences describing the PROPERTY STRUCTURE and PERMANENT FEATURES visible in Photo 1. Reference specific architectural details, finishes, or permanent fixtures from the caption. Start with "Welcome to {property_intro}" or similar. DO NOT mention furniture, decor, or temporary items.]

Scene 2 ({get_time_range(2, len(photos))}): [Title based on Photo 2's scene_type and caption]
**Content/Narration:** [2-4 sentences describing the PROPERTY STRUCTURE and PERMANENT FEATURES visible in Photo 2. Reference specific architectural details, finishes, or permanent fixtures from the caption. DO NOT mention furniture, decor, or temporary items.]

Scene 3 ({get_time_range(3, len(photos))}): [Title based on Photo 3's scene_type and caption]
**Content/Narration:** [2-4 sentences describing the PROPERTY STRUCTURE and PERMANENT FEATURES visible in Photo 3. Reference specific architectural details, finishes, or permanent fixtures from the caption. DO NOT mention furniture, decor, or temporary items.]

[Continue for ALL {len(photos)} scenes - do not stop until you have written Scene {len(photos)}]

**CRITICAL RULES:**
1. Generate ALL {len(photos)} scenes in ONE response. Do NOT stop after Scene 1.
2. Do NOT ask questions, wait for confirmation, or say "let me know when to proceed".
3. Use property address "{property_intro}" in Scene 1 only (e.g., "Welcome to {property_intro}").
4. **FORBIDDEN - DO NOT INCLUDE OR MENTION:**
   - "Visuals:" line (photos are already provided, no need to describe them)
   - Any notes, meta-commentary, or explanations at the end (e.g., "Note: I've written...")
   - **Furniture** (couches, sofas, chairs, tables, beds, mattresses, desks, etc.)
   - **Electronics** (televisions, TVs, flat screen TVs, computers, monitors, speakers, etc.)
   - **Appliances** (microwaves, ovens, refrigerators, dishwashers, washing machines, etc.) - UNLESS they are built-in permanent fixtures
   - **Decor items** (pictures, paintings, vases, rugs, curtains, blinds, etc.)
   - **Temporary items** (personal belongings, clothing, books, plants, etc.)
   - **Features NOT in the property details** (e.g., if balcony is not listed, DO NOT mention it)
   - **ANYTHING that can be moved or removed** - only describe permanent, built-in features
5. **ONLY MENTION:**
   - Property structure (rooms, layout, size, ceiling height, windows, doors)
   - Permanent fixtures (built-in cabinets, countertops, sinks, bathtubs, showers, lighting fixtures)
   - Architectural features (exposed beams, archways, built-in storage)
   - Finishes (flooring type, wall finishes, tile work)
   - Features from property details IF they appear in the photo (e.g., if "balcony" is in property features AND visible in photo)
6. Each scene MUST reference specific details from that photo's caption about STRUCTURE/FINISHES only.
7. Do NOT invent rooms, features, or amenities not in the photo captions OR property details.
8. Use professional South African real-estate language (Rands, m², suburbs, estates, complexes).
9. **END CLEANLY**: After Scene {len(photos)}, stop immediately. Do NOT add any notes, explanations, or meta-commentary.

**EXAMPLE OF WHAT TO DESCRIBE:**
- "This spacious living room features high ceilings, large windows that flood the space with natural light, and elegant tile flooring."
- "The modern kitchen boasts sleek countertops, built-in cabinetry, and a functional layout perfect for cooking."
- "The bathroom features a large mirror, modern fixtures, and quality tiling throughout."

**EXAMPLE OF WHAT NOT TO DESCRIBE:**
- "The plush couch invites you to relax" ❌ (furniture - can be moved)
- "The large television provides entertainment" ❌ (electronics - can be removed)
- "featuring a flat screen TV" ❌ (electronics - temporary item)
- "The microwave and microwave oven" ❌ (appliances - can be moved)
- "A beautiful balcony with stunning views" ❌ (if balcony not in property details)
- "The elegant curtains frame the windows" ❌ (decor - can be removed)

**REMEMBER: When selling a property, buyers are purchasing the STRUCTURE and PERMANENT FEATURES, not the furniture or temporary items. Focus ONLY on what stays with the property.**

**OUTPUT FORMAT REMINDER:**
- Each scene has ONLY two lines: "Scene X (time): Title" followed by "**Content/Narration:** [text]"
- NO "Visuals:" line (photos are the visuals)
- NO notes or explanations at the end
- Stop immediately after Scene {len(photos)}

**START WRITING ALL SCENES NOW - DO NOT STOP UNTIL SCENE {len(photos)} IS COMPLETE:**
"""
            else:
                # Fallback: generic listing template (no photo grounding)
                prompt = f"""Write a complete real estate property listing video script for: {property_summary}

**VIDEO SPECIFICATIONS:**
- Target Audience: Home buyers and real estate investors
- Tone: Professional, inviting, and descriptive. Highlight the property's best features.
- Number of Scenes: {image_count}
{f'- Approximate Total Word Count: {word_count}' if word_count else ''}
{real_estate_context}

**SCENE STRUCTURE FOR PROPERTY LISTINGS:**
Scene 1: Exterior/Introduction - Welcome viewers and introduce the property
Scene 2-3: Living spaces - Living room, dining area
Scene 4: Kitchen - Highlight modern features
Scene 5-6: Bedrooms - Showcase bedrooms and bathrooms
Scene 7: Additional features - Backyard, garage, special amenities
Scene 8: Neighborhood/Location - Surrounding area and amenities
Scene 9: Summary/Call to action - Recap key features and contact information

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
- Highlight property features naturally in the narration
- Use professional real estate language (e.g., "spacious", "well-appointed", "stunning")

**PROPERTY FEATURES TO HIGHLIGHT:** {features_list}
**TOPIC:** {topic}
"""
        
        elif video_type == 'neighborhood_guide':
            prompt = f"""Write a complete neighborhood guide video script for: {topic}

**VIDEO SPECIFICATIONS:**
- Target Audience: Potential home buyers and residents
- Tone: Informative, welcoming, and community-focused
- Number of Scenes: {image_count}
{f'- Approximate Total Word Count: {word_count}' if word_count else ''}
{real_estate_context}

**SCENE STRUCTURE FOR NEIGHBORHOOD GUIDES:**
Scene 1: Introduction - Welcome to the neighborhood
Scene 2-3: Location & Accessibility - Transportation, proximity to major areas
Scene 4-5: Schools & Education - Local schools and educational opportunities
Scene 6-7: Parks & Recreation - Parks, community centers, outdoor activities
Scene 8: Shopping & Dining - Local businesses, restaurants, shopping areas
Scene 9: Real Estate Overview - Types of homes, price ranges, market trends
Scene 10: Summary - Why this neighborhood is great

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
- Include specific, helpful information about the neighborhood
- Use engaging, community-focused language

**TOPIC:** {topic}
"""
        
        elif video_type == 'market_update':
            prompt = f"""Write a complete real estate market update video script for: {topic}

**VIDEO SPECIFICATIONS:**
- Target Audience: Home buyers, sellers, and real estate investors
- Tone: Professional, data-driven, and informative
- Number of Scenes: {image_count}
{f'- Approximate Total Word Count: {word_count}' if word_count else ''}
{real_estate_context}

**SCENE STRUCTURE FOR MARKET UPDATES:**
Scene 1: Introduction - Current market overview
Scene 2-3: Market Trends - Price trends, inventory levels
Scene 4-5: Sales Activity - Recent sales, days on market
Scene 6-7: Price Analysis - Average prices, price per square foot
Scene 8: Market Forecast - Predictions and trends
Scene 9: Advice for Buyers/Sellers - Actionable insights
Scene 10: Summary - Key takeaways

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
- Include data and statistics where relevant
- Use professional, authoritative language

**TOPIC:** {topic}
"""
        
        else:
            # Default script mode (general purpose)
            prompt = f"""Write a complete YouTube video script based on the title: "{topic}".

**VIDEO SPECIFICATIONS:**
- Target Audience: General audience (4th-grade reading level)
- Tone: Curiosity-driven, educational, and YouTube-safe.
- Number of Scenes: {image_count}
{f'- Approximate Total Word Count: {word_count}' if word_count else ''}
{real_estate_context}

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
    """Ensure script starts at Scene 1 and has proper Scene structure, and remove trailing notes."""
    if not text:
        return text
    
    # Find first Scene marker
    scene_match = re.search(r'Scene\s+1[\s:]', text, re.IGNORECASE)
    if scene_match:
        scene_index = scene_match.start()
        if scene_index > 0:
            text = text[scene_index:]
            print(f'Removed intro text, script now starts with: {text[:50]}...')
    
    # Find last Scene marker and remove everything after it that looks like notes/meta-commentary
    scene_matches = list(re.finditer(r'Scene\s+\d+[\s:]', text, re.IGNORECASE))
    if scene_matches:
        last_scene_match = scene_matches[-1]
        # Find the end of the last scene's Content/Narration section
        # Look for patterns like "Note:", "I've written", "according to", etc. after the last scene
        note_patterns = [
            r'\n\s*Note:.*$',
            r'\n\s*I\'ve written.*$',
            r'\n\s*according to.*$',
            r'\n\s*This script.*$',
        ]
        for pattern in note_patterns:
            note_match = re.search(pattern, text[last_scene_match.end():], re.IGNORECASE | re.DOTALL)
            if note_match:
                text = text[:last_scene_match.end() + note_match.start()]
                print(f'Removed trailing note/meta-commentary')
                break
    
    # Validate that we have Scene structure
    scene_count = len(re.findall(r'Scene\s+\d+', text, re.IGNORECASE))
    if scene_count == 0:
        print('⚠️  WARNING: No Scene markers found in generated script!')
        print(f'First 200 chars: {text[:200]}')
    else:
        print(f'✓ Found {scene_count} Scene markers in generated script')
    
    return text.strip()


def _estimate_max_tokens(word_count: int, mode: str, image_count: int = 10) -> int:
    """Rough estimate of tokens required for Groq completions."""
    if mode == 'outline':
        return 1024
    # For photo-grounded scripts, we need more tokens (each scene is ~150-200 tokens)
    # Base estimate: word_count * 1.5, plus extra for multiple scenes
    base_tokens = max(512, int(word_count * 1.5))
    # Add extra tokens for each scene (roughly 200 tokens per scene)
    scene_tokens = image_count * 200
    total = base_tokens + scene_tokens
    # Groq LLaMA models support up to 8192 tokens, but be conservative
    return min(6144, total)

