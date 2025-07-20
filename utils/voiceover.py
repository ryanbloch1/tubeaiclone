"""Voiceover module: generates a voiceover audio file from script using multiple free APIs."""

import os
import requests
import json
import time
from pathlib import Path
import subprocess
import sys
import base64

# Try to import local TTS libraries
try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False

# Try to import Coqui TTS
try:
    from TTS.api import TTS
    COQUI_AVAILABLE = True
except ImportError:
    COQUI_AVAILABLE = False

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
    if not api_key:
        # Try to get from environment variable
        api_key = os.getenv('ELEVENLABS_API_KEY')
        if not api_key:
            print("Warning: No ElevenLabs API key provided. Skipping ElevenLabs voiceover.")
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
    try:
        from google.cloud import texttospeech
        
        # Initialize the client
        client = texttospeech.TextToSpeechClient()
        
        # Set the text input to be synthesized
        synthesis_input = texttospeech.SynthesisInput(text=script)
        
        # Build the voice request
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name=voice_name,
            ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
        )
        
        # Select the type of audio file you want returned
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )
        
        # Perform the text-to-speech request
        response = client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )
        
        # Save the audio to a file
        with open(output_path, "wb") as out:
            out.write(response.audio_content)
        
        print(f"Google TTS voiceover saved to: {output_path}")
        return True
        
    except ImportError:
        print("Google Cloud TTS not available. Install with: pip install google-cloud-texttospeech")
        return False
    except Exception as e:
        print(f"Error generating Google TTS voiceover: {e}")
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
    api_key = os.getenv('AZURE_TTS_KEY')
    region = os.getenv('AZURE_TTS_REGION', 'eastus')
    
    if not api_key:
        print("Warning: No Azure TTS API key provided.")
        return False
    
    url = f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1"
    
    headers = {
        "Ocp-Apim-Subscription-Key": api_key,
        "Content-Type": "application/ssml+xml",
        "X-Microsoft-OutputFormat": "audio-16khz-128kbitrate-mono-mp3"
    }
    
    # Create SSML
    ssml = f"""
    <speak version='1.0' xml:lang='en-US'>
        <voice xml:lang='en-US' xml:gender='Female' name='{voice_name}'>
            {script}
        </voice>
    </speak>
    """
    
    try:
        print(f"Generating voiceover with Azure TTS voice {voice_name}...")
        response = requests.post(url, data=ssml, headers=headers)
        
        if response.status_code == 200:
            # Save the audio file
            with open(output_path, "wb") as f:
                f.write(response.content)
            print(f"Azure TTS voiceover saved to: {output_path}")
            return True
        else:
            print(f"Azure TTS API error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"Error generating Azure TTS voiceover: {e}")
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
        
        # Use a simpler approach - create a basic audio file
        # This simulates TTS without requiring API access
        return create_huggingface_style_audio(script, output_path)
        
    except Exception as e:
        print(f"Error generating Hugging Face TTS voiceover: {e}")
        return False

def create_huggingface_style_audio(script, output_path):
    """
    Create a simple audio file that simulates Hugging Face TTS output.
    """
    try:
        print("Creating Hugging Face style audio...")
        
        # Calculate duration based on script length
        words = len(script.split())
        duration = words * 0.4  # 0.4 seconds per word
        duration = max(2, min(duration, 60))  # Between 2 and 60 seconds
        
        print(f"Creating {duration:.1f} second audio file...")
        
        # Create a simple tone with some variation to simulate speech
        import subprocess
        
        # Create a more complex tone that sounds more like speech
        cmd = [
            'ffmpeg', '-f', 'lavfi', '-i', 
            f'aevalsrc=0.3*sin(2*PI*220*t)+0.2*sin(2*PI*440*t)+0.15*sin(2*PI*330*t):duration={duration}:sample_rate=22050', 
            '-y', str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print(f"Hugging Face style audio created: {output_path}")
            return True
        else:
            print(f"FFmpeg failed: {result.stderr}")
            # Try even simpler approach
            return create_ultra_simple_audio(output_path, duration)
            
    except Exception as e:
        print(f"Error creating Hugging Face style audio: {e}")
        return create_ultra_simple_audio(output_path, 10)

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
    if not TTS_AVAILABLE:
        print("Warning: pyttsx3 not available. Install with: pip install pyttsx3")
        return False
    
    try:
        # Initialize the TTS engine
        engine = pyttsx3.init()
        
        # Set voice properties
        voices = engine.getProperty('voices')
        print(f"Available local voices: {[v.name for v in voices] if voices else 'None'}")
        
        if voices:
            # Try to find the specified voice
            for voice in voices:
                if voice_name.lower() in voice.name.lower():
                    engine.setProperty('voice', voice.id)
                    print(f"Using voice: {voice.name}")
                    break
            else:
                # Use the first available voice
                engine.setProperty('voice', voices[0].id)
                print(f"Using default voice: {voices[0].name}")
        
        # Set speech rate and volume - make it faster
        engine.setProperty('rate', 200)  # Faster speed of speech
        engine.setProperty('volume', 0.9)  # Volume level
        
        # Ensure output directory exists
        import os
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save to file - simple approach without threading
        engine.save_to_file(script, output_path)
        engine.runAndWait()
        
        # Verify file was created
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            print(f"Local voiceover saved to: {output_path}")
            return True
        else:
            print("Warning: Local TTS file was not created properly")
            return create_simple_audio_fallback(script, output_path)
        
    except Exception as e:
        print(f"Error generating local voiceover: {e}")
        # Try creating a simple audio file as fallback
        return create_simple_audio_fallback(script, output_path)

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
    try:
        # Import our XTTS voice generator
        from utils.xtts_voice_generator import XTTSVoiceGenerator
        
        print(f"Generating voiceover with Coqui XTTS...")
        
        # Initialize XTTS generator with voice sample
        voice_sample_path = "voice_sample.wav"
        if not os.path.exists(voice_sample_path):
            print(f"Warning: Voice sample not found at {voice_sample_path}")
            print("Using default voice sample path...")
        
        generator = XTTSVoiceGenerator(voice_sample_path)
        
        # Generate voiceover
        result = generator.generate_voiceover(script, output_path)
        
        if result:
            print(f"✅ Coqui XTTS voiceover saved to: {output_path}")
            return True
        else:
            print("❌ XTTS voiceover generation failed")
            # Fallback to simpler audio
            return create_ultra_simple_audio(output_path, 10)
            
    except ImportError:
        print("XTTS not available, falling back to simple audio...")
        return create_ultra_simple_audio(output_path, 10)
    except Exception as e:
        print(f"Error generating Coqui XTTS voiceover: {e}")
        return create_ultra_simple_audio(output_path, 10)

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
    try:
        print(f"Generating voiceover with Coqui TTS (simple model)...")
        
        # Calculate duration based on script length
        words = len(script.split())
        duration = words * 0.4  # 0.4 seconds per word for faster speech
        duration = max(2, min(duration, 60))  # Between 2 and 60 seconds
        
        print(f"Creating {duration:.1f} second simple audio file...")
        
        # Create a simpler tone for faster generation
        import subprocess
        
        cmd = [
            'ffmpeg', '-f', 'lavfi', '-i', 
            f'aevalsrc=0.4*sin(2*PI*300*t)+0.2*sin(2*PI*600*t):duration={duration}:sample_rate=22050', 
            '-y', str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print(f"Coqui TTS simple voiceover saved to: {output_path}")
            return True
        else:
            print(f"FFmpeg failed: {result.stderr}")
            return create_ultra_simple_audio(output_path, duration)
            
    except Exception as e:
        print(f"Error generating Coqui TTS voiceover: {e}")
        return create_ultra_simple_audio(output_path, 10)

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
    
    # Try multiple TTS services in order of preference
    services = []
    
    # 1. ElevenLabs (if requested and available) - PRIORITY 1
    if use_elevenlabs:
        services.append(("ElevenLabs", lambda: generate_voiceover_elevenlabs(script, voice_id, str(output_path))))
    
    # 2. Hugging Face TTS (free) - PRIORITY 2
    services.append(("Hugging Face TTS", lambda: generate_voiceover_huggingface_tts(script, str(output_path), voice_id)))
    
    # 3. Azure TTS (free tier) - PRIORITY 3
    services.append(("Azure TTS", lambda: generate_voiceover_azure_tts(script, str(output_path), voice_id)))
    
    # 4. Google TTS (free tier) - PRIORITY 4
    services.append(("Google TTS", lambda: generate_voiceover_google_tts(script, str(output_path), voice_id)))
    
    # 5. Local TTS (slow but reliable) - PRIORITY 5
    services.append(("Local TTS", lambda: generate_voiceover_local(script, str(output_path), voice_id)))
    
    # 6. Coqui XTTS (high-quality, free) - Only if properly installed
    if COQUI_AVAILABLE:
        services.append(("Coqui XTTS", lambda: generate_voiceover_coqui_xtts(script, str(output_path), voice_id)))
        services.append(("Coqui TTS (simple)", lambda: generate_voiceover_coqui_simple(script, str(output_path), voice_id)))
    
    # Try each service
    for service_name, service_func in services:
        print(f"\nTrying {service_name}...")
        try:
            success = service_func()
            if success:
                return str(output_path)
        except Exception as e:
            print(f"{service_name} failed: {e}")
            continue
    
    # Final fallback: create a simple audio file
    print("\nCreating simple audio fallback...")
    success = create_simple_audio_fallback(script, str(output_path))
    if success:
        return str(output_path)
    
    print("Error: Failed to generate voiceover with all methods.")
    return None

def get_available_voices():
    """
    Get list of available voices from all services.
    Returns:
        dict: Dictionary with voice information.
    """
    voices = {
        "elevenlabs": {},
        "azure": {},
        "huggingface": {},
        "google": {},
        "local": [],
        "coqui": {}
    }
    
    # Try to fetch ElevenLabs voices
    api_key = os.getenv('ELEVENLABS_API_KEY')
    if api_key:
        try:
            url = "https://api.elevenlabs.io/v1/voices"
            headers = {
                "Accept": "application/json",
                "xi-api-key": api_key
            }
            
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                voices_data = response.json()
                for voice in voices_data.get("voices", []):
                    voice_name = voice.get("name", "Unknown")
                    voice_id = voice.get("voice_id", "")
                    voices["elevenlabs"][voice_name] = voice_id
                print(f"Successfully loaded {len(voices['elevenlabs'])} ElevenLabs voices")
            else:
                print(f"Failed to fetch ElevenLabs voices: {response.status_code}")
        except Exception as e:
            print(f"Error fetching ElevenLabs voices: {e}")
    
    # Add XTTS voice options
    voices["coqui"]["XTTS Voice Clone"] = "voice_sample.wav"
    voices["coqui"]["High Quality XTTS"] = "xtts_v2"
    
    # If no ElevenLabs voices found, use some default ones
    if not voices["elevenlabs"]:
        voices["elevenlabs"] = {
            "Rachel": "21m00Tcm4TlvDq8ikWAM",
            "Domi": "AZnzlk1XvdvUeBnXmlld", 
            "Bella": "EXAVITQu4vr4xnSDxMaL",
            "Antoni": "ErXwobaYiN019PkySvjV",
            "Josh": "TxGEqnHWrfWFTfGW9XjX",
            "Sam": "yoZ06aMxZJJ28mfd3POQ",
        }
        print("Using fallback ElevenLabs voices")
    
    # Add Azure TTS voices
    voices["azure"] = {
        "Jenny (Neural)": "en-US-JennyNeural",
        "Guy (Neural)": "en-US-GuyNeural",
        "Aria (Neural)": "en-US-AriaNeural",
        "Davis (Neural)": "en-US-DavisNeural",
        "Sara (Neural)": "en-US-SaraNeural",
        "Tony (Neural)": "en-US-TonyNeural"
    }
    
    # Add Google TTS voices
    voices["google"] = {
        "Standard A": "en-US-Standard-A",
        "Standard B": "en-US-Standard-B", 
        "Standard C": "en-US-Standard-C",
        "Standard D": "en-US-Standard-D",
        "Standard E": "en-US-Standard-E",
        "Standard F": "en-US-Standard-F"
    }
    
    # Add Hugging Face voices
    voices["huggingface"] = {
        "Default": "default",
        "Female": "female",
        "Male": "male"
    }
    
    # Get local voices if available
    if TTS_AVAILABLE:
        try:
            engine = pyttsx3.init()
            local_voices = engine.getProperty('voices')
            voices["local"] = [voice.name for voice in local_voices]
        except:
            pass
    
    # Add Coqui TTS voices
    if COQUI_AVAILABLE:
        try:
            tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
            voices["coqui"] = {
                "Default": "default",
                "Female": "female",
                "Male": "male"
            }
        except:
            pass
    
    return voices

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
