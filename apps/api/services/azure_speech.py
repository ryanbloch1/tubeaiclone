"""
Azure Speech Services for Text-to-Speech
Free alternative to ElevenLabs with excellent quality
"""
import os

try:
    import azure.cognitiveservices.speech as speechsdk
except ImportError:
    speechsdk = None

class AzureSpeechService:
    def __init__(self):
        # Get Azure Speech credentials from environment
        self.speech_key = os.getenv('AZURE_SPEECH_KEY')
        self.speech_region = os.getenv('AZURE_SPEECH_REGION', 'eastus')
        
        if not self.speech_key:
            print("⚠️  Azure Speech key not set. Using mock audio.")
    
    def generate_speech(self, text: str, voice_name: str = "en-US-AriaNeural") -> bytes:
        """
        Generate speech using Azure Speech Services
        
        Args:
            text: Text to convert to speech
            voice_name: Azure voice name (default: Aria - natural female voice)
            
        Returns:
            Audio bytes in WAV format
        """
        if not self.speech_key or not speechsdk:
            return self._generate_mock_audio(text)
        
        try:
            # Configure speech service
            speech_config = speechsdk.SpeechConfig(
                subscription=self.speech_key, 
                region=self.speech_region
            )
            
            # Set voice
            speech_config.speech_synthesis_voice_name = voice_name
            
            # Configure audio output
            audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=False)
            
            # Create synthesizer
            synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=speech_config, 
                audio_config=audio_config
            )
            
            # Synthesize speech
            result = synthesizer.speak_text_async(text).get()
            
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                return bytes(result.audio_data)
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = result.cancellation_details
                error_msg = f"Speech synthesis canceled: {cancellation_details.reason}"
                if cancellation_details.error_details:
                    error_msg += f". {cancellation_details.error_details}"
                raise RuntimeError(error_msg)
            else:
                raise RuntimeError(f"Speech synthesis failed with reason: {result.reason}")
                
        except Exception as e:
            print(f"Azure Speech error: {e}")
            return self._generate_mock_audio(text)
    
    def _generate_mock_audio(self, text: str) -> bytes:
        """
        Generate a simple mock audio file for testing
        This creates a minimal WAV file with a simple tone
        """
        import math
        
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

# Available Azure voices (all high quality neural voices)
AZURE_VOICES = {
    "aria": "en-US-AriaNeural",      # Natural female voice
    "guy": "en-US-GuyNeural",        # Natural male voice
    "jenny": "en-US-JennyNeural",    # Conversational female
    "ryan": "en-US-RyanNeural",      # Conversational male
    "michelle": "en-US-MichelleNeural", # Friendly female
    "brandon": "en-US-BrandonNeural",   # Professional male
}

def get_voice_by_name(voice_name: str) -> str:
    """Get Azure voice ID by friendly name"""
    return AZURE_VOICES.get(voice_name.lower(), "en-US-AriaNeural")

# Create global instance
azure_speech = AzureSpeechService()
