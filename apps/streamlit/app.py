from pathlib import Path
import sys

# Ensure repo root in sys.path for local dev
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
import app as streamlit_app  # reuse existing app for now


