from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.ffmpeg import run_ffmpeg


def generate_sample_raw_video(output_path: Path, *, duration: float = 18.0) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    run_ffmpeg(
        [
            "-f",
            "lavfi",
            "-t",
            str(duration),
            "-i",
            "testsrc2=size=1280x720:rate=30",
            "-f",
            "lavfi",
            "-t",
            str(duration),
            "-i",
            "sine=frequency=190:sample_rate=48000",
            "-filter_complex",
            "[0:v]eq=brightness=-0.08:saturation=0.72,drawbox=x=430:y=90:w=420:h=520:color=black@0.25:t=fill,"
            "drawtext=font='DejaVu Sans':text='RAW MEMBER CLIP':x=(w-tw)/2:y=52:fontsize=42:fontcolor=white,"
            "drawtext=font='DejaVu Sans':text='15-30 sec phone intro placeholder':x=(w-tw)/2:y=h-80:fontsize=30:fontcolor=white[v];"
            "[1:a]volume=0.18,highpass=f=80[a]",
            "-map",
            "[v]",
            "-map",
            "[a]",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-preset",
            "veryfast",
            "-c:a",
            "aac",
            "-shortest",
            str(output_path),
        ]
    )
    return output_path


if __name__ == "__main__":
    print(generate_sample_raw_video(Path("demo-output/before_raw_intro.mp4")))
