from pathlib import Path

from app.models import MemberMetadata
from app.transcription import FallbackTranscriptProvider, _segments_from_response


def test_diarized_response_uses_real_segment_timestamps() -> None:
    response = {
        "segments": [
            {"start": 0.2, "end": 1.4, "text": "Hello Topcoder"},
            {"start": 1.6, "end": 3.0, "text": "I build cool things"},
        ]
    }

    segments = _segments_from_response(response, "gpt-4o-transcribe-diarize", 3.0)

    assert len(segments) == 2
    assert segments[0].start == 0.2
    assert segments[0].end == 1.4
    assert segments[0].text == "Hello Topcoder"


def test_whisper_word_timestamps_are_grouped_into_caption_segments() -> None:
    response = {
        "words": [
            {"word": "Hello", "start": 0.0, "end": 0.2},
            {"word": "Topcoder", "start": 0.21, "end": 0.52},
            {"word": "community", "start": 0.54, "end": 0.92},
            {"word": "this", "start": 1.4, "end": 1.55},
            {"word": "is", "start": 1.56, "end": 1.66},
            {"word": "synced", "start": 1.67, "end": 2.0},
        ]
    }

    segments = _segments_from_response(response, "whisper-1", 2.0)

    assert len(segments) >= 2
    assert segments[0].start == 0.0
    assert segments[0].end == 0.92


def test_fallback_segments_do_not_overlap() -> None:
    metadata = MemberMetadata.from_dict(
        {
            "handle": "coder",
            "rating_color": "red",
            "tracks": ["Dev"],
            "top_skills": ["Python", "FFmpeg", "FastAPI"],
        }
    )

    segments = FallbackTranscriptProvider().transcribe(Path("unused.m4a"), metadata, 6.0)

    assert segments
    for current, following in zip(segments, segments[1:]):
        assert current.end <= following.start
