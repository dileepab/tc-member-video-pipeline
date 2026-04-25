from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.ffmpeg import escape_drawtext, run_ffmpeg


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a short walkthrough video for the demo flow.")
    parser.add_argument(
        "--preview",
        type=Path,
        default=Path("demo-output/after/profile_landscape.mp4"),
        help="Optional preview clip to show during the final step.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("demo-output/run_app_demo.mp4"),
        help="Output demo video path.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    preview = args.preview if args.preview.exists() else None

    commands = {
        "title": escape_drawtext("TOPCODER PROFILE VIDEO PIPELINE"),
        "step1": escape_drawtext("1. SET UP ENVIRONMENT"),
        "setup": escape_drawtext("python3 -m venv .venv && source .venv/bin/activate && pip install -e \".[dev]\""),
        "step2": escape_drawtext("2. GENERATE A SAMPLE MEMBER CLIP"),
        "sample": escape_drawtext("python scripts/generate_sample.py"),
        "step3": escape_drawtext("3. RENDER THE BRANDED BEFORE/AFTER OUTPUTS"),
        "render": escape_drawtext("python scripts/run_demo.py"),
        "step4": escape_drawtext("4. START THE API AND SUBMIT A JOB"),
        "api": escape_drawtext("uvicorn app.main:app --reload"),
        "curl": escape_drawtext("curl -X POST http://127.0.0.1:8000/jobs -H \"Content-Type: application/json\" -d @samples/job_local.json"),
        "outputs": escape_drawtext(
            "Outputs: profile_landscape.mp4, profile_vertical.mp4, captions, manifest"
        ),
    }

    background_chain = (
        "[0:v]"
        "drawbox=x=0:y=0:w=iw:h=ih:color=#05070B@1:t=fill,"
        "drawbox=x=0:y=0:w=iw:h=22:color=#EF3A3A@0.92:t=fill,"
        "drawbox=x=0:y=22:w=iw*0.36:h=8:color=#29A7DF@0.95:t=fill,"
        f"drawtext=font='DejaVu Sans':text='{commands['title']}':x=80:y=72:fontsize=42:fontcolor=white,"
        f"drawtext=font='DejaVu Sans':text='{commands['step1']}':x=80:y=178:fontsize=34:fontcolor=#29A7DF:enable='between(t,0,4)',"
        f"drawtext=font='DejaVu Sans':text='{commands['setup']}':x=80:y=236:fontsize=25:fontcolor=white:enable='between(t,0,4)',"
        f"drawtext=font='DejaVu Sans':text='{commands['step2']}':x=80:y=178:fontsize=34:fontcolor=#F7B500:enable='between(t,4,8)',"
        f"drawtext=font='DejaVu Sans':text='{commands['sample']}':x=80:y=236:fontsize=28:fontcolor=white:enable='between(t,4,8)',"
        f"drawtext=font='DejaVu Sans':text='{commands['step3']}':x=80:y=178:fontsize=34:fontcolor=#0AB88A:enable='between(t,8,12)',"
        f"drawtext=font='DejaVu Sans':text='{commands['render']}':x=80:y=236:fontsize=28:fontcolor=white:enable='between(t,8,12)',"
        f"drawtext=font='DejaVu Sans':text='{commands['step4']}':x=80:y=178:fontsize=34:fontcolor=#EF3A3A:enable='between(t,12,18)',"
        f"drawtext=font='DejaVu Sans':text='{commands['api']}':x=80:y=236:fontsize=26:fontcolor=white:enable='between(t,12,18)',"
        f"drawtext=font='DejaVu Sans':text='{commands['curl']}':x=80:y=286:fontsize=21:fontcolor=white:enable='between(t,12,18)',"
        f"drawtext=font='DejaVu Sans':text='{commands['outputs']}':x=80:y=612:fontsize=26:fontcolor=#D9E7F5:enable='between(t,12,18)'"
        "[bg]"
    )

    if preview:
        run_ffmpeg(
            [
                "-f",
                "lavfi",
                "-t",
                "18",
                "-i",
                "color=c=#05070B:s=1280x720:r=30",
                "-stream_loop",
                "-1",
                "-t",
                "18",
                "-i",
                str(preview),
                "-filter_complex",
                background_chain
                + ";[1:v]scale=500:-1[preview];"
                + "[bg][preview]overlay=x=730:y=146:enable='between(t,12,18)',format=yuv420p[vout]",
                "-map",
                "[vout]",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-preset",
                "veryfast",
                "-crf",
                "21",
                "-shortest",
                str(args.output),
            ]
        )
    else:
        run_ffmpeg(
            [
                "-f",
                "lavfi",
                "-t",
                "18",
                "-i",
                "color=c=#05070B:s=1280x720:r=30",
                "-vf",
                background_chain.replace("[0:v]", "").replace("[bg]", ""),
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-preset",
                "veryfast",
                "-crf",
                "21",
                str(args.output),
            ]
        )


if __name__ == "__main__":
    main()
