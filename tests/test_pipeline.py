import pytest
from pathlib import Path

from app.models import CaptionSegment, MemberMetadata
from app.pipeline import ProfileVideoPipeline, _validate_duration, _validate_output_file_size


class _QuotaFailProvider:
    name = "openai-gpt-4o-mini-transcribe"

    def transcribe(self, media_path: Path, metadata: MemberMetadata, duration_seconds: float) -> list[CaptionSegment]:
        raise RuntimeError("Error code: 429 - insufficient_quota")


def test_transcription_falls_back_after_openai_quota_error(tmp_path: Path) -> None:
    pipeline = ProfileVideoPipeline.__new__(ProfileVideoPipeline)
    metadata = MemberMetadata.from_dict(
        {
            "handle": "coder",
            "rating_color": "red",
            "tracks": ["Dev"],
            "top_skills": ["Python"],
            "intro_text": "Hello from Topcoder.",
        }
    )

    segments, adapter, warnings, requested = pipeline._transcribe_with_fallback(
        provider=_QuotaFailProvider(),
        voice=tmp_path / "voice.m4a",
        metadata=metadata,
        duration=5.0,
    )

    assert adapter == "fallback-scripted"
    assert requested == "openai-gpt-4o-mini-transcribe"
    assert warnings
    assert "insufficient_quota" in warnings[0]
    assert segments


def test_validate_duration_accepts_spec_window() -> None:
    _validate_duration(15.0)
    _validate_duration(30.0)


def test_validate_duration_rejects_too_short() -> None:
    with pytest.raises(ValueError, match="too short"):
        _validate_duration(14.5)


def test_validate_duration_rejects_too_long() -> None:
    with pytest.raises(ValueError, match="too long"):
        _validate_duration(30.5)


def test_validate_output_file_size_returns_size_for_allowed_file(tmp_path: Path) -> None:
    output = tmp_path / "profile_landscape.mp4"
    output.write_bytes(b"small")

    assert _validate_output_file_size(output, max_bytes=10) == 5


def test_validate_output_file_size_rejects_oversized_file(tmp_path: Path) -> None:
    output = tmp_path / "profile_vertical.mp4"
    output.write_bytes(b"toolarge")

    with pytest.raises(ValueError, match="maximum accepted output size"):
        _validate_output_file_size(output, max_bytes=4)
