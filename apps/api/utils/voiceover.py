"""Voiceover module: generates a voiceover audio file using Hugging Face path only (no paid APIs)."""

import os
import requests
import json
import time
from pathlib import Path
import subprocess
import sys
import base64

# Legacy paid/cloud backends removed. We'll use local Coqui‑AI XTTS‑v2 via Hugging Face
# if available (TTS package), and fall back to offline system TTS (macOS say) or tone.
TTS_AVAILABLE = False
COQUI_AVAILABLE = False

# Colab XTTS client disabled (explicitly opting out)
COLAB_CLIENT_AVAILABLE = False

def generate_voiceover_elevenlabs(script, voice_id, output_path, api_key=None):
    """
    Generate a voiceover audio file from the script using ElevenLabs API.
    Args:
        script (str): The script to narrate.
        voice_id (str): ElevenLabs voice ID.
        output_path (str): Path to save the audio file.
        api_key (str): ElevenLabs API key.
    Returns:
        bool: True if successful, False otherwise.
    """
    # Disabled
    print("Skipping ElevenLabs (disabled)")
    return False
    
    # ElevenLabs API endpoint
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": api_key
    }
    
    data = {
        "text": script,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.5
        }
    }
    
    try:
        print(f"Generating voiceover with ElevenLabs voice {voice_id}...")
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code == 200:
            # Save the audio file
            with open(output_path, "wb") as f:
                f.write(response.content)
            print(f"Voiceover saved to: {output_path}")
            return True
        else:
            print(f"ElevenLabs API error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"Error generating ElevenLabs voiceover: {e}")
        return False

def generate_voiceover_google_tts(script, output_path, voice_name="en-US-Standard-A"):
    """
    Generate voiceover using Google Cloud TTS (free tier available).
    Args:
        script (str): The script to narrate.
        output_path (str): Path to save the audio file.
        voice_name (str): Google TTS voice name.
    Returns:
        bool: True if successful, False otherwise.
    """
    print("Skipping Google TTS (disabled)")
    return False

def generate_voiceover_azure_tts(script, output_path, voice_name="en-US-JennyNeural"):
    """
    Generate voiceover using Microsoft Azure TTS (free tier available).
    Args:
        script (str): The script to narrate.
        output_path (str): Path to save the audio file.
        voice_name (str): Azure TTS voice name.
    Returns:
        bool: True if successful, False otherwise.
    """
    print("Skipping Azure TTS (disabled)")
    return False

def generate_voiceover_huggingface_tts(script, output_path, voice_name="default"):
    """
    Generate voiceover using Hugging Face TTS (free).
    Args:
        script (str): The script to narrate.
        output_path (str): Path to save the audio file.
        voice_name (str): Voice name.
    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        print(f"Generating voiceover with Hugging Face TTS...")
        
        # Preferred: real XTTS v2 via local Hugging Face weights if TTS is installed
        speaker_wav = os.getenv("VOICE_SAMPLE_PATH", "voice_sample.wav")
        ok = generate_voiceover_xtts_hf(script, output_path, speaker_wav)
        if ok:
            return True
        # Fallback: macOS say or simple tone
        return create_huggingface_style_audio(script, output_path)
        
    except Exception as e:
        print(f"Error generating Hugging Face TTS voiceover: {e}")
        return False

def create_huggingface_style_audio(script, output_path):
    """
    Create real spoken audio locally on macOS using the built-in 'say' TTS,
    then convert to WAV via ffmpeg. This keeps everything free and offline.
    """
    try:
        import sys
        import subprocess
        import tempfile
        import os

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        if sys.platform == 'darwin':
            print("Using macOS 'say' for local speech synthesis...")
            with tempfile.NamedTemporaryFile(suffix='.aiff', delete=False) as tf:
                aiff_path = tf.name
            try:
                # Generate AIFF with system voice (choose a common voice)
                say_cmd = ['say', '-v', 'Samantha', '-r', '190', '-o', aiff_path, script]
                say_res = subprocess.run(say_cmd, capture_output=True, text=True)
                if say_res.returncode != 0 or not os.path.exists(aiff_path) or os.path.getsize(aiff_path) == 0:
                    print(f"say failed: rc={say_res.returncode}, stderr={say_res.stderr}")
                    # Fallback
                    return create_ultra_simple_audio(output_path, 10)

                # Convert AIFF to WAV (mono 22.05kHz)
                ffmpeg_cmd = [
                    'ffmpeg', '-y', '-i', aiff_path,
                    '-ar', '22050', '-ac', '1', str(output_path)
                ]
                ffm_res = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
                if ffm_res.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    print(f"Created speech audio: {output_path}")
                    return True
                else:
                    print(f"ffmpeg conversion failed: {ffm_res.stderr}")
                    return create_ultra_simple_audio(output_path, 10)
            finally:
                try:
                    os.unlink(aiff_path)
                except Exception:
                    pass
        else:
            # Non-macOS fallback: keep ultra simple tone to avoid external deps
            words = len(script.split())
            duration = max(2, min(words * 0.4, 60))
            print("Non-macOS detected; using simple audio fallback.")
            return create_ultra_simple_audio(output_path, duration)

    except Exception as e:
        print(f"Error creating spoken audio: {e}")
        return create_ultra_simple_audio(output_path, 10)

def _split_into_sentences(text: str) -> list[str]:
    import re
    # Simple sentence splitter; keeps it conservative
    parts = re.split(r"(?<=[\.!?])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]

def generate_voiceover_xtts_hf(script: str, output_path: str, speaker_wav: str, language: str = "en", force_cpu: bool = True) -> bool:
    """
    Generate real speech using Coqui‑AI XTTS‑v2 model loaded via Hugging Face (local).
    Requires the `TTS` package and PyTorch. Uses CPU by default for stability on macOS.
    """
    try:
        from TTS.api import TTS as COQUI_TTS
        import torch
        import os
        os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")
        if not os.path.exists(speaker_wav) or os.path.getsize(speaker_wav) == 0:
            print(f"XTTS speaker_wav missing: {speaker_wav}")
            return False
        print("[XTTS] Loading coqui‑ai/XTTS‑v2 (local)…")
        tts = COQUI_TTS("tts_models/multilingual/multi-dataset/xtts_v2")
        # Force CPU on macOS to avoid MPS kernel limitations and ensure stability
        device = "cpu"
        try:
            tts = tts.to(device)
        except Exception:
            pass
        print(f"[XTTS] Using {device}")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Chunk long text to reduce drift and improve speed/memory
        sentences = _split_into_sentences(script)
        try:
            from pydub import AudioSegment
        except Exception:
            # If pydub not available, fall back to one-shot
            tts.tts_to_file(text=script, file_path=output_path, speaker_wav=speaker_wav, language=language)
            return os.path.exists(output_path) and os.path.getsize(output_path) > 0

        combined = AudioSegment.silent(duration=0)
        sample_rate = 22050
        import numpy as np
        from tempfile import NamedTemporaryFile

        for idx, sent in enumerate(sentences):
            if not sent:
                continue
            try:
                # Generate raw audio for the sentence
                wav = tts.tts(text=sent, speaker_wav=speaker_wav, language=language)
                # Convert numpy float waveform to pydub AudioSegment
                wav_np = np.array(wav)
                # Normalize to int16
                wav_int16 = np.clip(wav_np * 32767.0, -32768, 32767).astype(np.int16)
                # Write to temp WAV and load via pydub (simplest cross-platform path)
                with NamedTemporaryFile(suffix=".wav", delete=True) as tf:
                    import soundfile as sf
                    sf.write(tf.name, wav_int16, sample_rate, subtype='PCM_16')
                    seg = AudioSegment.from_wav(tf.name)
                combined += seg + AudioSegment.silent(duration=60)  # 60ms pause between sentences
            except Exception as se:
                print(f"[XTTS] Sentence synthesis failed at {idx}: {se}")
                continue

        if len(combined) == 0:
            return False
        combined.export(output_path, format="wav")
        ok = os.path.exists(output_path) and os.path.getsize(output_path) > 0
        print(f"[XTTS] Wrote (chunked): {output_path} -> {ok}")
        return ok
    except Exception as e:
        print(f"[XTTS] Error: {e}")
        return False

def generate_voiceover_local(script, output_path, voice_name="default"):
    """
    Generate a voiceover using local text-to-speech (pyttsx3).
    Args:
        script (str): The script to narrate.
        output_path (str): Path to save the audio file.
        voice_name (str): Voice name to use.
    Returns:
        bool: True if successful, False otherwise.
    """
    print("Skipping local TTS (disabled)")
    return False

def generate_voiceover_coqui_xtts(script, output_path, voice_name="default"):
    """
    Generate voiceover using Coqui XTTS (high-quality, free).
    Args:
        script (str): The script to narrate.
        output_path (str): Path to save the audio file.
        voice_name (str): Voice name or reference audio path.
    Returns:
        bool: True if successful, False otherwise.
    """
    print("Skipping Coqui XTTS (disabled)")
    return False

def generate_voiceover_coqui_simple(script, output_path, voice_name="default"):
    """
    Generate voiceover using Coqui TTS with simpler models (faster).
    Args:
        script (str): The script to narrate.
        output_path (str): Path to save the audio file.
        voice_name (str): Voice name.
    Returns:
        bool: True if successful, False otherwise.
    """
    print("Skipping Coqui simple (disabled)")
    return False

def generate_voiceover(script, voice_id="default", output_path=None, use_elevenlabs=True):
    """
    Generate a voiceover audio file from the script using multiple free APIs.
    Args:
        script (str): The script to narrate.
        voice_id (str): Voice ID or voice name.
        output_path (str): Path to save the audio file.
        use_elevenlabs (bool): Whether to try ElevenLabs first.
    Returns:
        str: Path to the generated audio file, or None if failed.
    """
    if not script or not script.strip():
        print("Error: No script provided for voiceover generation.")
        return None
    
    # Set default output path if not provided
    if not output_path:
        output_dir = Path("output/voiceovers")
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = int(time.time())
        output_path = output_dir / f"voiceover_{timestamp}.mp3"
    
    # Ensure output directory exists
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Prefer local XTTS‑v2 via Hugging Face (real speech)
    print("\nTrying Hugging Face (coqui‑ai XTTS‑v2) …")
    speaker_wav = voice_id if isinstance(voice_id, str) and os.path.exists(voice_id) else os.getenv("VOICE_SAMPLE_PATH", "voice_sample.wav")
    ok = generate_voiceover_xtts_hf(script, str(output_path), speaker_wav)
    if ok:
        return str(output_path)
    # Secondary: offline macOS say or tone
    print("\nFalling back to offline speech/tone…")
    ok2 = create_huggingface_style_audio(script, str(output_path))
    return str(output_path) if ok2 else None

def get_available_voices():
    """
    Get list of available voices from all services.
    Returns:
        dict: Dictionary with voice information.
    """
    # Hugging Face only
    return {
        "huggingface": {
            "Default": "default",
            "Female": "female",
            "Male": "male"
        }
    }

def estimate_voiceover_duration(script, words_per_minute=150):
    """
    Estimate the duration of a voiceover based on script length.
    Args:
        script (str): The script to estimate.
        words_per_minute (int): Average speaking rate.
    Returns:
        float: Estimated duration in seconds.
    """
    if not script:
        return 0
    
    # Count words
    words = len(script.split())
    
    # Calculate duration
    duration_minutes = words / words_per_minute
    duration_seconds = duration_minutes * 60
    
    return duration_seconds

def create_simple_audio_fallback(script, output_path):
    """
    Create a simple audio file as fallback when TTS fails.
    Args:
        script (str): The script text.
        output_path (str): Path to save the audio file.
    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        print("Creating simple audio fallback...")
        
        # Create a more speech-like audio file using ffmpeg
        import subprocess
        import os
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Calculate duration based on script length
        words = len(script.split())
        duration = words * 0.4  # 0.4 seconds per word (faster than TTS)
        duration = max(2, min(duration, 60))  # Between 2 and 60 seconds
        
        print(f"Creating {duration:.1f} second speech-like audio file...")
        
        # Create a more complex waveform that sounds more like speech
        # Use multiple frequencies and add some variation
        cmd = [
            'ffmpeg', '-f', 'lavfi', '-i', 
            f'aevalsrc=0.3*sin(2*PI*200*t)+0.2*sin(2*PI*400*t)+0.1*sin(2*PI*600*t):duration={duration}:sample_rate=22050', 
            '-af', 'highpass=f=50,lowpass=f=8000', '-y', str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            print(f"Speech-like audio fallback created: {output_path}")
            return True
        else:
            print(f"FFmpeg failed: {result.stderr}")
            # Try even simpler approach
            return create_ultra_simple_audio(output_path, duration)
            
    except Exception as e:
        print(f"Error creating audio fallback: {e}")
        return create_ultra_simple_audio(output_path, 10)

def create_ultra_simple_audio(output_path, duration=10):
    """
    Create the simplest possible audio file.
    """
    try:
        print("Creating ultra-simple audio file...")
        
        import os
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Create a simple sine wave with better parameters
        cmd = [
            'ffmpeg', '-f', 'lavfi', '-i', 
            f'aevalsrc=0.5*sin(2*PI*300*t):duration={duration}:sample_rate=22050', 
            '-y', str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        
        if result.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            print(f"Ultra-simple audio created: {output_path}")
            return True
        else:
            print(f"Ultra-simple audio failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"Error creating ultra-simple audio: {e}")
        return False
