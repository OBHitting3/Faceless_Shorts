"""Runway ML video generation – scene prompts → AI video clips."""
import asyncio
from pathlib import Path
from typing import List

from src.models import Scene, VideoClip

# Constants
PORTRAIT_RATIO = "720:1280"  # 9:16 vertical
DEFAULT_MAX_CONCURRENT = 3
TASK_TIMEOUT = 600  # 10 minutes per clip


def log(msg: str) -> None:
    print(f"[runway] {msg}")


def _fallback_clip(scene: Scene, output_dir: Path) -> VideoClip:
    """Generate a dark background fallback clip when Runway fails."""
    import subprocess
    clip_path = output_dir / "clips" / f"scene_{scene.scene_number:02d}.mp4"

    # Use ffmpeg to create a dark background video
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"color=c=#2D2D37:s=1080x1920:d={scene.duration_seconds}:r=30",
        "-c:v", "libx264", "-preset", "ultrafast",
        "-pix_fmt", "yuv420p",
        str(clip_path),
    ]
    subprocess.run(cmd, capture_output=True, text=True, check=True)
    log(f"Fallback clip for scene {scene.scene_number}: {clip_path}")

    return VideoClip(
        scene_number=scene.scene_number,
        file_path=str(clip_path),
        duration_seconds=scene.duration_seconds,
        runway_task_id="fallback",
    )


async def _generate_single_clip(
    client,
    scene: Scene,
    output_dir: Path,
    semaphore: asyncio.Semaphore,
    model_name: str,
) -> VideoClip:
    """Generate a single video clip via Runway ML."""
    import httpx

    async with semaphore:
        clip_path = output_dir / "clips" / f"scene_{scene.scene_number:02d}.mp4"

        log(f"Scene {scene.scene_number}: generating {scene.duration_seconds}s clip "
            f"with {model_name}...")

        task = await client.image_to_video.create(
            model=model_name,
            prompt_text=scene.visual_prompt,
            ratio=PORTRAIT_RATIO,
            duration=scene.duration_seconds,
        )

        log(f"Scene {scene.scene_number}: task {task.id} created, waiting...")

        # Poll for completion
        completed = False
        import time
        start_time = time.time()
        while not completed and (time.time() - start_time) < TASK_TIMEOUT:
            task_detail = await client.tasks.retrieve(task.id)
            if task_detail.status == "SUCCEEDED":
                completed = True
                video_url = task_detail.output[0]
            elif task_detail.status == "FAILED":
                raise RuntimeError(
                    f"Runway task {task.id} failed: {getattr(task_detail, 'failure', 'unknown')}"
                )
            else:
                await asyncio.sleep(10)  # Poll every 10 seconds

        if not completed:
            raise TimeoutError(f"Runway task {task.id} timed out after {TASK_TIMEOUT}s")

        # Download the video
        async with httpx.AsyncClient(timeout=120) as http:
            response = await http.get(video_url)
            response.raise_for_status()
            with open(clip_path, "wb") as f:
                f.write(response.content)

        log(f"Scene {scene.scene_number}: saved to {clip_path}")

        return VideoClip(
            scene_number=scene.scene_number,
            file_path=str(clip_path),
            duration_seconds=scene.duration_seconds,
            runway_task_id=task.id,
        )


async def generate_clips_async(
    scenes: List[Scene],
    output_dir: Path,
    api_key: str,
    model_name: str = "gen4_turbo",
    max_concurrent: int = DEFAULT_MAX_CONCURRENT,
) -> List[VideoClip]:
    """Generate video clips for all scenes in parallel via Runway ML."""
    from runwayml import AsyncRunwayML

    client = AsyncRunwayML(api_key=api_key)
    semaphore = asyncio.Semaphore(max_concurrent)

    tasks = [
        _generate_single_clip(client, scene, output_dir, semaphore, model_name)
        for scene in scenes
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    clips: List[VideoClip] = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            log(f"Scene {scenes[i].scene_number} failed: {result}; using fallback.")
            clips.append(_fallback_clip(scenes[i], output_dir))
        else:
            clips.append(result)

    clips.sort(key=lambda c: c.scene_number)
    return clips


def generate_clips(
    scenes: List[Scene],
    output_dir: Path,
    api_key: str,
    model_name: str = "gen4_turbo",
    max_concurrent: int = DEFAULT_MAX_CONCURRENT,
) -> List[VideoClip]:
    """Synchronous wrapper for generate_clips_async."""
    return asyncio.run(
        generate_clips_async(scenes, output_dir, api_key, model_name, max_concurrent)
    )
