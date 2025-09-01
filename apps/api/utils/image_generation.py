"""Hugging Face image generation helpers used by the FastAPI endpoint."""

import os
from typing import Optional

# All scene parsing/prompt helpers removed – frontend handles this now.

def generate_image_huggingface(prompt: str, output_path: str, api_key: Optional[str] = None) -> bool:
    """
    Generate an image using ONLY the Hugging Face Inference Providers API
    exactly as requested (InferenceClient with provider + model).
    """
    from huggingface_hub import InferenceClient  # raises if missing

    token = api_key or os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_API_KEY")
    if not token:
        print("Missing HF_TOKEN. Set HF_TOKEN in your environment.")
        return False

    provider = os.getenv("HF_PROVIDER", "replicate")
    model = os.getenv("HF_IMAGE_MODEL", "Qwen/Qwen-Image")

    try:
        client = InferenceClient(provider=provider, api_key=token)
        # output is a PIL.Image object
        image = client.text_to_image(prompt, model=model)
        image.save(output_path)
        return True
    except Exception as e:
        print(f"Hugging Face InferenceClient error: {e}")
        return False

def create_mock_image(*args, **kwargs) -> bool:  # retained only to avoid import churn
    return False

def generate_image_free(prompt: str, output_path: str) -> bool:
    """
    Generate an image using ONLY Hugging Face Inference Providers API.
    """
    print("Using Hugging Face Inference Providers…")
    return generate_image_huggingface(prompt, output_path)

def generate_images_for_script(*args, **kwargs):  # legacy alias kept to avoid import errors
    return []

def generate_images_huggingface_only(script: str, output_dir: str = "output/images") -> List[str]:
    # Backwards compatible alias
    return generate_images_for_script(script, output_dir)

def get_available_services():
    return [{"name": "Hugging Face Inference Providers"}]
