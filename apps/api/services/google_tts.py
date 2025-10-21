"""
Google Text-to-Speech Service
Free alternative with good quality voices
"""
import os
import math

try:
    from google.cloud import texttospeech
except ImportError:
    texttospeech = None

class GoogleTTSService:
    def __init__(self):
        # Get Google TTS credentials from environment
        self.credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        self.project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        
        if not self.credentials_path or not texttospeech:
            print("⚠️  Google TTS credentials not set or library not installed. Using mock audio.")
    
    def generate_speech(self, text: str, voice_name: str = "en-US-Standard-C") -> bytes:
        """
        Generate speech using Google Cloud Text-to-Speech
        
        Args:
            text: Text to convert to speech
            voice_name: Google voice name (default: Standard C - neutral female)
            
        Returns:
            Audio bytes in MP3 format
        """
        if not self.credentials_path or not texttospeech:
            return self._generate_mock_audio(text)
        
        try:
            # Initialize the client
            client = texttospeech.TextToSpeechClient()
            
            # Set the text input to be synthesized
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            # Build the voice request
            voice = texttospeech.VoiceSelectionParams(
                language_code="en-US",
                name=voice_name,
                ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL,
            )
            
            # Select the type of audio file you want returned
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3
            )
            
            # Perform the text-to-speech request
            response = client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            return response.audio_content
            
        except Exception as e:
            print(f"Google TTS error: {e}")
            return self._generate_mock_audio(text)
    
    def _generate_mock_audio(self, text: str) -> bytes:
        """
        Generate a simple mock audio file for testing
        This creates a minimal WAV file with a simple tone
        """
        # Create a simple WAV file with a tone
        sample_rate = 22050
        duration = max(2, len(text) * 0.1)  # Roughly 0.1 seconds per character
        num_samples = int(sample_rate * duration)
        
        # Generate a simple 440Hz tone (A note)
        frequency = 440.0
        audio_data = bytearray()
        
        for i in range(num_samples):
            # Generate sine wave
            sample = int(32767 * 0.3 * math.sin(2 * math.pi * frequency * i / sample_rate))
            # Convert to 16-bit little-endian
            audio_data.extend(sample.to_bytes(2, byteorder='little', signed=True))
        
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

# Available Google voices (all free with good quality)
GOOGLE_VOICES = {
    "standard_c": "en-US-Standard-C",      # Neutral female (default)
    "standard_d": "en-US-Standard-D",      # Neutral male
    "standard_e": "en-US-Standard-E",      # Female
    "standard_f": "en-US-Standard-F",      # Female
    "wavenet_a": "en-US-Wavenet-A",        # Neural female (premium)
    "wavenet_b": "en-US-Wavenet-B",        # Neural male (premium)
    "wavenet_c": "en-US-Wavenet-C",        # Neural female (premium)
    "wavenet_d": "en-US-Wavenet-D",        # Neural male (premium)
}

def get_voice_by_name(voice_name: str) -> str:
    """Get Google voice ID by friendly name"""
    return GOOGLE_VOICES.get(voice_name.lower(), "en-US-Standard-C")

# Create global instance
google_tts = GoogleTTSService()

