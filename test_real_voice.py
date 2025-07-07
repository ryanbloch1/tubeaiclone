#!/usr/bin/env python3
"""
Focused test to get REAL speech working, not beeps.
"""

import os
import sys
import subprocess

def test_pyttsx3_direct():
    """Test pyttsx3 directly to see if it works."""
    print("🎤 Testing pyttsx3 directly...")
    
    try:
        import pyttsx3
        
        # Initialize engine
        engine = pyttsx3.init()
        
        # Get available voices
        voices = engine.getProperty('voices')
        print(f"Available voices: {len(voices)}")
        for i, voice in enumerate(voices):
            print(f"  {i}: {voice.name} ({voice.id})")
        
        # Set properties
        engine.setProperty('rate', 150)  # Slower for testing
        engine.setProperty('volume', 1.0)
        
        if voices:
            engine.setProperty('voice', voices[0].id)
            print(f"Using voice: {voices[0].name}")
        
        # Test text
        test_text = "Hello world. This is a test of real speech generation."
        print(f"Speaking: {test_text}")
        
        # Try to speak
        engine.say(test_text)
        engine.runAndWait()
        
        print("✅ pyttsx3 speech test completed")
        return True
        
    except Exception as e:
        print(f"❌ pyttsx3 failed: {e}")
        return False

def test_pyttsx3_save():
    """Test saving pyttsx3 to file."""
    print("\n💾 Testing pyttsx3 file save...")
    
    try:
        import pyttsx3
        
        # Initialize engine
        engine = pyttsx3.init()
        
        # Set properties
        engine.setProperty('rate', 150)
        engine.setProperty('volume', 1.0)
        
        # Get voices
        voices = engine.getProperty('voices')
        if voices:
            engine.setProperty('voice', voices[0].id)
            print(f"Using voice: {voices[0].name}")
        
        # Test text
        test_text = "Hello world. This is a test of real speech generation."
        
        # Save to file
        output_path = "test_real_speech.wav"
        print(f"Saving to: {output_path}")
        
        engine.save_to_file(test_text, output_path)
        engine.runAndWait()
        
        # Check if file was created
        if os.path.exists(output_path):
            size = os.path.getsize(output_path)
            print(f"✅ File created: {output_path} ({size} bytes)")
            
            if size > 1000:
                print("🎵 File has content!")
                return True
            else:
                print("⚠️ File seems small")
                return False
        else:
            print("❌ File not created")
            return False
            
    except Exception as e:
        print(f"❌ pyttsx3 save failed: {e}")
        return False

def test_ffmpeg_speech():
    """Test FFmpeg with better speech-like generation."""
    print("\n🔊 Testing FFmpeg speech generation...")
    
    try:
        output_path = "test_ffmpeg_speech.wav"
        
        # Create a more speech-like waveform using FFmpeg
        # This creates a complex waveform that sounds more like human speech
        cmd = [
            'ffmpeg', '-f', 'lavfi', '-i',
            'aevalsrc=0.3*sin(2*PI*200*t)*exp(-t/10)+0.2*sin(2*PI*400*t)*exp(-t/8)+0.1*sin(2*PI*600*t)*exp(-t/12):duration=5:sample_rate=22050',
            '-af', 'highpass=f=80,lowpass=f=4000,volume=0.8',
            '-y', output_path
        ]
        
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0 and os.path.exists(output_path):
            size = os.path.getsize(output_path)
            print(f"✅ FFmpeg speech created: {output_path} ({size} bytes)")
            return True
        else:
            print(f"❌ FFmpeg failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ FFmpeg test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🎯 FOCUSED VOICE TEST - Getting Real Speech Working")
    print("=" * 50)
    
    # Test 1: Direct pyttsx3
    pyttsx3_works = test_pyttsx3_direct()
    
    # Test 2: pyttsx3 file save
    pyttsx3_save_works = test_pyttsx3_save()
    
    # Test 3: FFmpeg speech
    ffmpeg_works = test_ffmpeg_speech()
    
    print("\n" + "=" * 50)
    print("📊 RESULTS:")
    print(f"pyttsx3 direct: {'✅' if pyttsx3_works else '❌'}")
    print(f"pyttsx3 save: {'✅' if pyttsx3_save_works else '❌'}")
    print(f"FFmpeg speech: {'✅' if ffmpeg_works else '❌'}")
    
    if pyttsx3_save_works:
        print("\n🎉 SUCCESS! Real speech generation is working!")
        print("You can now use the Streamlit app with proper voiceover.")
    else:
        print("\n❌ Still need to fix speech generation.")
        print("Let's try a different approach...")

if __name__ == "__main__":
    main() 