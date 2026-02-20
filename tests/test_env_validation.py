#!/usr/bin/env python3
"""Test env validation (config/.env presence and required keys)."""
import os
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))


class TestEnvValidation(unittest.TestCase):
    def test_load_env_fails_when_env_file_missing(self):
        """load_env should exit when config/.env does not exist."""
        from scripts import run_pipeline

        with tempfile.TemporaryDirectory() as tmp:
            config_dir = Path(tmp) / "config"
            config_dir.mkdir()
            # No .env file
            with self.assertRaises(SystemExit):
                orig = run_pipeline.CONFIG_DIR
                run_pipeline.CONFIG_DIR = config_dir
                try:
                    run_pipeline.load_env()
                finally:
                    run_pipeline.CONFIG_DIR = orig

    def test_load_env_fails_when_keys_missing(self):
        """load_env should exit when GEMINI_API_KEY or ELEVENLABS_API_KEY missing."""
        from scripts import run_pipeline

        with tempfile.TemporaryDirectory() as tmp:
            config_dir = Path(tmp) / "config"
            config_dir.mkdir()
            (config_dir / ".env").write_text("GEMINI_API_KEY=\nELEVENLABS_API_KEY=\n")
            orig = run_pipeline.CONFIG_DIR
            run_pipeline.CONFIG_DIR = config_dir
            try:
                with self.assertRaises(SystemExit):
                    run_pipeline.load_env()
            finally:
                run_pipeline.CONFIG_DIR = orig

    def test_load_env_succeeds_with_keys(self):
        """load_env should not exit when both keys present."""
        from scripts import run_pipeline

        # Clear any env vars from previous tests
        for key in ("GEMINI_API_KEY", "ELEVENLABS_API_KEY"):
            os.environ.pop(key, None)

        with tempfile.TemporaryDirectory() as tmp:
            config_dir = Path(tmp) / "config"
            config_dir.mkdir()
            (config_dir / ".env").write_text(
                "GEMINI_API_KEY=test_key\nELEVENLABS_API_KEY=test_key\n"
            )
            orig = run_pipeline.CONFIG_DIR
            run_pipeline.CONFIG_DIR = config_dir
            try:
                run_pipeline.load_env()
                self.assertEqual(os.getenv("GEMINI_API_KEY"), "test_key")
                self.assertEqual(os.getenv("ELEVENLABS_API_KEY"), "test_key")
            finally:
                run_pipeline.CONFIG_DIR = orig


if __name__ == "__main__":
    unittest.main()
