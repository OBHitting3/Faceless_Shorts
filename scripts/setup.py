#!/usr/bin/env python3
"""
Faceless Shorts Automator V2 – Setup validator.
Checks: folder structure, .env presence, API keys, ffmpeg, YouTube OAuth.
Run from repo root: python scripts/setup.py
"""
import os
import shutil
import sys
from pathlib import Path


def log(msg: str) -> None:
    print(f"[setup] {msg}")


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    os.chdir(repo_root)

    log("Checking folder structure...")
    required_dirs = ["config", "docs", "scripts", "workflows", "tests", "src", "templates"]
    missing = [d for d in required_dirs if not (repo_root / d).is_dir()]
    if missing:
        log(f"Missing directories: {missing}")
        return 1
    log("Folders OK")

    log("Checking config...")
    config_env = repo_root / "config" / ".env"
    if not config_env.exists():
        log("config/.env not found. Copy .env.example and add your API keys.")
        return 1
    log("config/.env present")

    try:
        from dotenv import load_dotenv
        load_dotenv(config_env)

        required_keys = {
            "GEMINI_API_KEY": "Google AI Studio",
            "ELEVENLABS_API_KEY": "ElevenLabs dashboard",
            "RUNWAYML_API_SECRET": "Runway Developer Portal",
        }
        for key, source in required_keys.items():
            val = os.getenv(key)
            if not val:
                log(f"{key} missing in config/.env (get from {source})")
                return 1
        log("API keys loaded from .env")
    except ImportError:
        log("Run: pip install -r requirements.txt")
        return 1

    log("Checking ffmpeg...")
    if shutil.which("ffmpeg"):
        log("ffmpeg found")
    else:
        log("WARNING: ffmpeg not found in PATH. Install: https://ffmpeg.org/download.html")

    if shutil.which("ffprobe"):
        log("ffprobe found")
    else:
        log("WARNING: ffprobe not found in PATH (needed for audio duration detection)")

    log("Checking YouTube OAuth...")
    yt_oauth = repo_root / "config" / "youtube-oauth.json"
    if not yt_oauth.exists():
        log("config/youtube-oauth.json not found (run: python scripts/auth_youtube.py)")
    else:
        log("youtube-oauth.json present")

    log("")
    log("Setup validation complete.")
    log("Run a Short: python -m src.pipeline \"Your topic here\" --no-upload")
    log("Batch run:   python -m src.batch \"Topic 1\" \"Topic 2\" --no-upload")
    return 0


if __name__ == "__main__":
    sys.exit(main())
