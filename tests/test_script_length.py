#!/usr/bin/env python3
"""Test script length constraints (under 60 seconds / ~150 words)."""
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.run_pipeline import _fallback_script

MAX_WORDS = 150


class TestScriptLength(unittest.TestCase):
    def test_fallback_script_word_count(self):
        """Fallback script should stay under 150 words."""
        script = _fallback_script("Why the sky is blue")
        words = len(script.split())
        self.assertLessEqual(words, MAX_WORDS, f"Fallback script has {words} words, max is {MAX_WORDS}")

    def test_fallback_script_not_empty(self):
        """Fallback script should not be empty."""
        script = _fallback_script("Test topic")
        self.assertGreater(len(script.strip()), 0)

    def test_fallback_script_includes_topic(self):
        """Fallback script should include the topic."""
        topic = "Why the sky is blue"
        script = _fallback_script(topic)
        self.assertTrue(
            topic in script or "sky" in script.lower() or "blue" in script.lower()
        )


if __name__ == "__main__":
    unittest.main()
