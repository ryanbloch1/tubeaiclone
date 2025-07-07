#!/usr/bin/env python3
"""
Clean test for Coqui TTS with XTTS models.
"""

import os
import TTS
from TTS.api import TTS as TTSCore

def test_coqui_tts():
    """Test Coqui TTS with XTTS models."""
    
    print("🎤 Testing Coqui TTS...")
    print(f"TTS version: {TTS.__version__}")
    
    # List available models (ModelManager -> list)
    print("\n📋 Available models:")
    model_manager = TTSCore().list_models()
    model_list = model_manager.list_models()
    
    # Find XTTS models
    xtts_models = [m for m in model_list if 'xtts' in m.lower()]
    
    print(f"Total models: {len(model_list)}")
    print(f"XTTS models found: {len(xtts_models)}")
    
    if xtts_models:
        print("XTTS models:")
        for i, model in enumerate(xtts_models[:5]):  # Show first 5
            print(f"  {i+1}: {model}")
        
        # Test with first XTTS model
        test_model = xtts_models[0]
        print(f"\n🧪 Testing with model: {test_model}")
        
        try:
            # Load the model
            print("Loading model...")
            tts_model = TTSCore(test_model)
            
            # Test text
            test_text = "Hello! This is a test of Coqui TTS XTTS. If you hear this, it works perfectly!"
            
            # Output path
            output_path = "coqui_xtts_test.wav"
            
            # Generate speech
            print(f"Generating speech: '{test_text}'")
            tts_model.tts_to_file(text=test_text, file_path=output_path, speaker_wav="voice_sample.wav", language="en")
            
            # Check result
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                print(f"✅ Success! File saved: {output_path} ({file_size} bytes)")
                return True
            else:
                print("❌ File was not created")
                return False
                
        except Exception as e:
            print(f"❌ Error testing XTTS: {e}")
            return False
    else:
        print("❌ No XTTS models found")
        return False

if __name__ == "__main__":
    success = test_coqui_tts()
    if success:
        print("\n🎉 Coqui TTS XTTS is working!")
    else:
        print("\n💥 Coqui TTS XTTS test failed") 