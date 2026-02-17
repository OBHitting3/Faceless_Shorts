"""ElevenLabs TTS with word-level timestamps for animated captions."""
from pathlib import Path
from typing import List, Tuple

from src.models import WordTimestamp


def log(msg: str) -> None:
    print(f"[voice] {msg}")


def _characters_to_words(
    characters: list,
    starts: list,
    ends: list,
) -> List[WordTimestamp]:
    """Convert character-level ElevenLabs alignment to word-level timestamps."""
    words: List[WordTimestamp] = []
    current_word = ""
    word_start = None

    for char, start, end in zip(characters, starts, ends):
        if char == " " and current_word:
            words.append(WordTimestamp(word=current_word, start=word_start, end=end))
            current_word = ""
            word_start = None
        else:
            if word_start is None:
                word_start = start
            current_word += char

    # Last word
    if current_word and word_start is not None:
        words.append(WordTimestamp(
            word=current_word,
            start=word_start,
            end=ends[-1] if ends else word_start,
        ))

    return words


def _approximate_timestamps(script: str, duration: float) -> List[WordTimestamp]:
    """Fallback: evenly distribute words across audio duration."""
    words = script.split()
    if not words:
        return []
    word_duration = duration / len(words)
    return [
        WordTimestamp(
            word=w,
            start=round(i * word_duration, 3),
            end=round((i + 1) * word_duration, 3),
        )
        for i, w in enumerate(words)
    ]


def _get_audio_duration(audio_path: Path) -> float:
    """Get audio duration using ffprobe."""
    import subprocess
    cmd = [
        "ffprobe", "-v", "quiet", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return float(result.stdout.strip())
    except ValueError:
        return 30.0  # safe default


def generate_voice(
    script: str,
    output_path: Path,
    api_key: str,
    voice_id: str = "21m00Tcm4TlvDq8ikWAM",
) -> Tuple[Path, List[WordTimestamp]]:
    """Generate TTS audio with word-level timestamps.

    Returns (audio_path, word_timestamps).
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        from elevenlabs.client import ElevenLabs

        client = ElevenLabs(api_key=api_key)

        # Try convert_with_timestamps first for word-level timing
        try:
            result = client.text_to_speech.convert_with_timestamps(
                voice_id=voice_id,
                text=script,
                model_id="eleven_multilingual_v2",
                output_format="mp3_44100_128",
            )

            # Extract audio bytes
            import base64
            audio_bytes = base64.b64decode(result.audio_base64)
            with open(output_path, "wb") as f:
                f.write(audio_bytes)

            # Extract word timestamps from alignment
            word_timestamps: List[WordTimestamp] = []
            if result.alignment:
                word_timestamps = _characters_to_words(
                    result.alignment.characters,
                    result.alignment.character_start_times_seconds,
                    result.alignment.character_end_times_seconds,
                )

            log(f"Voice saved to {output_path} ({len(word_timestamps)} word timestamps)")
            return output_path, word_timestamps

        except (AttributeError, TypeError):
            # convert_with_timestamps not available in this SDK version
            # Fall back to regular convert without timestamps
            log("convert_with_timestamps not available; using convert without timestamps.")
            audio = client.text_to_speech.convert(
                voice_id=voice_id,
                text=script,
                model_id="eleven_multilingual_v2",
                output_format="mp3_44100_128",
            )
            with open(output_path, "wb") as f:
                if isinstance(audio, bytes):
                    f.write(audio)
                else:
                    for chunk in audio:
                        f.write(chunk)
            log(f"Voice saved to {output_path} (no timestamps; will approximate)")
            duration = _get_audio_duration(output_path)
            return output_path, _approximate_timestamps(script, duration)

    except Exception as e:
        if any(s in str(e) for s in ("401", "403", "missing_permissions")):
            log("ElevenLabs permission denied; using gTTS fallback.")
            from gtts import gTTS
            tts = gTTS(text=script, lang="en")
            tts.save(str(output_path))
            log(f"Voice (gTTS) saved to {output_path}")
            duration = _get_audio_duration(output_path)
            return output_path, _approximate_timestamps(script, duration)
        raise
