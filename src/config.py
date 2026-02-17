"""Centralized configuration loading and path constants."""
import os
import shutil
import sys
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = REPO_ROOT / "config"
OUTPUT_DIR = REPO_ROOT / "output"
TEMPLATES_DIR = REPO_ROOT / "templates"

REQUIRED_KEYS = ["GEMINI_API_KEY", "ELEVENLABS_API_KEY", "RUNWAYML_API_SECRET"]
OPTIONAL_KEYS = ["ELEVENLABS_VOICE_ID", "RUNWAY_MODEL", "RUNWAY_MAX_CONCURRENT",
                 "CAPTION_STYLE", "TRANSITION_TYPE", "TRANSITION_DURATION"]

AI_DISCLOSURE = "Script and voice generated with AI. Video clips generated with Runway ML."


def log(msg: str) -> None:
    print(f"[config] {msg}")


def load_config() -> dict:
    """Load and validate all config. Returns dict of env vars."""
    env_file = CONFIG_DIR / ".env"
    if not env_file.exists():
        log("config/.env not found. Copy .env.example and fill in your keys.")
        sys.exit(1)
    load_dotenv(env_file)

    missing = [k for k in REQUIRED_KEYS if not os.getenv(k)]
    if missing:
        log(f"Missing required env vars in config/.env: {missing}")
        sys.exit(1)

    if not shutil.which("ffmpeg"):
        log("ffmpeg not found in PATH. Install ffmpeg: https://ffmpeg.org/download.html")
        sys.exit(1)

    config = {}
    for k in REQUIRED_KEYS + OPTIONAL_KEYS:
        val = os.getenv(k)
        if val:
            config[k] = val
    return config


def get_output_dir(topic: str) -> Path:
    """Create and return a per-topic output directory."""
    safe_name = "".join(c if c.isalnum() or c in " -_" else "_" for c in topic)[:50].strip()
    topic_dir = OUTPUT_DIR / safe_name
    topic_dir.mkdir(parents=True, exist_ok=True)
    (topic_dir / "clips").mkdir(exist_ok=True)
    return topic_dir


def safe_filename(topic: str) -> str:
    """Sanitize topic for use in filenames."""
    return "".join(c if c.isalnum() or c in " -_" else "_" for c in topic)[:50].strip()
