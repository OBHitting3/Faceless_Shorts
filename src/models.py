"""Data models for the Faceless Shorts pipeline."""
from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class Scene(BaseModel):
    """A single scene in the script breakdown."""
    scene_number: int
    duration_seconds: int = Field(ge=5, le=10)
    narration: str
    visual_prompt: str
    caption_text: str


class ScriptBreakdown(BaseModel):
    """Complete structured output from Gemini."""
    topic: str = ""
    title: str
    full_script: str
    scenes: List[Scene]
    total_duration_seconds: float = 0
    hashtags: List[str] = []


class WordTimestamp(BaseModel):
    """Word-level timing from ElevenLabs."""
    word: str
    start: float
    end: float


class VideoClip(BaseModel):
    """Metadata for a generated Runway clip."""
    scene_number: int
    file_path: str
    duration_seconds: float
    runway_task_id: str = ""


class PipelineStatus(str, Enum):
    PENDING = "pending"
    SCRIPTING = "scripting"
    VOICE = "voice"
    VIDEO_GEN = "video_gen"
    ASSEMBLY = "assembly"
    UPLOADING = "uploading"
    COMPLETE = "complete"
    FAILED = "failed"


class PipelineResult(BaseModel):
    """Tracks the state of a single video through the pipeline."""
    topic: str
    status: PipelineStatus = PipelineStatus.PENDING
    output_dir: str = ""
    script: Optional[ScriptBreakdown] = None
    audio_path: Optional[str] = None
    word_timestamps: List[WordTimestamp] = []
    clips: List[VideoClip] = []
    final_video_path: Optional[str] = None
    youtube_id: Optional[str] = None
    error: Optional[str] = None
