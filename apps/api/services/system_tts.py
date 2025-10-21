"""
System Text-to-Speech Service
Uses your computer's built-in TTS - no API keys needed!
"""
import os
import io
import math

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None

class SystemTTSService:
    def __init__(self):
        if not pyttsx3:
            print("⚠️  pyttsx3 not installed. Using mock audio.")
    
    def generate_speech(self, text: str, voice_name: str = "default") -> bytes:
        """
        Generate speech using system TTS (macOS 'say' command or pyttsx3)
        
        Args:
            text: Text to convert to speech
            voice_name: Voice name (default, female, male)
            
        Returns:
            Audio bytes in WAV format
        """
        # Try macOS 'say' command first (more reliable)
        if os.name == 'posix':  # macOS/Linux
            try:
                return self._generate_with_say_command(text, voice_name)
            except Exception as e:
                print(f"macOS 'say' command failed: {e}")
        
        # Fallback to pyttsx3
        if not pyttsx3:
            return self._generate_realistic_mock_audio(text)
        
        try:
            # Initialize TTS engine
            engine = pyttsx3.init()
            
            # Set voice properties
            voices = engine.getProperty('voices')
            if voices:
                # Try to find the requested voice
                if voice_name.lower() == "female" and len(voices) > 1:
                    engine.setProperty('voice', voices[1].id)  # Usually female
                elif voice_name.lower() == "male" and len(voices) > 0:
                    engine.setProperty('voice', voices[0].id)  # Usually male
                # Default voice is already set
            
            # Set speech rate (words per minute)
            engine.setProperty('rate', 150)  # Normal speaking rate
            
            # Set volume (0.0 to 1.0)
            engine.setProperty('volume', 0.8)
            
            # Save to bytes instead of playing
            # We'll use a temporary file approach since pyttsx3 doesn't directly support bytes
            import tempfile
            import wave
            
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = temp_file.name
            
            try:
                # Save speech to temporary file
                engine.save_to_file(text, temp_path)
                engine.runAndWait()
                
                # Read the generated audio file
                with open(temp_path, 'rb') as f:
                    audio_data = f.read()
                
                return audio_data
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                    
        except Exception as e:
            print(f"System TTS error: {e}")
            return self._generate_realistic_mock_audio(text)
    
    def _generate_with_say_command(self, text: str, voice_name: str) -> bytes:
        """
        Generate speech using macOS 'say' command with proper WAV conversion
        """
        import tempfile
        import subprocess
        
        # Map voice names to macOS voice options
        voice_map = {
            "default": "",
            "female": "-v Samantha",  # Common female voice on macOS
            "male": "-v Alex"         # Common male voice on macOS
        }
        
        voice_option = voice_map.get(voice_name.lower(), "")
        
        with tempfile.NamedTemporaryFile(suffix='.aiff', delete=False) as aiff_file:
            aiff_path = aiff_file.name
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as wav_file:
            wav_path = wav_file.name
        
        try:
            # Use macOS 'say' command to generate speech (AIFF format)
            cmd = ['say']
            if voice_option:
                cmd.extend(voice_option.split())
            cmd.extend(['-o', aiff_path, text])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and os.path.exists(aiff_path):
                # Convert AIFF to WAV using afconvert (proper conversion)
                convert_cmd = ['afconvert', '-f', 'WAVE', '-d', 'LEI16@22050', aiff_path, wav_path]
                convert_result = subprocess.run(convert_cmd, capture_output=True, text=True, timeout=10)
                
                if convert_result.returncode == 0 and os.path.exists(wav_path):
                    # Read the converted WAV file
                    with open(wav_path, 'rb') as f:
                        wav_data = f.read()
                    return wav_data
                else:
                    raise Exception(f"afconvert failed: {convert_result.stderr}")
            else:
                raise Exception(f"say command failed: {result.stderr}")
                
        finally:
            # Clean up temporary files
            if os.path.exists(aiff_path):
                os.unlink(aiff_path)
            if os.path.exists(wav_path):
                os.unlink(wav_path)
    
    def _convert_aiff_to_wav(self, aiff_data: bytes) -> bytes:
        """
        Convert AIFF data to WAV format using pydub for proper conversion
        """
        try:
            from pydub import AudioSegment
            import io
            
            # Load AIFF data with pydub
            audio_segment = AudioSegment.from_file(io.BytesIO(aiff_data), format="aiff")
            
            # Convert to WAV format
            wav_buffer = io.BytesIO()
            audio_segment.export(wav_buffer, format="wav")
            wav_data = wav_buffer.getvalue()
            wav_buffer.close()
            
            return wav_data
            
        except ImportError:
            print("⚠️  pydub not available, using basic conversion")
            # Fallback to basic conversion
            return self._basic_aiff_to_wav(aiff_data)
        except Exception as e:
            print(f"⚠️  pydub conversion failed: {e}, using basic conversion")
            return self._basic_aiff_to_wav(aiff_data)
    
    def _basic_aiff_to_wav(self, aiff_data: bytes) -> bytes:
        """
        Basic AIFF to WAV conversion (fallback)
        """
        if len(aiff_data) < 54:  # Minimum AIFF header size
            raise Exception("Invalid AIFF data")
        
        # Extract audio data (skip AIFF header, keep audio data)
        audio_data = aiff_data[54:]  # Skip AIFF header
        
        # Create WAV header
        data_size = len(audio_data)
        total_size = 36 + data_size
        
        wav_header = bytearray([
            # RIFF header
            0x52, 0x49, 0x46, 0x46,  # "RIFF"
            0x00, 0x00, 0x00, 0x00,  # File size - 8 (will be updated)
            0x57, 0x41, 0x56, 0x45,  # "WAVE"
            
            # fmt chunk
            0x66, 0x6D, 0x74, 0x20,  # "fmt "
            0x10, 0x00, 0x00, 0x00,  # fmt chunk size (16)
            0x01, 0x00,              # Audio format (PCM)
            0x01, 0x00,              # Number of channels (1)
            0x44, 0xAC, 0x00, 0x00,  # Sample rate (22050)
            0x88, 0x58, 0x01, 0x00,  # Byte rate (44100)
            0x02, 0x00,              # Block align (2)
            0x10, 0x00,              # Bits per sample (16)
            
            # data chunk
            0x64, 0x61, 0x74, 0x61,  # "data"
        ])
        
        # Update file size in header
        wav_header[4:8] = total_size.to_bytes(4, byteorder='little')
        wav_header[40:44] = data_size.to_bytes(4, byteorder='little')
        
        return bytes(wav_header) + audio_data
    
    def _generate_realistic_mock_audio(self, text: str) -> bytes:
        """
        Generate a more realistic mock audio that sounds like speech patterns
        """
        sample_rate = 22050
        duration = max(2, len(text) * 0.08)  # Roughly 0.08 seconds per character
        num_samples = int(sample_rate * duration)
        
        audio_data = bytearray()
        
        # Create speech-like patterns with varying frequencies and pauses
        words = text.split()
        samples_per_word = num_samples // max(1, len(words))
        
        for word_idx, word in enumerate(words):
            start_sample = word_idx * samples_per_word
            end_sample = min((word_idx + 1) * samples_per_word, num_samples)
            
            # Vary frequency based on word length and position
            base_freq = 200 + (len(word) * 10)  # Longer words = higher pitch
            freq_variation = 50 * math.sin(word_idx * 0.5)  # Vary over time
            
            for i in range(start_sample, end_sample):
                if i < num_samples:
                    # Create speech-like rhythm with pauses
                    if i % (samples_per_word // 3) == 0:  # Pause between syllables
                        sample = 0
                    else:
                        # Vary frequency and amplitude for speech-like quality
                        freq = base_freq + freq_variation
                        amplitude = 0.2 + 0.1 * math.sin(i * 0.01)  # Varying amplitude
                        
                        # Add some harmonics for richer sound
                        sample = int(32767 * amplitude * (
                            math.sin(2 * math.pi * freq * i / sample_rate) +
                            0.3 * math.sin(2 * math.pi * freq * 2 * i / sample_rate) +
                            0.1 * math.sin(2 * math.pi * freq * 3 * i / sample_rate)
                        ))
                    
                    # Convert to 16-bit little-endian
                    audio_data.extend(sample.to_bytes(2, byteorder='little', signed=True))
        
        # Pad with silence if needed
        while len(audio_data) < num_samples * 2:
            audio_data.extend((0).to_bytes(2, byteorder='little', signed=True))
        
        data_size = len(audio_data)
        
        # WAV header (44 bytes)
        header = bytearray([
            # RIFF header
            0x52, 0x49, 0x46, 0x46,  # "RIFF"
            0x24, 0x00, 0x00, 0x00,  # File size - 8 (will be updated)
            0x57, 0x41, 0x56, 0x45,  # "WAVE"
            
            # fmt chunk
            0x66, 0x6D, 0x74, 0x20,  # "fmt "
            0x10, 0x00, 0x00, 0x00,  # fmt chunk size (16)
            0x01, 0x00,              # Audio format (PCM)
            0x01, 0x00,              # Number of channels (1)
            0x22, 0x56, 0x00, 0x00,  # Sample rate (22050)
            0x44, 0xAC, 0x00, 0x00,  # Byte rate (44100)
            0x02, 0x00,              # Block align (2)
            0x10, 0x00,              # Bits per sample (16)
            
            # data chunk
            0x64, 0x61, 0x74, 0x61,  # "data"
        ])
        
        # Calculate and update file size
        total_size = 36 + data_size
        header[4:8] = total_size.to_bytes(4, byteorder='little')
        header[40:44] = data_size.to_bytes(4, byteorder='little')
        
        return bytes(header) + bytes(audio_data)

# Available system voices (depends on your OS)
SYSTEM_VOICES = {
    "default": "default",    # System default voice
    "female": "female",      # Female voice (if available)
    "male": "male",          # Male voice (if available)
}

def get_voice_by_name(voice_name: str) -> str:
    """Get system voice by friendly name"""
    return SYSTEM_VOICES.get(voice_name.lower(), "default")

# Create global instance
system_tts = SystemTTSService()

