#!/usr/bin/env python3
"""
Local XTTS v2 CLI wrapper.

Run this with a Python 3.11 environment that has:
  pip install TTS==0.22.0 torch torchvision torchaudio

Usage:
  python local_xtts_cli.py --text "hello" --speaker voice_sample.wav --out output.wav --lang en

This script is intentionally minimal and has no external deps.
"""
import argparse
import os
import sys
import time

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", required=True)
    parser.add_argument("--speaker", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--lang", default="en")
    args = parser.parse_args()

    try:
        # Allowlist XTTS config class for PyTorch >=2.6 safe unpickling
        try:
            from torch.serialization import add_safe_globals  # type: ignore
            from TTS.tts.configs.xtts_config import XttsConfig  # type: ignore
            from TTS.tts.models.xtts import XttsAudioConfig  # type: ignore
            add_safe_globals([XttsConfig, XttsAudioConfig])
        except Exception:
            pass

        from TTS.api import TTS
    except Exception as e:
        print(f"ERR: TTS import failed: {e}")
        return 2

    try:
        print("[XTTS] Loading xtts_v2…", flush=True)
        tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
        # Select best device
        # Force CPU to avoid MPS channel limitation on macOS
        try:
            import torch  # type: ignore
            if hasattr(tts, "to"):
                tts = tts.to("cpu")
            print("[XTTS] Using CPU")
        except Exception:
            print("[XTTS] Using CPU (torch not available)")

        os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
        start = time.time()
        tts.tts_to_file(
            text=args.text,
            file_path=args.out,
            speaker_wav=args.speaker,
            language=args.lang,
        )
        dur = time.time() - start
        print(f"[XTTS] Done in {dur:.2f}s -> {args.out}")
        return 0
    except Exception as e:
        print(f"ERR: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())


