import os
from pathlib import Path


def generate_voiceover_job(script: str, voice_sample_path: str | None, output_filename: str | None, language: str | None = "en") -> dict:
    from utils.voiceover_simple import generate_voiceover

    out_dir = Path("output/voiceovers")
    out_dir.mkdir(parents=True, exist_ok=True)
    if not output_filename:
        output_filename = "job_voiceover.wav"
    out_path = out_dir / output_filename

    # Use simplified voiceover generation
    result_path = generate_voiceover(
        script=script,
        voice_sample_path=voice_sample_path,
        output_path=str(out_path)
    )
    success = bool(result_path and os.path.exists(result_path))
    return {"success": success, "output_path": result_path}


