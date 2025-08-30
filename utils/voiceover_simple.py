"""
Simplified voiceover generation for production deployment.
Uses only reliable TTS methods that work in containers.
"""

import os
import tempfile
import logging
import subprocess
import shutil
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_voiceover(script: str, voice_sample_path: str = None, output_path: str = None) -> str:
    """
    Generate voiceover using the most reliable method available.
    
    Args:
        script: Text to convert to speech
        voice_sample_path: Path to voice sample (optional for production)
        output_path: Output file path (optional, will create temp file if not provided)
    
    Returns:
        Path to generated audio file
    """
    
    if not output_path:
        # Create a temporary file for output
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            output_path = tmp.name
    
    logger.info(f"🎤 Generating voiceover for {len(script)} characters")

    # Optional override to force placeholder path (fast/local, no TTS)
    if os.getenv("VOICE_TTS_MODE", "").lower() == "placeholder":
        return _generate_placeholder_audio(script, output_path)
    
    try:
        # Try system TTS first (works on most systems)
        return _generate_system_tts(script, output_path)
    except Exception as e:
        logger.warning(f"System TTS failed: {e}")
        
        try:
            # Fallback: Generate a simple audio tone as placeholder
            return _generate_placeholder_audio(script, output_path)
        except Exception as e:
            logger.error(f"All TTS methods failed: {e}")
            raise RuntimeError(f"Could not generate voiceover: {e}")

def _generate_system_tts(script: str, output_path: str) -> str:
    """Generate TTS using system commands (macOS 'say', Linux espeak, etc.)"""
    
    # Try macOS 'say' command
    if _command_exists('say'):
        logger.info("🍎 Using macOS 'say' command")
        try:
            # Generate with macOS say command
            subprocess.run([
                'say', 
                '-o', output_path.replace('.wav', '.aiff'),  # say outputs AIFF
                script
            ], check=True, capture_output=True, timeout=8)
            
            # Convert AIFF to WAV if needed
            aiff_path = output_path.replace('.wav', '.aiff')
            if _command_exists('ffmpeg'):
                subprocess.run([
                    'ffmpeg', '-i', aiff_path, '-y', output_path
                ], check=True, capture_output=True, timeout=15)
                os.unlink(aiff_path)  # Remove temp AIFF file
            else:
                # Just use the AIFF file
                os.rename(aiff_path, output_path)
            
            logger.info(f"✅ Generated TTS using macOS 'say': {output_path}")
            return output_path
            
        except subprocess.CalledProcessError as e:
            logger.error(f"macOS 'say' failed: {e}")
            raise
    
    # Try Linux espeak
    elif _command_exists('espeak'):
        logger.info("🐧 Using Linux espeak")
        try:
            subprocess.run([
                'espeak', '-w', output_path, script
            ], check=True, capture_output=True, timeout=8)
            
            logger.info(f"✅ Generated TTS using espeak: {output_path}")
            return output_path
            
        except subprocess.CalledProcessError as e:
            logger.error(f"espeak failed: {e}")
            raise
    
    # Try Windows SAPI (if available)
    elif os.name == 'nt':
        logger.info("🪟 Attempting Windows SAPI")
        try:
            # This would require additional setup, skip for now
            raise RuntimeError("Windows SAPI not implemented in this version")
        except Exception as e:
            logger.error(f"Windows SAPI failed: {e}")
            raise
    
    else:
        raise RuntimeError("No system TTS commands available")

def _generate_placeholder_audio(script: str, output_path: str) -> str:
    """Generate a simple beep/tone as audio placeholder"""
    
    logger.info("🔊 Generating placeholder audio tone")
    
    # Calculate duration based on script length (rough estimate)
    estimated_duration = max(2, len(script) / 10)  # ~10 chars per second
    
    if _command_exists('ffmpeg'):
        try:
            # Generate a simple tone with ffmpeg
            subprocess.run([
                'ffmpeg', '-f', 'lavfi', 
                '-i', f'sine=frequency=800:duration={estimated_duration}',
                '-y', output_path
            ], check=True, capture_output=True, timeout=10)
            
            logger.info(f"✅ Generated placeholder tone: {output_path}")
            return output_path
            
        except subprocess.CalledProcessError as e:
            logger.error(f"ffmpeg tone generation failed: {e}")
    
    # Final fallback: create a minimal WAV file
    try:
        import wave
        import struct
        
        # Create a very basic WAV file with silence
        sample_rate = 44100
        duration_samples = int(sample_rate * estimated_duration)
        
        with wave.open(output_path, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            
            # Write silence (zeros)
            for _ in range(duration_samples):
                wav_file.writeframes(struct.pack('<h', 0))
        
        logger.info(f"✅ Generated silence placeholder: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Could not create placeholder audio: {e}")
        raise

def _command_exists(command: str) -> bool:
    """Check if a command exists in the system PATH without executing it"""
    return shutil.which(command) is not None

# For testing
if __name__ == "__main__":
    test_script = "Hello, this is a test of the simplified voiceover system."
    output_file = generate_voiceover(test_script)
    print(f"Generated test voiceover: {output_file}")
