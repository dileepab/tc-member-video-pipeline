from __future__ import annotations

import argparse
import json
from pathlib import Path

import httpx


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Smoke-test a deployed Topcoder profile video API.")
    parser.add_argument("base_url", help="Deployment base URL, for example https://example.onrender.com")
    parser.add_argument(
        "--video",
        type=Path,
        default=Path("demo-output/before_raw_intro.mp4"),
        help="15-30 second raw clip to upload through POST /render.",
    )
    parser.add_argument(
        "--metadata",
        type=Path,
        default=Path("samples/member_metadata.json"),
        help="Member metadata JSON file.",
    )
    parser.add_argument(
        "--skip-render",
        action="store_true",
        help="Only check root, health, and docs endpoints.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    base_url = args.base_url.rstrip("/")

    for path in ("/", "/health", "/docs"):
        response = httpx.get(base_url + path, timeout=30)
        response.raise_for_status()
        print(f"OK {path}: {response.status_code}")

    if args.skip_render:
        return

    metadata = args.metadata.read_text(encoding="utf-8")
    render_options = json.dumps({"aspect": "landscape"})
    with args.video.open("rb") as video_file:
        response = httpx.post(
            base_url + "/render",
            files={"video": (args.video.name, video_file, "video/mp4")},
            data={"metadata_json": metadata, "render_options_json": render_options},
            timeout=180,
        )
    response.raise_for_status()
    payload = response.json()
    print(json.dumps(payload, indent=2))

    landscape_url = (
        payload.get("download_urls", {})
        .get("outputs", {})
        .get("landscape")
    )
    if not landscape_url:
        raise RuntimeError("render response did not include a landscape download URL")
    download = httpx.get(base_url + landscape_url, timeout=60)
    download.raise_for_status()
    print(f"OK download {landscape_url}: {len(download.content)} bytes")


if __name__ == "__main__":
    main()
