"""Generate ASS subtitle files with CapCut-style word-by-word karaoke highlighting."""
from pathlib import Path
from typing import List

from src.models import WordTimestamp

# ASS file header — bold font, yellow highlight, black outline, bottom-center
ASS_HEADER = r"""[Script Info]
Title: Faceless Shorts Captions
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,72,&H00FFFFFF,&H0000FFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,4,2,2,40,40,200,0
Style: Highlight,Arial,80,&H0000FFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,5,2,2,40,40,200,0

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def log(msg: str) -> None:
    print(f"[captions] {msg}")


def _seconds_to_ass_time(seconds: float) -> str:
    """Convert seconds to ASS time format H:MM:SS.CC."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds % 1) * 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def _group_words(
    timestamps: List[WordTimestamp],
    group_size: int,
) -> List[List[WordTimestamp]]:
    """Group words into chunks for display."""
    groups = []
    for i in range(0, len(timestamps), group_size):
        groups.append(timestamps[i:i + group_size])
    return groups


def generate_captions(
    word_timestamps: List[WordTimestamp],
    output_path: Path,
    words_per_group: int = 3,
) -> Path:
    """Generate ASS subtitle file with karaoke-style word highlighting.

    Each group of words appears as a subtitle line. Within each line,
    \\kf tags create a fill-sweep effect as each word is spoken.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not word_timestamps:
        log("No word timestamps; writing empty captions file.")
        output_path.write_text(ASS_HEADER)
        return output_path

    events: List[str] = []
    groups = _group_words(word_timestamps, words_per_group)

    for group in groups:
        start_time = group[0].start
        # Add small padding after last word
        end_time = group[-1].end + 0.15

        # Build karaoke-tagged text with fade animation
        karaoke_parts = []
        for wt in group:
            duration_cs = max(int((wt.end - wt.start) * 100), 10)
            karaoke_parts.append(f"{{\\kf{duration_cs}}}{wt.word}")

        text = " ".join(karaoke_parts)
        # Add fade-in/fade-out
        animated_text = f"{{\\fad(150,100)}}{text}"

        start_ass = _seconds_to_ass_time(start_time)
        end_ass = _seconds_to_ass_time(end_time)

        event = f"Dialogue: 0,{start_ass},{end_ass},Default,,0,0,0,,{animated_text}"
        events.append(event)

    ass_content = ASS_HEADER + "\n".join(events) + "\n"
    output_path.write_text(ass_content, encoding="utf-8")

    log(f"Captions saved to {output_path} ({len(events)} lines)")
    return output_path
