#!/usr/bin/env python3
"""
Test Multiple Hugging Face Models
Find a model that actually works on the Inference API.
"""

import os
import requests
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_model(model_id, api_key):
    """Test a specific model."""
    url = f"https://api-inference.huggingface.co/models/{model_id}"
    headers = {"Authorization": f"Bearer {api_key}"}
    
    test_prompt = "a simple coffee cup"
    
    try:
        print(f"🔄 Testing {model_id}...")
        response = requests.post(
            url,
            headers=headers,
            json={"inputs": test_prompt},
            timeout=30
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"   ✅ SUCCESS! {model_id} works!")
            return True
        elif response.status_code == 503:
            print(f"   ⏳ Loading... {model_id} is loading (normal)")
            return "loading"
        else:
            print(f"   ❌ Failed: {response.text[:100]}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def find_working_model():
    """Find a working Hugging Face model."""
    
    print("🔍 Finding Working Hugging Face Models")
    print("=" * 60)
    
    api_key = os.getenv('HUGGINGFACE_API_KEY')
    if not api_key:
        print("❌ No API key found")
        return None
    
    print(f"✅ API key loaded: {api_key[:10]}...")
    
    # List of models to test (these should be available)
    models_to_test = [
        "stabilityai/stable-diffusion-2-1",
        "runwayml/stable-diffusion-v1-5",
        "CompVis/stable-diffusion-v1-4",
        "prompthero/openjourney",
        "stabilityai/stable-diffusion-xl-base-1.0",
        "stabilityai/sdxl-turbo",
        "stabilityai/stable-diffusion-2",
        "runwayml/stable-diffusion-inpainting",
        "stabilityai/stable-diffusion-2-inpainting"
    ]
    
    working_models = []
    
    for model_id in models_to_test:
        result = test_model(model_id, api_key)
        if result == True:
            working_models.append(model_id)
        elif result == "loading":
            # Try again after a short wait
            time.sleep(2)
            result = test_model(model_id, api_key)
            if result == True:
                working_models.append(model_id)
        
        time.sleep(1)  # Be nice to the API
    
    print(f"\n" + "="*60)
    if working_models:
        print(f"🎉 Found {len(working_models)} working models:")
        for model in working_models:
            print(f"   ✅ {model}")
        return working_models[0]  # Return the first working one
    else:
        print("❌ No working models found")
        return None

if __name__ == "__main__":
    working_model = find_working_model()
    if working_model:
        print(f"\n🚀 Use this model: {working_model}")
    else:
        print("\n💡 Try these alternatives:")
        print("   1. Use mock images for testing")
        print("   2. Get a Stability AI API key")
        print("   3. Use local models with diffusers") 