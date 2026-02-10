"""
Photo analysis service using a free, local BLIP vision model.

This runs entirely on your machine (no external API calls) and can use the
Apple Silicon GPU (MPS) on an M2 Mac if available.
"""

from typing import Dict, List
import io

import torch
from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration


def _get_device() -> torch.device:
    """
    Prefer Apple Silicon GPU (MPS) when available, otherwise fall back to CPU.
    """
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():  # type: ignore[attr-defined]
        return torch.device("mps")
    return torch.device("cpu")


DEVICE = _get_device()
_processor: BlipProcessor | None = None
_model: BlipForConditionalGeneration | None = None


def _load_model() -> tuple[BlipProcessor, BlipForConditionalGeneration]:
    """
    Lazily load the BLIP model and processor once per process.
    """
    global _processor, _model
    if _processor is None or _model is None:
        print(f"[PHOTO_ANALYSIS] Loading BLIP model on {DEVICE}...")
        _processor = BlipProcessor.from_pretrained("salesforce/blip-image-captioning-base")
        _model = BlipForConditionalGeneration.from_pretrained(
            "salesforce/blip-image-captioning-base"
        ).to(DEVICE)
        print("[PHOTO_ANALYSIS] BLIP model loaded")
    return _processor, _model


SCENE_KEYWORDS: Dict[str, List[str]] = {
    "kitchen": ["kitchen", "stove", "oven", "cooktop", "countertop"],
    "living_room": ["living room", "lounge", "sofa", "couch", "tv", "fireplace"],
    "bedroom": ["bedroom", "bed", "headboard"],
    "bathroom": ["bathroom", "shower", "bathtub", "toilet", "sink", "vanity"],
    "balcony": ["balcony", "patio", "terrace", "veranda"],
    "view": ["view", "mountain", "sea", "ocean", "harbour", "harbor", "city skyline"],
    "exterior": ["building", "house", "street", "garden", "yard", "driveway", "garage"],
}


def _infer_scene_type(caption: str) -> str:
    """
    Infer a coarse scene_type from the caption text using simple keyword rules.
    """
    text = caption.lower()
    for scene, keywords in SCENE_KEYWORDS.items():
        if any(k in text for k in keywords):
            return scene

    # Fallback guesses
    if "inside" in text or "interior" in text:
        return "interior"
    return "exterior"


def _extract_features(caption: str) -> List[str]:
    """
    Extract a small list of descriptive feature phrases from the caption.
    This is intentionally simple and cheap – we just split on commas and
    common joiners like 'with' and 'featuring'.
    """
    text = caption
    for token in [" with ", " featuring ", " and "]:
        text = text.replace(token, ", ")
    parts = [p.strip() for p in text.split(",") if p.strip()]
    # Drop very short fragments
    return [p for p in parts if len(p.split()) >= 2]


def analyse_image_bytes(image_bytes: bytes) -> Dict:
    """
    Run BLIP on raw image bytes and return a structured analysis dict:

    {
        "caption": "...",
        "scene_type": "...",
        "features": [...],
        "confidence": 1.0
    }
    """
    processor, model = _load_model()

    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    inputs = processor(image, return_tensors="pt").to(DEVICE)
    with torch.no_grad():
        output_ids = model.generate(**inputs, max_new_tokens=64)

    caption = processor.decode(output_ids[0], skip_special_tokens=True)
    scene_type = _infer_scene_type(caption)
    features = _extract_features(caption)

    return {
        "caption": caption,
        "scene_type": scene_type,
        "features": features,
        "confidence": 1.0,
    }


