from pathlib import Path

from app.captions import write_srt
from app.models import CaptionSegment


def test_write_srt_formats_timestamps(tmp_path: Path) -> None:
    output = write_srt(
        [CaptionSegment(start=1.2, end=3.45, text="Hello Topcoder")],
        tmp_path / "captions.srt",
    )

    assert "00:00:01,200 --> 00:00:03,450" in output.read_text()
