#!/usr/bin/env python3
"""
Test Mock Image Generation
Generate mock images from a sample script (works immediately, no API keys needed).
"""

import os
from utils.image_generation import analyze_script_for_scenes, generate_image_prompt, create_mock_image

def test_mock_generation():
    """Test mock image generation with a sample script."""
    
    print("🎨 Testing Mock Image Generation (Instant & Free)")
    print("=" * 60)
    
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
    print("\n" + "="*60)
    
    # Create output directory
    output_dir = "output/test_mock"
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"🎨 Generating mock images...")
    print(f"📁 Output directory: {output_dir}")
    
    # Analyze script for scenes
    scenes = analyze_script_for_scenes(sample_script)
    
    if not scenes:
        print("❌ No scenes found in script")
        return
    
    print(f"✅ Found {len(scenes)} scenes in script")
    
    # Generate images for each scene
    generated_images = []
    
    for i, scene in enumerate(scenes):
        print(f"\n🎨 Processing scene {scene['scene_number']}...")
        
        # Generate prompt for this scene
        prompt = generate_image_prompt(scene["text"], scene["scene_number"])
        print(f"📝 Generated prompt: {prompt}")
        
        # Create output path
        import time
        timestamp = int(time.time())
        image_filename = f"scene_{scene['scene_number']:02d}_{timestamp}.png"
        image_path = os.path.join(output_dir, image_filename)
        
        # Generate mock image
        success = create_mock_image(prompt, image_path)
        
        if success and os.path.exists(image_path):
            generated_images.append(image_path)
            file_size = os.path.getsize(image_path)
            print(f"✅ Scene {scene['scene_number']} mock image generated successfully")
            print(f"📁 Saved to: {image_path}")
            print(f"📊 File size: {file_size} bytes")
        else:
            print(f"❌ Failed to generate mock image for scene {scene['scene_number']}")
    
    # Summary
    print(f"\n" + "="*60)
    if generated_images:
        print(f"🎉 Successfully generated {len(generated_images)} mock images!")
        print("\n📁 Generated images:")
        for i, image_path in enumerate(generated_images, 1):
            print(f"   {i}. {image_path}")
        print(f"\n💡 These mock images are perfect for testing your video workflow!")
        print(f"💡 You can now use them in your Streamlit app to test the complete pipeline.")
    else:
        print("❌ No images were generated.")

if __name__ == "__main__":
    test_mock_generation() 