#!/usr/bin/env python3
"""
Test XTTS integration with Streamlit app structure.
"""

import os
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

def test_xtts_integration():
    """Test XTTS integration with the app structure."""
    
    print("🧪 Testing XTTS integration with Streamlit app...")
    
    # Test 1: Import XTTS voice generator
    try:
        from utils.xtts_voice_generator import XTTSVoiceGenerator
        print("✅ XTTS voice generator imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import XTTS voice generator: {e}")
        return False
    
    # Test 2: Check voice sample
    voice_sample_path = "voice_sample.wav"
    if not os.path.exists(voice_sample_path):
        print(f"❌ Voice sample not found: {voice_sample_path}")
        return False
    print(f"✅ Voice sample found: {voice_sample_path}")
    
    # Test 3: Initialize generator
    try:
        generator = XTTSVoiceGenerator(voice_sample_path)
        print("✅ XTTS generator initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize XTTS generator: {e}")
        return False
    
    # Test 4: Get processing info
    try:
        info = generator.get_processing_info()
        print("✅ Processing info retrieved:")
        for key, value in info.items():
            if key != "features":
                print(f"   {key}: {value}")
        print("   Features:")
        for feature in info["features"]:
            print(f"     - {feature}")
    except Exception as e:
        print(f"❌ Failed to get processing info: {e}")
        return False
    
    # Test 5: Test voiceover generation
    test_script = "This is a test of the XTTS integration with the Streamlit application. The voice generation should work seamlessly with the main app."
    test_output = "test_streamlit_xtts_output.wav"
    
    print(f"🎤 Testing voiceover generation...")
    print(f"📝 Script: {test_script}")
    
    try:
        result = generator.generate_voiceover(test_script, test_output)
        if result and os.path.exists(test_output):
            file_size = os.path.getsize(test_output)
            print(f"✅ Voiceover generated successfully!")
            print(f"📊 File: {test_output}")
            print(f"📊 Size: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")
            
            # Clean up test file
            try:
                os.remove(test_output)
                print("🧹 Test file cleaned up")
            except:
                pass
            
            return True
        else:
            print("❌ Voiceover generation failed")
            return False
    except Exception as e:
        print(f"❌ Error during voiceover generation: {e}")
        return False

def test_voiceover_module_integration():
    """Test integration with the main voiceover module."""
    
    print("\n🧪 Testing voiceover module integration...")
    
    try:
        from utils.voiceover import generate_voiceover_coqui_xtts
        print("✅ XTTS function imported from voiceover module")
    except ImportError as e:
        print(f"❌ Failed to import XTTS function: {e}")
        return False
    
    # Test XTTS generation through voiceover module
    test_script = "Testing the XTTS integration through the voiceover module. This should work seamlessly with the Streamlit app."
    test_output = "test_voiceover_module_output.wav"
    
    try:
        success = generate_voiceover_coqui_xtts(test_script, test_output)
        if success and os.path.exists(test_output):
            file_size = os.path.getsize(test_output)
            print(f"✅ Voiceover module integration successful!")
            print(f"📊 File: {test_output}")
            print(f"📊 Size: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")
            
            # Clean up test file
            try:
                os.remove(test_output)
                print("🧹 Test file cleaned up")
            except:
                pass
            
            return True
        else:
            print("❌ Voiceover module integration failed")
            return False
    except Exception as e:
        print(f"❌ Error during voiceover module test: {e}")
        return False

if __name__ == "__main__":
    print("🎬 Testing XTTS Integration with Streamlit App")
    print("=" * 50)
    
    # Test XTTS integration
    xtts_success = test_xtts_integration()
    
    # Test voiceover module integration
    module_success = test_voiceover_module_integration()
    
    print("\n" + "=" * 50)
    if xtts_success and module_success:
        print("🎉 All tests passed! XTTS is ready for Streamlit integration!")
        print("🚀 You can now run the Streamlit app with XTTS voice generation.")
    else:
        print("💥 Some tests failed. Please check the setup.")
        if not xtts_success:
            print("   - XTTS integration needs attention")
        if not module_success:
            print("   - Voiceover module integration needs attention") 