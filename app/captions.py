from __future__ import annotations

from pathlib import Path

from app.branding import normalize_hex
from app.models import CaptionSegment


def write_srt(segments: list[CaptionSegment], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    for index, segment in enumerate(segments, start=1):
        lines.extend(
            [
                str(index),
                f"{_srt_time(segment.start)} --> {_srt_time(segment.end)}",
                segment.text,
                "",
            ]
        )
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


def write_ass(
    segments: list[CaptionSegment],
    output_path: Path,
    *,
    primary_color: str,
    accent_color: str,
    font_name: str = "DejaVu Sans",
    # Render dimensions — must match the target video so libass scales correctly.
    # Portrait (1080×1920) and landscape (1280×720) need different PlayRes values;
    # using a mismatched PlayRes is what caused the oversized portrait font.
    width: int = 1280,
    height: int = 720,
    # When True, draw a semi-transparent box behind each caption line instead of
    # a coloured outline.  This keeps text readable over any background without
    # relying on outline contrast alone.
    box_background: bool = False,
    # Suppress captions that begin before this offset (seconds).  Useful to keep
    # the intro slate and lower-third slide-in animation caption-free.
    min_start_seconds: float = 0.0,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    primary = _ass_color(normalize_hex(primary_color))
    accent = _ass_color(normalize_hex(accent_color))

    is_portrait = height > width

    # Font size — expressed in PlayRes units that map 1-to-1 to the video pixels
    # because we set PlayRes = actual render resolution below.
    # Portrait is narrower (1080 px) so we size relative to width; landscape is
    # shorter so we size relative to height.
    if is_portrait:
        font_size = round(width * 0.044)   # 1080 → 47 ≈ 48 px on screen
    else:
        font_size = round(height * 0.055)  # 720 → 39 ≈ 40 px on screen

    # Vertical margin keeps captions just above the lower-third overlay.
    # Lower-third occupies the bottom 420 px (portrait) / 205 px (landscape).
    if is_portrait:
        margin_v = round(height * 0.230)   # 1920 → 442 px, clears 420-px lower-third
        margin_h = 60
    else:
        margin_v = round(height * 0.410)   # 720 → 295 px, clears the raised lower-third
        margin_h = 80

    if box_background:
        # BorderStyle 3 = opaque box; BackColour fills the box (50 % opaque dark).
        # ASS alpha: 0x00 = fully opaque, 0xFF = fully transparent.
        border_style = 3
        outline = 10   # box padding around the text
        shadow = 0
        back_colour = "&H80000000"
        # White text: always readable against the dark box regardless of the rating
        # colour.  The rating colour is shown in the lower-third overlay instead.
        text_colour = "&H00FFFFFF"
    else:
        border_style = 1
        outline = 3
        shadow = 1
        back_colour = "&H9A050505"
        # Without a box, use the rating colour with a dark outline for contrast.
        text_colour = primary

    lines = [
        "[Script Info]",
        "ScriptType: v4.00+",
        f"PlayResX: {width}",
        f"PlayResY: {height}",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        f"Style: TopcoderCaption,{font_name},{font_size},{text_colour},{accent},&HCC050505,{back_colour},-1,0,0,0,100,100,0,0,{border_style},{outline},{shadow},2,{margin_h},{margin_h},{margin_v},1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    for segment in segments:
        if segment.end <= min_start_seconds:
            continue  # segment ends before the delay window — skip entirely
        actual_start = max(segment.start, min_start_seconds)
        text = segment.text.replace("{", "\\{").replace("}", "\\}")
        lines.append(
            f"Dialogue: 0,{_ass_time(actual_start)},{_ass_time(segment.end)},TopcoderCaption,,0,0,0,,{text}"
        )
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


def _srt_time(seconds: float) -> str:
    millis = round(max(seconds, 0.0) * 1000)
    hours, remainder = divmod(millis, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, ms = divmod(remainder, 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{ms:03}"


def _ass_time(seconds: float) -> str:
    centis = round(max(seconds, 0.0) * 100)
    hours, remainder = divmod(centis, 360_000)
    minutes, remainder = divmod(remainder, 6_000)
    secs, cs = divmod(remainder, 100)
    return f"{hours}:{minutes:02}:{secs:02}.{cs:02}"


def _ass_color(hex_color: str) -> str:
    value = hex_color.lstrip("#")
    red = value[0:2]
    green = value[2:4]
    blue = value[4:6]
    return f"&H00{blue}{green}{red}"
