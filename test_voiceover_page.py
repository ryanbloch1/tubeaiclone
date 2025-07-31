#!/usr/bin/env python3
"""
Test script for voiceover generation page functionality
"""

import os
import sys
import time
from pathlib import Path

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_voice_sample_upload():
    """Test voice sample upload functionality"""
    print("🧪 Testing voice sample upload...")
    
    # Check if voice sample exists
    voice_sample_path = "voice_sample.wav"
    if os.path.exists(voice_sample_path):
        file_size = os.path.getsize(voice_sample_path) / 1024
        print(f"✅ Voice sample found: {voice_sample_path}")
        print(f"📊 File size: {file_size:.1f} KB")
        return True
    else:
        print("❌ No voice sample found")
        print("💡 Please upload a voice sample first")
        return False

def test_xtts_availability():
    """Test if XTTS is available and working"""
    print("\n🧪 Testing XTTS availability...")
    
    try:
        from utils.xtts_voice_generator import XTTSVoiceGenerator
        print("✅ XTTS voice generator imported successfully")
        
        # Test model loading
        generator = XTTSVoiceGenerator("voice_sample.wav")
        print("✅ XTTSVoiceGenerator created successfully")
        
        # Test model loading
        if generator.load_model():
            print("✅ XTTS model loaded successfully")
            return True
        else:
            print("❌ Failed to load XTTS model")
            return False
            
    except ImportError as e:
        print(f"❌ XTTS not available: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing XTTS: {e}")
        return False

def test_voiceover_generation():
    """Test actual voiceover generation"""
    print("\n🧪 Testing voiceover generation...")
    
    # Test script
    test_script = "Hello, this is a test of the voiceover generation system. How does it sound?"
    
    try:
        from utils.xtts_voice_generator import XTTSVoiceGenerator
        
        # Create output directory
        os.makedirs("output/test_voiceovers", exist_ok=True)
        
        # Generate voiceover
        generator = XTTSVoiceGenerator("voice_sample.wav")
        
        if not generator.load_model():
            print("❌ Could not load XTTS model")
            return False
        
        output_path = f"output/test_voiceovers/test_voiceover_{int(time.time())}.wav"
        
        print(f"🎤 Generating voiceover for: '{test_script}'")
        print(f"📁 Output path: {output_path}")
        
        result = generator.generate_voiceover(test_script, output_path)
        
        if result and os.path.exists(result):
            file_size = os.path.getsize(result) / 1024
            print(f"✅ Voiceover generated successfully!")
            print(f"📊 File: {result}")
            print(f"📊 Size: {file_size:.1f} KB")
            return True
        else:
            print("❌ Voiceover generation failed")
            return False
            
    except Exception as e:
        print(f"❌ Error during voiceover generation: {e}")
        return False

def test_app_components():
    """Test app components and dependencies"""
    print("\n🧪 Testing app components...")
    
    # Test required modules
    try:
        import streamlit as st
        print("✅ Streamlit available")
    except ImportError:
        print("❌ Streamlit not available")
        return False
    
    try:
        from utils.voiceover import estimate_voiceover_duration
        print("✅ Voiceover utilities available")
    except ImportError:
        print("❌ Voiceover utilities not available")
        return False
    
    try:
        from utils.sanitization import sanitize_script
        print("✅ Script sanitization available")
    except ImportError:
        print("❌ Script sanitization not available")
        return False
    
    return True

def main():
    """Run all tests"""
    print("🚀 Starting voiceover page tests...\n")
    
    tests = [
        ("App Components", test_app_components),
        ("Voice Sample Upload", test_voice_sample_upload),
        ("XTTS Availability", test_xtts_availability),
        ("Voiceover Generation", test_voiceover_generation),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"📋 {test_name}")
        print("-" * 50)
        
        try:
            result = test_func()
            results.append((test_name, result))
            
            if result:
                print(f"✅ {test_name} PASSED\n")
            else:
                print(f"❌ {test_name} FAILED\n")
                
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}\n")
            results.append((test_name, False))
    
    # Summary
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Voiceover page should work correctly.")
    else:
        print("⚠️ Some tests failed. Check the issues above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 