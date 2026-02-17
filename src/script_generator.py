"""Gemini-powered script generation with structured scene breakdowns."""
import json
import re

import google.generativeai as genai

from src.config import TEMPLATES_DIR
from src.models import Scene, ScriptBreakdown


def log(msg: str) -> None:
    print(f"[script] {msg}")


def _clean_json(raw: str) -> str:
    """Strip markdown fencing and whitespace from Gemini JSON output."""
    text = raw.strip()
    # Remove ```json ... ``` wrapping
    if text.startswith("```"):
        text = re.sub(r"^```\w*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    return text.strip()


def _fallback_breakdown(topic: str) -> ScriptBreakdown:
    """Minimal single-scene fallback when Gemini fails."""
    script = (
        f"Here's something you might not know. {topic}. "
        "We're keeping this short so you get the idea in under a minute. "
        "More to explore on this channel. Thanks for watching."
    )
    return ScriptBreakdown(
        topic=topic,
        title=f"{topic} | Short",
        full_script=script,
        scenes=[
            Scene(
                scene_number=1,
                duration_seconds=10,
                narration=script,
                visual_prompt=(
                    f"Cinematic slow motion shot related to {topic}. "
                    "Vertical 9:16 format, dramatic lighting, smooth camera movement, "
                    "high quality, atmospheric mood."
                ),
                caption_text=topic[:50],
            )
        ],
        total_duration_seconds=10,
        hashtags=["#shorts"],
    )


def generate_script(topic: str, api_key: str) -> ScriptBreakdown:
    """Generate structured scene breakdown from topic using Gemini 2.0 Flash."""
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")

    prompt_path = TEMPLATES_DIR / "scene_breakdown_prompt.txt"
    if prompt_path.exists():
        prompt = prompt_path.read_text().replace("{topic}", topic)
    else:
        # Inline fallback prompt
        prompt = (
            f'Write a YouTube Shorts script for: "{topic}". '
            "Return JSON with title, full_script, scenes array "
            "(each with scene_number, duration_seconds [5 or 10], narration, "
            "visual_prompt, caption_text), and hashtags."
        )

    try:
        response = model.generate_content(prompt)
        raw_text = (response.text or "").strip()
        if not raw_text:
            log("Empty Gemini response; using fallback.")
            return _fallback_breakdown(topic)

        cleaned = _clean_json(raw_text)
        data = json.loads(cleaned)

        data["topic"] = topic
        data["total_duration_seconds"] = sum(
            s["duration_seconds"] for s in data.get("scenes", [])
        )

        breakdown = ScriptBreakdown(**data)

        # Clamp scene durations to 5 or 10
        for scene in breakdown.scenes:
            if scene.duration_seconds not in (5, 10):
                scene.duration_seconds = 5

        # Recalculate total
        breakdown.total_duration_seconds = sum(
            s.duration_seconds for s in breakdown.scenes
        )

        log(f"Script generated: {len(breakdown.scenes)} scenes, "
            f"{breakdown.total_duration_seconds}s total")
        return breakdown

    except Exception as e:
        if "429" in str(e):
            log("Gemini rate limit; using fallback script.")
        else:
            log(f"Gemini error: {e}; using fallback script.")
        return _fallback_breakdown(topic)
