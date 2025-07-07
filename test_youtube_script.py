#!/usr/bin/env python3
"""
Test XTTS with a YouTube-style script.
"""

import os
from TTS.api import TTS

def test_youtube_script():
    """Test XTTS with a longer YouTube-style script."""
    
    print("🎬 Testing XTTS with YouTube-style script...")
    
    # YouTube-style script (about 1-2 minutes of content)
    youtube_script = """
    Welcome to today's video! In this comprehensive guide, we're going to explore the fascinating world of artificial intelligence and how it's revolutionizing content creation.
    
    Whether you're a creator, developer, or just curious about the future of technology, this video has something for everyone. We'll cover everything from basic concepts to advanced applications that are changing the industry.
    
    So grab your favorite beverage, get comfortable, and let's dive deep into the world of AI-powered content creation. Trust me, by the end of this video, you'll have a whole new perspective on what's possible.
    
    Don't forget to like, subscribe, and hit that notification bell if you want to stay updated with our latest content. Now, let's get started!
    """
    
    # Clean up the script
    youtube_script = youtube_script.strip().replace('\n', ' ')
    
    print(f"📝 Script length: {len(youtube_script)} characters")
    print(f"📝 Estimated duration: ~{len(youtube_script.split()) * 0.4:.1f} seconds")
    
    try:
        # Load XTTS model
        print("🤖 Loading XTTS model...")
        tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
        
        # Output path
        output_path = "youtube_voiceover.wav"
        
        # Generate voiceover
        print("🎤 Generating YouTube-style voiceover...")
        print("⏱️  This may take a few minutes for longer content...")
        
        tts.tts_to_file(
            text=youtube_script,
            file_path=output_path,
            speaker_wav="voice_sample.wav",
            language="en"
        )
        
        # Check result
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            duration_seconds = file_size / (16000 * 2)  # Rough estimate for WAV
            print(f"✅ Success! YouTube voiceover saved: {output_path}")
            print(f"📊 File size: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")
            print(f"⏱️  Estimated duration: {duration_seconds:.1f} seconds")
            print(f"🎵 You can play it with: afplay {output_path}")
            return True
        else:
            print("❌ File was not created")
            return False
            
    except Exception as e:
        print(f"❌ Error generating YouTube voiceover: {e}")
        return False

if __name__ == "__main__":
    success = test_youtube_script()
    if success:
        print("\n🎉 YouTube-style voiceover generation successful!")
        print("🎬 Your AI voiceover is ready for video production!")
    else:
        print("\n💥 YouTube voiceover generation failed") 