#!/usr/bin/env python3
"""
Test Hugging Face Image Generation
Generate images from a sample script using Hugging Face.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from utils.image_generation import generate_images_huggingface_only

def test_huggingface_generation():
    """Test Hugging Face image generation with a sample script."""
    
    print("🤗 Testing Hugging Face Image Generation")
    print("=" * 50)
    
    # Check if API key is loaded
    api_key = os.getenv('HUGGINGFACE_API_KEY')
    if api_key:
        print(f"✅ Hugging Face API key loaded: {api_key[:10]}...")
    else:
        print("❌ No Hugging Face API key found in .env file")
        return
    
    # Sample script with scenes
    sample_script = """
    Scene 1: Introduction to Coffee Making
    
    Welcome to the art of brewing the perfect cup of coffee. Today we'll explore the essential techniques and tools needed to create a delicious coffee experience at home.
    
    Scene 2: Coffee Beans and Grinding
    
    The journey begins with selecting high-quality coffee beans. We'll learn about different bean varieties and the importance of proper grinding techniques for optimal flavor extraction.
    
    Scene 3: Brewing Methods
    
    From pour-over to French press, we'll explore various brewing methods that can transform your coffee experience. Each method offers unique characteristics and flavors.
    
    Scene 4: Perfect Cup
    
    Finally, we'll discover the secrets to achieving the perfect balance of flavor, aroma, and body in every cup of coffee you brew.
    """
    
    print("📝 Sample Script:")
    print(sample_script)
    print("\n" + "="*50)
    
    # Create output directory
    output_dir = "output/test_huggingface"
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"🎨 Generating images with Hugging Face...")
    print(f"📁 Output directory: {output_dir}")
    
    # Generate images
    try:
        generated_images = generate_images_huggingface_only(
            script=sample_script,
            output_dir=output_dir
        )
        
        if generated_images:
            print(f"\n✅ Successfully generated {len(generated_images)} images!")
            print("\n📁 Generated images:")
            for i, image_path in enumerate(generated_images, 1):
                print(f"   {i}. {image_path}")
        else:
            print("\n❌ No images were generated.")
            
    except Exception as e:
        print(f"\n❌ Error during image generation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_huggingface_generation() 