"""Main pipeline orchestrator: topic → final YouTube Short."""
import argparse
import json
import sys
from pathlib import Path

from src.config import load_config, get_output_dir, AI_DISCLOSURE
from src.models import PipelineResult, PipelineStatus
from src.script_generator import generate_script
from src.voice_generator import generate_voice
from src.video_generator import generate_clips
from src.caption_generator import generate_captions
from src.video_assembler import assemble_video
from src.uploader import upload_to_youtube


def log(msg: str) -> None:
    print(f"[pipeline] {msg}")


def run_pipeline(
    topic: str,
    no_upload: bool = False,
    runway_model: str = "gen4_turbo",
    max_concurrent: int = 3,
    transition_type: str = "fade",
    transition_duration: float = 0.5,
) -> PipelineResult:
    """Execute the full pipeline for a single topic."""
    result = PipelineResult(topic=topic)

    try:
        config = load_config()
        output_dir = get_output_dir(topic)
        result.output_dir = str(output_dir)

        # Override defaults from config
        runway_model = config.get("RUNWAY_MODEL", runway_model)
        max_concurrent = int(config.get("RUNWAY_MAX_CONCURRENT", max_concurrent))
        transition_type = config.get("TRANSITION_TYPE", transition_type)
        transition_duration = float(config.get("TRANSITION_DURATION", transition_duration))

        # Step 1: Script Generation
        result.status = PipelineStatus.SCRIPTING
        log(f"Step 1/6: Generating script for '{topic}'")
        breakdown = generate_script(topic, config["GEMINI_API_KEY"])
        result.script = breakdown
        with open(output_dir / "script.json", "w") as f:
            f.write(breakdown.model_dump_json(indent=2))
        log(f"  → {len(breakdown.scenes)} scenes, {breakdown.total_duration_seconds}s")

        # Step 2: Voice Generation
        result.status = PipelineStatus.VOICE
        log(f"Step 2/6: Generating voice ({len(breakdown.full_script.split())} words)")
        audio_path = output_dir / "voice.mp3"
        voice_id = config.get("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
        audio_path, word_timestamps = generate_voice(
            breakdown.full_script, audio_path,
            config["ELEVENLABS_API_KEY"], voice_id,
        )
        result.audio_path = str(audio_path)
        result.word_timestamps = word_timestamps
        with open(output_dir / "voice_timestamps.json", "w") as f:
            json.dump([wt.model_dump() for wt in word_timestamps], f, indent=2)
        log(f"  → {len(word_timestamps)} word timestamps")

        # Step 3: Video Clip Generation (Runway ML)
        result.status = PipelineStatus.VIDEO_GEN
        log(f"Step 3/6: Generating {len(breakdown.scenes)} video clips via Runway ML")
        clips = generate_clips(
            breakdown.scenes, output_dir,
            config["RUNWAYML_API_SECRET"],
            model_name=runway_model,
            max_concurrent=max_concurrent,
        )
        result.clips = clips
        log(f"  → {len(clips)} clips generated")

        # Step 4: Caption Generation
        log("Step 4/6: Generating animated captions")
        captions_path = output_dir / "captions.ass"
        generate_captions(word_timestamps, captions_path)

        # Step 5: Video Assembly
        result.status = PipelineStatus.ASSEMBLY
        log("Step 5/6: Assembling final video with ffmpeg")
        final_path = output_dir / "final.mp4"
        assemble_video(
            clips, audio_path, captions_path, final_path,
            transition_type=transition_type,
            transition_duration=transition_duration,
        )
        result.final_video_path = str(final_path)

        # Step 6: Upload
        if not no_upload:
            result.status = PipelineStatus.UPLOADING
            log("Step 6/6: Uploading to YouTube")
            desc = (
                f"{topic}\n\n{AI_DISCLOSURE}\n\n"
                f"{' '.join(breakdown.hashtags)}"
            )
            video_id = upload_to_youtube(final_path, breakdown.title, desc)
            result.youtube_id = video_id
        else:
            log("Step 6/6: Skipped upload (--no-upload)")

        result.status = PipelineStatus.COMPLETE
        log(f"Done! Final video: {result.final_video_path}")

    except Exception as e:
        result.status = PipelineStatus.FAILED
        result.error = str(e)
        log(f"Pipeline failed: {e}")

    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Faceless Shorts V2: topic → AI-generated Short on YouTube"
    )
    parser.add_argument("topic", help="Topic for the Short")
    parser.add_argument("--no-upload", action="store_true",
                        help="Build video only; skip YouTube upload")
    parser.add_argument("--runway-model", default="gen4_turbo",
                        choices=["gen4_turbo", "gen4.5"],
                        help="Runway ML model (default: gen4_turbo)")
    parser.add_argument("--transition", default="fade",
                        help="Transition type between clips (default: fade)")
    args = parser.parse_args()

    result = run_pipeline(
        topic=args.topic.strip(),
        no_upload=args.no_upload,
        runway_model=args.runway_model,
        transition_type=args.transition,
    )

    if result.status == PipelineStatus.FAILED:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
