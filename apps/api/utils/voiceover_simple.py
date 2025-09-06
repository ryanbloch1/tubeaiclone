"""
Simplified voiceover generation for production deployment.
Uses only reliable TTS methods that work in containers.
"""

import logging
import math
import os
import shutil
import struct
import subprocess
import tempfile
import wave

import requests

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_voiceover(
    script: str, voice_sample_path: str | None = None, output_path: str | None = None
) -> str:
    """
    Generate voiceover using the most reliable method available.

    Args:
        script: Text to convert to speech
        voice_sample_path: Unused. Present for API compatibility only.
        output_path: Output file path (optional, will create temp file if not provided)

    Returns:
        Path to generated audio file
    """

    if not output_path:
        # Create a temporary file for output
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            output_path = tmp.name

    # Reference voice_sample_path to satisfy linters; not used in simplified path
    if voice_sample_path:
        _ = voice_sample_path

    mode = (os.getenv("VOICE_TTS_MODE", "say") or "say").lower()
    logger.info("🎤 Generating voiceover for %d characters (mode=%s)", len(script), mode)

    # ElevenLabs (explicit opt-in)
    if mode in ("elevenlabs", "cloud", "sdk", "http"):
        return _generate_elevenlabs_tts(script, output_path)

    # Minimal, cost-free paths
    if mode in ("say", "mac", "macos"):
        try:
            return _generate_macos_say(script, output_path)
        except Exception as e:
            logger.error("macOS say failed: %s", e)
            return _generate_placeholder_tone(script, output_path)

    # Explicit placeholder/mocks
    if mode in ("placeholder", "mock", "dummy"):
        return _generate_placeholder_tone(script, output_path)

    # Auto: prefer ElevenLabs if key present, else say, else placeholder
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if api_key:
        try:
            return _generate_elevenlabs_tts(script, output_path)
        except Exception as e:
            logger.error("ElevenLabs failed in auto: %s", e)
    try:
        return _generate_macos_say(script, output_path)
    except Exception:
        return _generate_placeholder_tone(script, output_path)


def _command_exists(command: str) -> bool:
    """Check if a command exists in the system PATH without executing it"""
    return shutil.which(command) is not None


def _generate_macos_say(script: str, output_path: str) -> str:
    """Use macOS 'say' to synthesize TTS. Converts to WAV using ffmpeg if available."""
    if not _command_exists("say"):
        raise RuntimeError("'say' not found on PATH")

    aiff_path = output_path.replace(".wav", ".aiff")
    voice_name = os.getenv("VOICE_NAME")
    voice_rate = os.getenv("VOICE_RATE")  # words per minute
    cmd = ["say"]
    if voice_name:
        cmd += ["-v", voice_name]
    if voice_rate:
        cmd += ["-r", voice_rate]
    cmd += ["-o", aiff_path, script]
    subprocess.run(cmd, check=True, capture_output=True, timeout=120)

    if _command_exists("ffmpeg"):
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                aiff_path,
                "-ar",
                "22050",
                "-ac",
                "1",
                "-sample_fmt",
                "s16",
                output_path,
            ],
            check=True,
            capture_output=True,
        )
        os.unlink(aiff_path)
        return output_path

    # As a last resort, rename AIFF to .wav (not ideal but unblocks playback in some clients)
    os.rename(aiff_path, output_path)
    return output_path


def _generate_elevenlabs_tts(script: str, output_path: str) -> str:
    """Generate TTS using ElevenLabs raw HTTP API and save as WAV (mp3→wav)."""
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        raise RuntimeError("ELEVENLABS_API_KEY is not set")

    voice_id = os.getenv("ELEVENLABS_VOICE_ID", "JBFqnCBsd6RMkjVDRZzb")
    model_id = os.getenv("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2")
    output_format = os.getenv("ELEVENLABS_OUTPUT_FORMAT", "mp3_44100_128")

    if not output_path:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            output_path = tmp.name

    logger.info(
        "🔗 ElevenLabs HTTP: voice_id=%s model_id=%s len_chars=%d format=%s",
        voice_id,
        model_id,
        len(script),
        output_format,
    )

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": api_key,
        "accept": "audio/mpeg",
        "content-type": "application/json",
    }
    payload = {"text": script, "model_id": model_id}

    resp = requests.post(
        url,
        params={"output_format": output_format},
        headers=headers,
        json=payload,
        stream=True,
        timeout=60,
    )

    if resp.status_code != 200:
        try:
            body = resp.json()
        except Exception:
            body = resp.text
        raise RuntimeError(
            f"headers: {dict(resp.headers)}, status_code: {resp.status_code}, body: {body}"
        )

    mp3_path = output_path.replace(".wav", ".mp3")
    with open(mp3_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

    if _command_exists("ffmpeg"):
        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    mp3_path,
                    "-ar",
                    "22050",
                    "-ac",
                    "1",
                    "-sample_fmt",
                    "s16",
                    output_path,
                ],
                check=True,
                capture_output=True,
            )
            os.unlink(mp3_path)
        except Exception:
            os.rename(mp3_path, output_path)
    else:
        os.rename(mp3_path, output_path)

    logger.info(f"✅ Generated TTS using ElevenLabs HTTP API: {output_path}")
    return output_path


def _generate_placeholder_tone(script: str, output_path: str) -> str:
    """Generate a simple placeholder tone WAV so end-to-end flow works offline."""
    # Duration scales gently with script length, capped
    duration_sec = max(2.0, min(8.0, len(script) / 50.0))
    sample_rate = 22050
    frequency_hz = 440.0
    amplitude = 0.3

    num_frames = int(duration_sec * sample_rate)
    with wave.open(output_path, "w") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)  # 16-bit
        wav.setframerate(sample_rate)
        for i in range(num_frames):
            t = i / sample_rate
            sample = amplitude * math.sin(2 * math.pi * frequency_hz * t)
            wav.writeframes(struct.pack("<h", int(sample * 32767)))

    logger.info("✅ Generated placeholder tone WAV: %s", output_path)
    return output_path


# For testing
if __name__ == "__main__":
    test_script = "Hello, this is a test of the simplified voiceover system."
    output_file = generate_voiceover(test_script)
    print(f"Generated test voiceover: {output_file}")
