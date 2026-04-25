from __future__ import annotations

import os
from pathlib import Path
from typing import Protocol

from app.models import CaptionSegment, MemberMetadata


class TranscriptProvider(Protocol):
    name: str

    def transcribe(
        self, media_path: Path, metadata: MemberMetadata, duration_seconds: float
    ) -> list[CaptionSegment]:
        ...


class FallbackTranscriptProvider:
    name = "fallback-scripted"

    def transcribe(
        self, media_path: Path, metadata: MemberMetadata, duration_seconds: float
    ) -> list[CaptionSegment]:
        script = metadata.intro_text or _metadata_script(metadata)
        words = script.split()
        if not words:
            return []

        # Leave the first 2 seconds caption-free so the intro slate and
        # lower-third slide-in animation play unobstructed, then distribute
        # the remaining words evenly over the rest of the clip.
        start_offset = 2.0
        available = max(duration_seconds - start_offset - 0.5, 2.0)
        seconds_per_word = available / len(words)
        segments: list[CaptionSegment] = []
        cursor = 0
        while cursor < len(words):
            chunk = words[cursor : cursor + 6]
            start = start_offset + cursor * seconds_per_word
            chunk_end = start_offset + (cursor + len(chunk)) * seconds_per_word
            has_next = cursor + len(chunk) < len(words)
            end = min(chunk_end - 0.04 if has_next else chunk_end + 0.12, duration_seconds)
            end = max(min(end, duration_seconds), start + 0.3)
            segments.append(CaptionSegment(start=start, end=end, text=" ".join(chunk)))
            cursor += len(chunk)
        return _clamp_overlaps(segments, duration_seconds)


class OpenAITranscriptProvider:
    def __init__(self, model: str = "gpt-4o-mini-transcribe") -> None:
        self.model = model
        self.name = f"openai-{model}"

    def transcribe(
        self, media_path: Path, metadata: MemberMetadata, duration_seconds: float
    ) -> list[CaptionSegment]:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("openai package is required for OpenAI transcription") from exc

        client = OpenAI()
        with media_path.open("rb") as audio_file:
            request = {
                "model": self.model,
                "file": audio_file,
            }

            if self.model.startswith("gpt-4o-transcribe-diarize"):
                request["response_format"] = "diarized_json"
                request["chunking_strategy"] = "auto"
            elif self.model.startswith("whisper-1"):
                request["response_format"] = "verbose_json"
                request["timestamp_granularities"] = ["word"]
            else:
                request["response_format"] = "json"
                request["prompt"] = _metadata_script(metadata)

            response = client.audio.transcriptions.create(**request)

        segments = _segments_from_response(response, self.model, duration_seconds)
        if segments:
            return segments

        text = _response_text(response).strip()
        if text:
            return _segment_text(text, duration_seconds)
        return []


def choose_transcript_provider(model: str) -> TranscriptProvider:
    if os.getenv("OPENAI_API_KEY"):
        return OpenAITranscriptProvider(model=model)
    return FallbackTranscriptProvider()


def _metadata_script(metadata: MemberMetadata) -> str:
    skills = ", ".join(metadata.top_skills[:4]) or "building great solutions"
    tracks = " and ".join(track.value for track in metadata.tracks)
    return (
        f"Hi, I am {metadata.handle}, a Topcoder {tracks} member focused on {skills}. "
        "I love solving hard problems with the community."
    )


def _segment_text(text: str, duration_seconds: float) -> list[CaptionSegment]:
    words = text.split()
    if not words:
        return []
    seconds_per_word = max(duration_seconds, 1.0) / len(words)
    segments: list[CaptionSegment] = []
    for index in range(0, len(words), 7):
        chunk = words[index : index + 7]
        start = index * seconds_per_word
        chunk_end = (index + len(chunk)) * seconds_per_word
        has_next = index + len(chunk) < len(words)
        end = min(chunk_end - 0.04 if has_next else chunk_end + 0.12, duration_seconds)
        end = max(min(end, duration_seconds), start + 0.3)
        segments.append(CaptionSegment(start=start, end=end, text=" ".join(chunk)))
    return _clamp_overlaps(segments, duration_seconds)


def _segments_from_response(response: object, model: str, duration_seconds: float) -> list[CaptionSegment]:
    if model.startswith("gpt-4o-transcribe-diarize"):
        return _clamp_overlaps(_segments_from_items(_response_items(response, "segments")), duration_seconds)

    if model.startswith("whisper-1"):
        word_segments = _clamp_overlaps(_word_segments(_response_items(response, "words")), duration_seconds)
        if word_segments:
            return word_segments
        return _clamp_overlaps(_segments_from_items(_response_items(response, "segments")), duration_seconds)

    # Non-diarize GPT transcription models return text/json but no timestamps.
    text = _response_text(response).strip()
    return _segment_text(text, duration_seconds) if text else []


def _segments_from_items(items: list[object]) -> list[CaptionSegment]:
    segments: list[CaptionSegment] = []
    for item in items:
        start = _item_value(item, "start", 0.0)
        end = _item_value(item, "end", start + 1.5)
        text = str(_item_value(item, "text", "")).strip()
        if text:
            segments.append(CaptionSegment(start=float(start), end=float(end), text=text))
    return segments


def _word_segments(items: list[object]) -> list[CaptionSegment]:
    if not items:
        return []

    segments: list[CaptionSegment] = []
    chunk: list[str] = []
    chunk_start: float | None = None
    last_end: float | None = None

    for item in items:
        word = str(_item_value(item, "word", "")).strip()
        start = float(_item_value(item, "start", last_end or 0.0))
        end = float(_item_value(item, "end", start + 0.2))
        if not word:
            continue

        if chunk_start is None:
            chunk_start = start

        pause = start - (last_end if last_end is not None else start)
        if chunk and (len(chunk) >= 5 or pause > 0.35 or end - chunk_start > 2.6):
            segments.append(
                CaptionSegment(start=chunk_start, end=last_end or end, text=" ".join(chunk))
            )
            chunk = []
            chunk_start = start

        chunk.append(word)
        last_end = end

    if chunk and chunk_start is not None and last_end is not None:
        segments.append(CaptionSegment(start=chunk_start, end=last_end, text=" ".join(chunk)))

    return segments


def _clamp_overlaps(
    segments: list[CaptionSegment], duration_seconds: float, gap_seconds: float = 0.02
) -> list[CaptionSegment]:
    if not segments:
        return []

    cleaned: list[CaptionSegment] = []
    for index, segment in enumerate(segments):
        start = max(segment.start, 0.0)
        end = min(segment.end, duration_seconds)
        if index + 1 < len(segments):
            next_start = max(segments[index + 1].start, start)
            end = min(end, max(start + 0.12, next_start - gap_seconds))
        end = max(end, start + 0.12)
        cleaned.append(CaptionSegment(start=start, end=min(end, duration_seconds), text=segment.text))
    return cleaned


def _response_items(response: object, field: str) -> list[object]:
    items = getattr(response, field, None)
    if items is None and isinstance(response, dict):
        items = response.get(field)
    return list(items or [])


def _response_text(response: object) -> str:
    if isinstance(response, str):
        return response
    text = getattr(response, "text", None)
    if text is None and isinstance(response, dict):
        text = response.get("text")
    return str(text or "")


def _item_value(item: object, field: str, default: object) -> object:
    if isinstance(item, dict):
        return item.get(field, default)
    return getattr(item, field, default)
