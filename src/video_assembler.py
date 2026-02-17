"""ffmpeg-based video assembly — stitch clips + audio + captions + transitions."""
import subprocess
from pathlib import Path
from typing import List

from src.models import VideoClip

FINAL_WIDTH = 1080
FINAL_HEIGHT = 1920
FPS = 30
DEFAULT_TRANSITION = "fade"
DEFAULT_TRANSITION_DURATION = 0.5


def log(msg: str) -> None:
    print(f"[assembler] {msg}")


def _run_ffmpeg(cmd: List[str]) -> None:
    """Run an ffmpeg command and raise on failure."""
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed (exit {result.returncode}):\n{result.stderr[-2000:]}")


def assemble_video(
    clips: List[VideoClip],
    audio_path: Path,
    captions_path: Path,
    output_path: Path,
    transition_type: str = DEFAULT_TRANSITION,
    transition_duration: float = DEFAULT_TRANSITION_DURATION,
) -> Path:
    """Assemble final video from Runway clips, audio, and captions using ffmpeg.

    Steps:
    1. Normalize all clips to same resolution/fps
    2. Stitch with xfade crossfade transitions
    3. Mix audio track
    4. Burn in ASS captions
    5. Output final MP4
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not clips:
        raise ValueError("No clips to assemble")

    if len(clips) == 1:
        return _single_clip_assembly(
            clips[0], audio_path, captions_path, output_path
        )

    return _multi_clip_assembly(
        clips, audio_path, captions_path, output_path,
        transition_type, transition_duration,
    )


def _single_clip_assembly(
    clip: VideoClip,
    audio_path: Path,
    captions_path: Path,
    output_path: Path,
) -> Path:
    """Assembly for a single clip (no transitions needed)."""
    log("Single clip assembly...")

    # Escape the captions path for ffmpeg filter (replace : and \ )
    captions_escaped = str(captions_path).replace("\\", "/").replace(":", "\\:")

    cmd = [
        "ffmpeg", "-y",
        "-i", clip.file_path,
        "-i", str(audio_path),
        "-filter_complex",
        (
            f"[0:v]scale={FINAL_WIDTH}:{FINAL_HEIGHT}:"
            f"force_original_aspect_ratio=decrease,"
            f"pad={FINAL_WIDTH}:{FINAL_HEIGHT}:(ow-iw)/2:(oh-ih)/2,"
            f"fps={FPS},"
            f"ass='{captions_escaped}'[vout]"
        ),
        "-map", "[vout]",
        "-map", "1:a",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        "-movflags", "+faststart",
        str(output_path),
    ]
    _run_ffmpeg(cmd)
    log(f"Final video saved to {output_path}")
    return output_path


def _multi_clip_assembly(
    clips: List[VideoClip],
    audio_path: Path,
    captions_path: Path,
    output_path: Path,
    transition_type: str,
    transition_duration: float,
) -> Path:
    """Assembly for multiple clips with crossfade transitions."""
    log(f"Multi-clip assembly: {len(clips)} clips, {transition_type} transitions...")

    # First: concat clips into an intermediate file (without audio/captions)
    # Using the concat demuxer approach for reliability
    concat_path = output_path.parent / "assembled_noCaptions.mp4"

    # Normalize each clip to consistent format first
    normalized_clips = []
    for i, clip in enumerate(clips):
        norm_path = output_path.parent / "clips" / f"norm_{i:02d}.mp4"
        cmd = [
            "ffmpeg", "-y",
            "-i", clip.file_path,
            "-vf", f"scale={FINAL_WIDTH}:{FINAL_HEIGHT}:force_original_aspect_ratio=decrease,"
                   f"pad={FINAL_WIDTH}:{FINAL_HEIGHT}:(ow-iw)/2:(oh-ih)/2,"
                   f"fps={FPS}",
            "-c:v", "libx264", "-preset", "fast", "-crf", "18",
            "-pix_fmt", "yuv420p",
            "-an",  # Remove any audio from clips
            str(norm_path),
        ]
        _run_ffmpeg(cmd)
        normalized_clips.append(str(norm_path))

    # Build xfade filter chain
    if len(normalized_clips) == 2:
        # Simple case: 2 clips
        offset = clips[0].duration_seconds - transition_duration
        cmd = [
            "ffmpeg", "-y",
            "-i", normalized_clips[0],
            "-i", normalized_clips[1],
            "-filter_complex",
            f"[0:v][1:v]xfade=transition={transition_type}:"
            f"duration={transition_duration}:offset={offset}[vout]",
            "-map", "[vout]",
            "-c:v", "libx264", "-preset", "medium", "-crf", "18",
            "-pix_fmt", "yuv420p",
            str(concat_path),
        ]
        _run_ffmpeg(cmd)
    else:
        # 3+ clips: chain xfade filters
        filter_parts = []
        inputs = []
        for i, norm in enumerate(normalized_clips):
            inputs.extend(["-i", norm])

        # First xfade: [0:v][1:v] -> [xf0]
        cumulative_offset = clips[0].duration_seconds - transition_duration
        filter_parts.append(
            f"[0:v][1:v]xfade=transition={transition_type}:"
            f"duration={transition_duration}:offset={cumulative_offset}[xf0]"
        )

        for i in range(2, len(clips)):
            prev_label = f"xf{i - 2}"
            cumulative_offset += clips[i - 1].duration_seconds - transition_duration

            if i == len(clips) - 1:
                out_label = "vout"
            else:
                out_label = f"xf{i - 1}"

            filter_parts.append(
                f"[{prev_label}][{i}:v]xfade=transition={transition_type}:"
                f"duration={transition_duration}:offset={cumulative_offset}[{out_label}]"
            )

        filter_complex = ";".join(filter_parts)

        cmd = ["ffmpeg", "-y"]
        cmd.extend(inputs)
        cmd.extend([
            "-filter_complex", filter_complex,
            "-map", "[vout]",
            "-c:v", "libx264", "-preset", "medium", "-crf", "18",
            "-pix_fmt", "yuv420p",
            str(concat_path),
        ])
        _run_ffmpeg(cmd)

    # Now add audio and burn in captions
    captions_escaped = str(captions_path).replace("\\", "/").replace(":", "\\:")

    cmd = [
        "ffmpeg", "-y",
        "-i", str(concat_path),
        "-i", str(audio_path),
        "-vf", f"ass='{captions_escaped}'",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        "-movflags", "+faststart",
        str(output_path),
    ]
    _run_ffmpeg(cmd)

    log(f"Final video saved to {output_path}")
    return output_path
