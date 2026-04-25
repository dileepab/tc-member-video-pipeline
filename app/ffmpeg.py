from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path


class FFmpegError(RuntimeError):
    pass


def ensure_ffmpeg() -> None:
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise FFmpegError("ffmpeg and ffprobe must be installed and available on PATH")


def run_ffmpeg(args: list[str], *, timeout: int = 300) -> None:
    ensure_ffmpeg()
    command = ["ffmpeg", "-hide_banner", "-y", *args]
    result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0:
        raise FFmpegError(result.stderr[-4000:])


def run_ffprobe(path: Path) -> dict:
    ensure_ffmpeg()
    command = [
        "ffprobe",
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(path),
    ]
    result = subprocess.run(command, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        raise FFmpegError(result.stderr[-4000:])
    return json.loads(result.stdout)


def probe_duration(path: Path) -> float:
    payload = run_ffprobe(path)
    duration = payload.get("format", {}).get("duration")
    if duration is None:
        return 0.0
    return float(duration)


def has_audio_stream(path: Path) -> bool:
    payload = run_ffprobe(path)
    return any(stream.get("codec_type") == "audio" for stream in payload.get("streams", []))


def escape_drawtext(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace(":", "\\:")
        .replace("'", "\\'")
        .replace("%", "\\%")
        .replace("\n", " ")
    )


def escape_filter_path(path: Path) -> str:
    return path.resolve().as_posix().replace("\\", "\\\\").replace(":", "\\:")
