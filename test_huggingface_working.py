#!/usr/bin/env python3
"""
Test Working Hugging Face Image Generation
Use a different approach that definitely works.
"""

import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_huggingface_working():
    """Test Hugging Face with a working model."""
    
    print("🤗 Testing Working Hugging Face Image Generation")
    print("=" * 60)
    
    # Check API key
    api_key = os.getenv('HUGGINGFACE_API_KEY')
    if not api_key:
        print("❌ No Hugging Face API key found")
        return
    
    print(f"✅ API key loaded: {api_key[:10]}...")
    
    # Use a model that's definitely available
    model_id = "prompthero/openjourney"  # This model is available and works
    
    url = f"https://api-inference.huggingface.co/models/{model_id}"
    headers = {"Authorization": f"Bearer {api_key}"}
    
    # Test prompt
    test_prompt = "Professional video scene: coffee brewing, high quality, cinematic lighting"
    
    print(f"🎨 Testing with model: {model_id}")
    print(f"📝 Prompt: {test_prompt}")
    
    # Create output directory
    output_dir = "output/huggingface_working"
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        print("\n🔄 Sending request to Hugging Face...")
        
        response = requests.post(
            url,
            headers=headers,
            json={"inputs": test_prompt}
        )
        
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            # Save the image
            output_path = os.path.join(output_dir, "test_image.png")
            with open(output_path, "wb") as f:
                f.write(response.content)
            
            print(f"✅ Image generated successfully!")
            print(f"📁 Saved to: {output_path}")
            print(f"📊 File size: {os.path.getsize(output_path)} bytes")
            
            return True
            
        elif response.status_code == 503:
            print("⚠️  Model is loading. This is normal for the first request.")
            print("💡 The model will be ready in a few minutes.")
            return False
            
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"📄 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

if __name__ == "__main__":
    test_huggingface_working() 