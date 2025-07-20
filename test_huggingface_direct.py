#!/usr/bin/env python3
"""
Test Hugging Face Direct Usage
Use Hugging Face models directly without API keys.
"""

import os
import torch
from diffusers import StableDiffusionPipeline
from PIL import Image

def test_huggingface_direct():
    """Test using Hugging Face models directly."""
    
    print("🤗 Testing Hugging Face Direct Usage")
    print("=" * 50)
    
    try:
        # Check if we have the required libraries
        print("📦 Checking dependencies...")
        
        # Try to import diffusers
        try:
            from diffusers import StableDiffusionPipeline
            print("✅ diffusers library available")
        except ImportError:
            print("❌ diffusers library not installed")
            print("💡 Install with: pip install diffusers transformers accelerate")
            return
        
        # Check for CUDA/GPU
        if torch.cuda.is_available():
            print("🚀 CUDA GPU available - will use GPU acceleration")
            device = "cuda"
        else:
            print("💻 Using CPU (slower but works)")
            device = "cpu"
        
        # Create output directory
        output_dir = "output/huggingface_direct"
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"\n🎨 Loading Stable Diffusion model...")
        print("⏳ This may take a few minutes on first run...")
        
        # Load the model
        model_id = "runwayml/stable-diffusion-v1-5"
        pipe = StableDiffusionPipeline.from_pretrained(
            model_id,
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
            safety_checker=None
        )
        pipe = pipe.to(device)
        
        print("✅ Model loaded successfully!")
        
        # Test prompts
        test_prompts = [
            "Professional video scene: coffee brewing, high quality, cinematic lighting",
            "Professional video scene: coffee beans, grinding, high quality, detailed",
            "Professional video scene: pour-over coffee, brewing methods, high quality",
            "Professional video scene: perfect cup of coffee, steam rising, high quality"
        ]
        
        print(f"\n🎨 Generating {len(test_prompts)} images...")
        
        for i, prompt in enumerate(test_prompts, 1):
            print(f"\n📝 Generating image {i}: {prompt[:50]}...")
            
            # Generate image
            image = pipe(prompt, num_inference_steps=20).images[0]
            
            # Save image
            output_path = os.path.join(output_dir, f"direct_image_{i}.png")
            image.save(output_path)
            
            print(f"✅ Image {i} saved to: {output_path}")
        
        print(f"\n🎉 Successfully generated {len(test_prompts)} images!")
        print(f"📁 Check the images in: {output_dir}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 If you get import errors, install the required packages:")
        print("pip install diffusers transformers accelerate")

if __name__ == "__main__":
    test_huggingface_direct() 