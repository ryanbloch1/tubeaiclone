#!/usr/bin/env python3
"""Test script for free image generation."""

import os
from utils.image_generation import (
    analyze_script_for_scenes, 
    generate_image_prompt, 
    generate_image_free,
    get_available_services
)

def test_image_generation():
    """Test the free image generation functionality."""
    
    print("🧪 Testing Free Image Generation")
    print("=" * 50)
    
    # Test 1: Check available services
    print("\n1. Checking available services...")
    services = get_available_services()
    for service in services:
        print(f"   • {service['name']}: {service['status']}")
    
    # Test 2: Analyze a sample script
    print("\n2. Testing script analysis...")
    sample_script = """
    Scene 1: Introduction to Space Exploration
    
    Welcome to our journey through the cosmos. Today we'll explore the wonders of space exploration and the incredible technology that makes it possible.
    
    Scene 2: The Technology Behind Space Travel
    
    From powerful rockets to advanced satellites, the technology behind space travel has evolved dramatically over the decades.
    
    Scene 3: Future of Space Exploration
    
    As we look to the future, new technologies like AI and robotics are revolutionizing how we explore the universe.
    """
    
    scenes = analyze_script_for_scenes(sample_script)
    print(f"   Found {len(scenes)} scenes:")
    for scene in scenes:
        print(f"   • Scene {scene['scene_number']}: {scene['description']}")
    
    # Test 3: Generate prompts
    print("\n3. Testing prompt generation...")
    for scene in scenes:
        prompt = generate_image_prompt(scene["text"], scene["scene_number"])
        print(f"   Scene {scene['scene_number']} prompt: {prompt[:80]}...")
    
    # Test 4: Generate a test image
    print("\n4. Testing image generation...")
    
    # Create output directory
    os.makedirs("output/images", exist_ok=True)
    
    # Test with a simple prompt
    test_prompt = "Professional video scene: space, technology, future, high quality, cinematic"
    output_path = "output/images/test_image.png"
    
    print(f"   Generating image with prompt: {test_prompt}")
    success = generate_image_free(test_prompt, output_path)
    
    if success:
        print(f"   ✅ Image generated successfully: {output_path}")
        print(f"   📁 File size: {os.path.getsize(output_path)} bytes")
    else:
        print("   ❌ Image generation failed")
    
    print("\n🎉 Test completed!")

if __name__ == "__main__":
    test_image_generation() 