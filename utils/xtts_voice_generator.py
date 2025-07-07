#!/usr/bin/env python3
"""
XTTS Voice Generator Module
High-quality local voice cloning using Coqui XTTS.
"""

import os
import time
import subprocess
from pathlib import Path
from typing import Optional, Tuple

# Try to import XTTS
try:
    from TTS.api import TTS
    XTTS_AVAILABLE = True
except ImportError:
    XTTS_AVAILABLE = False
    print("Warning: XTTS not available. Install with: pip install TTS")

class XTTSVoiceGenerator:
    """High-quality voice generation using Coqui XTTS with voice cloning."""
    
    def __init__(self, voice_sample_path: str = "voice_sample.wav"):
        """
        Initialize XTTS voice generator.
        
        Args:
            voice_sample_path: Path to voice sample for cloning
        """
        self.voice_sample_path = voice_sample_path
        self.tts = None
        self.model_loaded = False
        
        # Check if voice sample exists
        if not os.path.exists(voice_sample_path):
            print(f"Warning: Voice sample not found at {voice_sample_path}")
            print("Please provide a voice sample for voice cloning.")
    
    def load_model(self) -> bool:
        """
        Load the XTTS model.
        
        Returns:
            bool: True if model loaded successfully
        """
        if not XTTS_AVAILABLE:
            print("Error: XTTS not available. Please install TTS package.")
            return False
        
        try:
            print("🤖 Loading XTTS model...")
            self.tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
            self.model_loaded = True
            print("✅ XTTS model loaded successfully!")
            return True
        except Exception as e:
            print(f"❌ Failed to load XTTS model: {e}")
            return False
    
    def generate_voiceover(self, script: str, output_path: str, language: str = "en") -> Optional[str]:
        """
        Generate voiceover using XTTS with voice cloning.
        
        Args:
            script: Text to convert to speech
            output_path: Path to save the audio file
            language: Language code (default: "en")
            
        Returns:
            str: Path to generated audio file, or None if failed
        """
        if not self.model_loaded:
            if not self.load_model():
                return None
        
        if not script or not script.strip():
            print("Error: No script provided")
            return None
        
        # Ensure output directory exists
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            print(f"🎤 Generating voiceover with XTTS...")
            print(f"📝 Script length: {len(script)} characters")
            print(f"🎯 Voice sample: {self.voice_sample_path}")
            
            # Generate voiceover
            self.tts.tts_to_file(
                text=script,
                file_path=str(output_path),
                speaker_wav=self.voice_sample_path,
                language=language
            )
            
            # Verify file was created
            if output_path.exists():
                file_size = output_path.stat().st_size
                print(f"✅ Voiceover generated successfully!")
                print(f"📊 File: {output_path}")
                print(f"📊 Size: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")
                return str(output_path)
            else:
                print("❌ Voiceover file was not created")
                return None
                
        except Exception as e:
            print(f"❌ Error generating voiceover: {e}")
            return None
    
    def estimate_duration(self, script: str) -> float:
        """
        Estimate the duration of the generated voiceover.
        
        Args:
            script: Text to estimate duration for
            
        Returns:
            float: Estimated duration in seconds
        """
        words = len(script.split())
        # XTTS typically generates at ~150 words per minute
        duration_minutes = words / 150
        return duration_minutes * 60
    
    def get_processing_info(self) -> dict:
        """
        Get information about XTTS processing capabilities.
        
        Returns:
            dict: Processing information
        """
        return {
            "available": XTTS_AVAILABLE,
            "model_loaded": self.model_loaded,
            "voice_sample_exists": os.path.exists(self.voice_sample_path),
            "voice_sample_path": self.voice_sample_path,
            "features": [
                "High-quality voice cloning",
                "Multi-language support",
                "Local processing (no internet required)",
                "Free to use",
                "Commercial use allowed"
            ]
        }

def create_voice_sample_from_audio(input_path: str, output_path: str = "voice_sample.wav") -> bool:
    """
    Convert an audio file to the format required by XTTS.
    
    Args:
        input_path: Path to input audio file
        output_path: Path to save converted voice sample
        
    Returns:
        bool: True if conversion successful
    """
    try:
        # Convert to WAV format with appropriate sample rate for XTTS
        cmd = [
            'ffmpeg', '-i', input_path,
            '-ar', '22050',  # Sample rate
            '-ac', '1',      # Mono
            '-y',            # Overwrite output
            output_path
        ]
        
        print(f"🔄 Converting {input_path} to voice sample...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print(f"✅ Voice sample created: {output_path}")
            return True
        else:
            print(f"❌ FFmpeg conversion failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error creating voice sample: {e}")
        return False

def test_xtts_setup() -> bool:
    """
    Test if XTTS is properly set up and working.
    
    Returns:
        bool: True if XTTS is working
    """
    print("🧪 Testing XTTS setup...")
    
    # Check if XTTS is available
    if not XTTS_AVAILABLE:
        print("❌ XTTS not available")
        return False
    
    # Check if voice sample exists
    voice_sample = "voice_sample.wav"
    if not os.path.exists(voice_sample):
        print(f"❌ Voice sample not found: {voice_sample}")
        return False
    
    # Try to load model
    generator = XTTSVoiceGenerator(voice_sample)
    if not generator.load_model():
        print("❌ Failed to load XTTS model")
        return False
    
    # Test with a short script
    test_script = "Hello, this is a test of the XTTS voice generation system."
    test_output = "test_xtts_output.wav"
    
    print("🎤 Testing voice generation...")
    result = generator.generate_voiceover(test_script, test_output)
    
    if result and os.path.exists(test_output):
        print("✅ XTTS test successful!")
        # Clean up test file
        try:
            os.remove(test_output)
        except:
            pass
        return True
    else:
        print("❌ XTTS test failed")
        return False

if __name__ == "__main__":
    # Test the XTTS setup
    success = test_xtts_setup()
    if success:
        print("\n🎉 XTTS is ready for integration!")
    else:
        print("\n💥 XTTS setup needs attention") 