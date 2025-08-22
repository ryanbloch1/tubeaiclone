import os
from pathlib import Path


def generate_voiceover_job(script: str, voice_sample_path: str | None, output_filename: str | None, language: str | None = "en") -> dict:
    from utils.voiceover import generate_voiceover

    out_dir = Path("output/voiceovers")
    out_dir.mkdir(parents=True, exist_ok=True)
    if not output_filename:
        output_filename = "job_voiceover.wav"
    out_path = out_dir / output_filename

    # Allow custom sample via env or param
    if voice_sample_path and os.path.exists(voice_sample_path):
        os.environ["VOICE_SAMPLE_PATH"] = voice_sample_path

    result_path = generate_voiceover(
        script=script,
        voice_id=os.environ.get("VOICE_SAMPLE_PATH", "voice_sample.wav"),
        output_path=str(out_path),
        use_elevenlabs=False,
    )
    success = bool(result_path and os.path.exists(result_path))
    return {"success": success, "output_path": result_path}


