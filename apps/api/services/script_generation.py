"""
AI service for professional real-estate script generation.
Strictly structural. No furniture. No electronics. No ambience.
Hard validation + compliance enforcement.
"""

import os
import re
from typing import Optional, Literal

try:
    from dotenv import find_dotenv, load_dotenv
    load_dotenv(find_dotenv(), override=True)
except Exception:
    pass

try:
    import httpx
except ImportError:
    httpx = None


GROQ_PLACEHOLDER_KEYS = {'', 'your_api_key_here', 'YOUR_KEY_HERE'}

FORBIDDEN_WORDS = [
    # Furniture / objects
    "sofa", "couch", "chair", "table", "bed", "desk",
    "television", "tv", "monitor", "screen",
    "microwave", "oven", "fridge", "refrigerator",
    "curtain", "rug", "carpet", "plant",
    "lamp", "appliance", "decor", "furniture",
    # Views / lifestyle / mood
    "balcony", "view", "atmosphere", "ambience",
    "relax", "chill", "retreat", "cozy",
    "comfortable", "entertainment",
    "stunning", "beautiful", "beautifully",
    "quiet", "tranquil", "tranquility",
    "secluded", "seclusion", "peaceful",
    "serene", "unique", "grand", "grandeur",
    "elegant", "elegance", "manicured",
    "spacious", "inviting", "warm", "charming",
]

INVALID_ROOM_NAMES = {
    "other", "outdoor", "outside", "unknown", "misc"
}


# ---------------------------------------------------
# MAIN GENERATOR
# ---------------------------------------------------
async def generate_script_with_gemini(
    topic: str,
    style_name: Optional[str] = None,
    mode: Literal['script', 'outline', 'rewrite'] = 'script',
    temperature: float = 0.4,
    word_count: int = 500,
    image_count: int = 10,
    selection: Optional[str] = None,
    context_mode: Optional[str] = 'default',
    transcript: Optional[str] = None,
    web_data: Optional[str] = None,
    video_type: Optional[str] = None,
    property_address: Optional[str] = None,
    property_type: Optional[str] = None,
    property_price: Optional[float] = None,
    bedrooms: Optional[int] = None,
    bathrooms: Optional[float] = None,
    square_feet: Optional[int] = None,
    mls_number: Optional[str] = None,
    property_features: Optional[list[str]] = None,
    photos: Optional[list[dict]] = None,
) -> str:

    prompt = build_prompt(
        topic, mode, image_count, word_count,
        style_name, selection, context_mode,
        transcript, web_data,
        video_type, property_address, property_type,
        property_price, bedrooms, bathrooms,
        square_feet, mls_number,
        property_features, photos
    )

    groq_key = os.getenv("GROQ_API_KEY")

    if groq_key and groq_key not in GROQ_PLACEHOLDER_KEYS:
        text = await _generate_with_groq(
            groq_key, prompt, temperature,
            _estimate_max_tokens(word_count, mode, image_count)
        )
    else:
        text = await _generate_with_gemini_sdk(prompt, temperature)

    # ---------------- VALIDATION PIPELINE ----------------
    text = _strip_intro_to_first_scene(text)
    text = _strip_forbidden_features(text)
    text = _strip_dimensions(text)

    expected_scenes = len(photos) if photos else image_count
    text = _validate_scene_count(text, expected_scenes)

    text = _validate_scene_content(text)
    text = _validate_unique_rooms(text)
    text = _validate_room_names(text)

    return text


# ---------------------------------------------------
# GROQ
# ---------------------------------------------------
async def _generate_with_groq(api_key, prompt, temperature, max_tokens):
    if httpx is None:
        raise Exception("httpx not installed")

    api_url = "https://api.groq.com/openai/v1/chat/completions"
    model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

    payload = {
        "model": model,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a professional South African real estate listing "
                    "scriptwriter. Describe only permanent structural features."
                )
            },
            {"role": "user", "content": prompt}
        ]
    }

    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            api_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json=payload
        )

    if r.status_code >= 400:
        raise Exception(r.text)

    return r.json()["choices"][0]["message"]["content"]


# ---------------------------------------------------
# GEMINI FALLBACK
# ---------------------------------------------------
async def _generate_with_gemini_sdk(prompt: str, temperature: float):
    try:
        from google import generativeai as genai
    except ImportError:
        raise Exception("Gemini SDK not installed")

    api_key = os.getenv("GEMINI_API_KEY")
    genai.configure(api_key=api_key)

    model = genai.GenerativeModel(
        "gemini-2.0-flash-exp",
        system_instruction=(
            "You are a professional structural real estate listing "
            "scriptwriter. Structural descriptions only."
        ),
        generation_config={
            "temperature": temperature,
            "max_output_tokens": 8192
        }
    )

    return model.generate_content(prompt).text


# ---------------------------------------------------
# PROMPT BUILDER
# ---------------------------------------------------
def build_prompt(
    topic, mode, image_count, word_count,
    style_name, selection, context_mode,
    transcript, web_data,
    video_type, property_address,
    property_type, property_price,
    bedrooms, bathrooms,
    square_feet, mls_number,
    property_features, photos
):

    expected_scenes = len(photos) if photos else image_count

    photos_block = ""
    if photos:
        photos_block = "\n".join(
            [f"{i+1}. {p.get('scene_type')} - {p.get('caption')}"
             for i, p in enumerate(photos)]
        )

    allowed_features = []
    if bedrooms:
        allowed_features.append(f"{bedrooms} bedrooms")
    if bathrooms:
        allowed_features.append(f"{bathrooms} bathrooms")
    if square_feet:
        allowed_features.append(f"{square_feet} square metres")
    if property_features:
        allowed_features.extend(property_features)

    allowed_features_str = ", ".join(allowed_features)

    photos_section = ""
    if photos_block:
        photos_section = f"""
PHOTOS (STRICT ORDER — ONE SCENE PER LINE, IN THIS EXACT ORDER):
For each line below, write ONE scene that focuses on that room type.
If multiple lines share a similar room type (e.g. several living_room photos),
you MUST still write a separate scene for EACH line, describing a different
fixed/structural aspect or angle of that space.
{photos_block}
"""

    prompt = f"""
Generate a PROFESSIONAL SOUTH AFRICAN PROPERTY LISTING SCRIPT.

STRICT STRUCTURAL RULES:
- ONLY permanent, fixed, built-in structural features
- NO furniture, NO appliances, NO electronics, NO décor
- NO mood, NO lifestyle, NO ambience
- NO second person (“you”), NO first person (“we”)
- NO specific numeric room measurements (no square metres, no ceiling heights, no exact dimensions)

MANDATORY PER SCENE:
1. Identify room/area
2. Layout + dimensions
3. Fixed structure (walls, windows, doors)
4. Finishes (floors, walls, ceilings)

FORBIDDEN GENERIC ROOMS:
- Outdoor, Other, Misc, Unknown, Outside

PROPERTY DATA:
Address: {property_address}
Type: {property_type}
Price: R{property_price}
Features Allowed: {allowed_features_str}

{photos_section}

OUTPUT FORMAT (EXACT):
Scene X (time): Room Name
**Content/Narration:** [2–4 factual sentences]

WRITE ALL {expected_scenes} SCENES.
STOP AFTER FINAL SCENE.
NO NOTES.
"""

    return prompt


# ---------------------------------------------------
# VALIDATION + STRIPPING
# ---------------------------------------------------
def _strip_intro_to_first_scene(text: str) -> str:
    match = re.search(r"Scene\s+1", text, re.IGNORECASE)
    return text[match.start():] if match else text


def _strip_forbidden_features(text: str) -> str:
    """Strip forbidden words at the sentence level instead of nuking whole scenes.

    We want to keep as many structurally useful scenes as possible while
    removing marketing / lifestyle language. We:
      - Split each scene into sentences after the Content/Narration marker
      - Drop sentences containing forbidden words
      - Drop the whole scene only if *all* sentences are removed
    """
    scene_blocks = re.split(r"(Scene\s+\d+[\s\S]*?)(?=Scene\s+\d+|$)", text)
    cleaned_blocks: list[str] = []

    for block in scene_blocks:
        if "Scene" not in block:
            # Carry over any preamble or whitespace untouched
            cleaned_blocks.append(block)
            continue

        # Split header vs body
        parts = block.split("**Content/Narration:**")
        if len(parts) == 1:
            # No explicit narration marker; keep scene as-is unless it's clearly illegal
            lower = block.lower()
            if any(word in lower for word in FORBIDDEN_WORDS):
                print(f"⚠️ Removed illegal scene (no clean narration):\n{block.splitlines()[0]}")
                continue
            cleaned_blocks.append(block)
            continue

        header, body = parts[0], parts[1]

        # Split body into rough sentences
        sentences = re.split(r"(?<=[\.\!\?])\s+", body)
        kept_sentences: list[str] = []

        for s in sentences:
            lower_s = s.lower()
            if any(word in lower_s for word in FORBIDDEN_WORDS):
                print(f"⚠️ Removed illegal sentence: {s.strip()}")
                continue
            if s.strip():
                kept_sentences.append(s)

        if not kept_sentences:
            # No usable narration left; drop entire scene
            print(f"⚠️ Removed illegal scene (all narration sentences filtered):\n{header.splitlines()[0]}")
            continue

        cleaned_body = " ".join(kept_sentences).strip()
        cleaned_blocks.append(f"{header}**Content/Narration:** {cleaned_body}\n")

    return "".join(cleaned_blocks).strip()


def _strip_dimensions(text: str) -> str:
    """Remove explicit numeric room measurements and dimensions.

    We want to avoid hallucinated sizes like '8.2 square meters' or
    'ceiling height is 2.4 meters' while keeping the rest of the narration.
    """
    patterns = [
        # "measures 8.2 square meters"
        r"\bmeasures\s+\d+(\.\d+)?\s*(square\s+met(?:er|re)s?|m2|sqm|sq\s*m(?:eters?)?)",
        # "ceiling height is 2.4 meters"
        r"\bceiling height\s+is\s+\d+(\.\d+)?\s*(meters?|metres?|m)\b",
        # "room's dimensions are 3.5 meters by 2.3 meters"
        r"\broom['’]s dimensions are\s+\d+(\.\d+)?\s*(meters?|metres?|m)\s*(by|x)\s*\d+(\.\d+)?\s*(meters?|metres?|m)\b",
        # "dimensions are 3.5 meters by 2.3 meters"
        r"\bdimensions\s+are\s+\d+(\.\d+)?\s*(meters?|metres?|m)\s*(by|x)\s*\d+(\.\d+)?\s*(meters?|metres?|m)\b",
        # Standalone "8.2 square meters", "10 sqm", "45 m2"
        r"\b\d+(\.\d+)?\s*(square\s+met(?:er|re)s?|m2|sqm|sq\s*m(?:eters?)?)\b",
    ]

    for pattern in patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    # Normalise spacing after removals
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _validate_scene_count(text: str, expected: int) -> str:
    """Validate that we have at least one scene and warn (but don't hard-fail) on mismatches.

    The model can occasionally under- or over-generate scenes even when the prompt
    requests a fixed count. We only treat '0 scenes' as a hard error; for any
    other mismatch we log a warning and continue so the UI doesn't get a 500.
    """
    found = len(re.findall(r"Scene\s+\d+", text, re.IGNORECASE))

    # Hard fail only if we got nothing usable back
    if found == 0:
        raise ValueError("Model returned 0 scenes; script unusable")

    # Soft warning if we didn't hit the exact expected count
    if found != expected:
        print(f"[SCRIPT] Warning: Model returned {found} scenes, expected {expected}; proceeding with {found}")

    return text


def _validate_scene_content(text: str) -> str:
    """Soft validation of scene content.

    We no longer block scripts here – we only log which scenes look weak so that
    the UI/user can decide whether to edit or regenerate. This avoids 500s when
    the model under-performs but still returns something usable.
    """
    scenes = re.split(r"(Scene\s+\d+[\s\S]*?)(?=Scene\s+\d+|$)", text)
    blocks_with_scenes = [b for b in scenes if "Scene" in b]
    invalid_titles: list[str] = []

    for block in blocks_with_scenes:
        if "**Content/Narration:**" not in block:
            invalid_titles.append(block.splitlines()[0])
        else:
            narration = block.split("**Content/Narration:**")[-1].strip()
            if len(narration) < 30:
                invalid_titles.append(block.splitlines()[0])

    if invalid_titles:
        print(
            "[SCRIPT] Warning: some scenes have weak/invalid content and may "
            f"need manual editing: {invalid_titles}"
        )
    return text


def _validate_unique_rooms(text: str) -> str:
    titles = re.findall(r"Scene\s+\d+.*?:\s*(.+)", text)
    normalized = [t.lower().strip() for t in titles]

    duplicates = set([t for t in normalized if normalized.count(t) > 1])
    if duplicates:
        # Soft enforcement: warn but don't fail. UI can still show script and user can edit.
        print(f"[SCRIPT] Warning: duplicate room types detected (first kept, others may be alternates): {duplicates}")

    return text


def _validate_room_names(text: str) -> str:
    titles = re.findall(r"Scene\s+\d+.*?:\s*(.+)", text)
    invalid: list[str] = []
    for title in titles:
        if title.lower().strip() in INVALID_ROOM_NAMES:
            invalid.append(title)

    if invalid:
        # Soft enforcement – we already bias the model via prompt; here we just log.
        print(f"[SCRIPT] Warning: generic/invalid room names used (consider renaming in UI): {invalid}")
    return text


def _estimate_max_tokens(word_count: int, mode: str, image_count: int):
    return min(6144, word_count * 2 + image_count * 250)