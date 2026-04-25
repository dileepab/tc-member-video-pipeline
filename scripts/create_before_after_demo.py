from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.ffmpeg import escape_drawtext, run_ffmpeg


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create the Topcoder Star before/after transformation demo video."
    )
    parser.add_argument(
        "--before",
        type=Path,
        default=Path("demo-output/Profile_Intro_Video_Generated.mp4"),
        help="Raw input clip to show on the left.",
    )
    parser.add_argument(
        "--after",
        type=Path,
        default=Path("demo-output/after/profile_landscape.mp4"),
        help="Rendered Topcoder Star clip to show on the right.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("demo-output/topcoder_star_before_after.mp4"),
        help="Output before/after showcase video path.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.before.exists():
        raise FileNotFoundError(f"before clip not found: {args.before}")
    if not args.after.exists():
        raise FileNotFoundError(f"after clip not found: {args.after}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    title = escape_drawtext("TOPCODER STAR TRANSFORMATION")
    before = escape_drawtext("BEFORE: RAW MEMBER CLIP")
    after = escape_drawtext("AFTER: BRANDED PROFILE INTRO")

    filter_complex = (
        "[0:v]scale=604:340:force_original_aspect_ratio=decrease,"
        "pad=604:340:(ow-iw)/2:(oh-ih)/2:color=#111111[before];"
        "[1:v]scale=604:340:force_original_aspect_ratio=decrease,"
        "pad=604:340:(ow-iw)/2:(oh-ih)/2:color=#111111[after];"
        "[before][after]hstack=inputs=2[stack];"
        "color=c=#06080B:s=1280x720:r=30[canvas];"
        "[canvas][stack]overlay=x=38:y=174[base];"
        "[base]"
        "drawbox=x=0:y=0:w=iw:h=18:color=#00797A@0.95:t=fill,"
        "drawbox=x=0:y=18:w=iw*0.22:h=8:color=#3DDBD9@0.95:t=fill,"
        "drawbox=x=iw*0.22:y=18:w=iw*0.18:h=8:color=#60267D@0.92:t=fill,"
        f"drawtext=font='DejaVu Sans':text='{title}':x=(w-tw)/2:y=58:fontsize=42:fontcolor=white,"
        f"drawtext=font='DejaVu Sans':text='{before}':x=58:y=128:fontsize=24:fontcolor=#E9ECEF,"
        f"drawtext=font='DejaVu Sans':text='{after}':x=682:y=128:fontsize=24:fontcolor=#3DDBD9,"
        "drawbox=x=38:y=174:w=604:h=340:color=#6C757D@0.9:t=3,"
        "drawbox=x=642:y=174:w=604:h=340:color=#00797A@0.9:t=3,"
        "drawtext=font='DejaVu Sans':text='Metadata, captions, music ducking, track icons, rating color':"
        "x=(w-tw)/2:y=562:fontsize=25:fontcolor=#E9ECEF,"
        "format=yuv420p[vout]"
    )

    run_ffmpeg(
        [
            "-i",
            str(args.before),
            "-i",
            str(args.after),
            "-filter_complex",
            filter_complex,
            "-map",
            "[vout]",
            "-map",
            "1:a?",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-preset",
            "veryfast",
            "-crf",
            "21",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
            "-shortest",
            str(args.output),
        ]
    )
    print(args.output)


if __name__ == "__main__":
    main()
