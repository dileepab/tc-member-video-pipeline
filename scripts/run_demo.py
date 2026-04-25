from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import get_settings
from app.ffmpeg import probe_duration
from app.models import MemberMetadata, RenderOptions
from app.pipeline import ProfileVideoPipeline, _result_to_dict
from scripts.generate_sample import generate_sample_raw_video


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render a Topcoder profile intro demo from the bundled sample clip or a generated fallback."
    )
    parser.add_argument(
        "--input",
        type=Path,
        help="Optional path to a specific input video. When omitted, the bundled sample clip is used if present; otherwise a reproducible 18-second sample clip is generated.",
    )
    parser.add_argument(
        "--metadata",
        type=Path,
        default=Path("samples/member_metadata.json"),
        help="Path to the member metadata JSON file.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("demo-output/after"),
        help="Directory for rendered outputs.",
    )
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=Path("demo-output/work"),
        help="Directory for intermediate render artifacts.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_root = Path("demo-output")
    bundled_sample = output_root / "Profile_Intro_Video_Generated.mp4"
    if args.input:
        raw_path = args.input
    elif bundled_sample.exists() and probe_duration(bundled_sample) > 0:
        raw_path = bundled_sample
    else:
        raw_path = generate_sample_raw_video(output_root / "before_raw_intro.mp4")
    metadata = MemberMetadata.from_dict(json.loads(args.metadata.read_text()))
    pipeline = ProfileVideoPipeline(get_settings())
    result = pipeline.process_file(
        input_video=raw_path,
        metadata=metadata,
        options=RenderOptions.from_dict(
            {
                "aspect": "both",
                "output_dir": str(args.output_dir),
                "work_dir": str(args.work_dir),
                "keep_intermediates": False,
            }
        ),
        job_id="demo-topcoder-star",
    )
    print(json.dumps(_result_to_dict(result), indent=2))


if __name__ == "__main__":
    main()
