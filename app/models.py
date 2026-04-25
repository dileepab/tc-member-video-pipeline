from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any


class Track(StrEnum):
    DEV = "Dev"
    DESIGN = "Design"
    DATA_SCIENCE = "Data Science"


class RenderAspect(StrEnum):
    LANDSCAPE = "landscape"
    VERTICAL = "vertical"
    BOTH = "both"


@dataclass(frozen=True)
class MemberMetadata:
    handle: str
    rating_color: str
    tracks: list[Track]
    top_skills: list[str]
    rating_label: str | None = None
    intro_text: str | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "MemberMetadata":
        handle = str(payload.get("handle", "")).strip()
        if not handle:
            raise ValueError("member metadata requires a non-empty handle")

        rating_color = str(
            payload.get("rating_color") or _rating_color_from_score(payload.get("rating")) or "#EF3A3A"
        ).strip()
        if not _is_color(rating_color):
            raise ValueError("rating_color must be a CSS hex color or supported color name")

        raw_tracks = (
            payload.get("tracks")
            or payload.get("top_tracks")
            or payload.get("top_track")
            or payload.get("track")
            or ["Dev"]
        )
        if isinstance(raw_tracks, str):
            raw_tracks = [raw_tracks]
        tracks = [_parse_track(value) for value in raw_tracks]

        raw_skills = payload.get("top_skills") or payload.get("skills") or []
        top_skills = [str(skill).strip() for skill in raw_skills]
        top_skills = [skill for skill in top_skills if skill]

        return cls(
            handle=handle,
            rating_color=rating_color,
            rating_label=payload.get("rating_label"),
            tracks=tracks,
            top_skills=top_skills,
            intro_text=payload.get("intro_text"),
        )

    def display_rating(self) -> str:
        if self.rating_label:
            return self.rating_label

        normalized = self.rating_color.strip().lower()
        named_labels = {
            "red": "RED RATED",
            "yellow": "YELLOW RATED",
            "blue": "BLUE RATED",
            "green": "GREEN RATED",
            "gray": "GRAY RATED",
            "grey": "GRAY RATED",
        }
        if normalized in named_labels:
            return named_labels[normalized]

        hex_value = normalized if normalized.startswith("#") else f"#{normalized}"
        hex_labels = {
            "#dc3545": "RED RATED",
            "#ef3a3a": "RED RATED",
            "#ffc107": "YELLOW RATED",
            "#f2c94c": "YELLOW RATED",
            "#0d61bf": "BLUE RATED",
            "#2d9cdb": "BLUE RATED",
            "#28a745": "GREEN RATED",
            "#27ae60": "GREEN RATED",
            "#6c757d": "GRAY RATED",
            "#8c8c8c": "GRAY RATED",
        }
        return hex_labels.get(hex_value, "TOPCODER MEMBER")


@dataclass(frozen=True)
class RenderOptions:
    aspect: RenderAspect = RenderAspect.BOTH
    template: str = "topcoder-star"
    output_dir: Path = Path("outputs")
    work_dir: Path = Path("work")
    music_path: Path | None = None
    keep_intermediates: bool = False
    # Music mix shaping.  ``music_volume`` is the level applied while voice is
    # active (after sidechain ducking) — keep it low so speech stays intelligible.
    # ``music_lead_volume`` is the level during the silent intro/outro windows;
    # this is what makes music actually audible at the start of the clip rather
    # than only after the speaker stops.  Set ``music_lead_volume`` <= 0 to keep
    # the previous behaviour of a single uniform music volume.
    music_volume: float = 0.55
    music_lead_volume: float = 1.1
    music_intro_seconds: float = 2.0
    music_outro_seconds: float = 1.6

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None = None) -> "RenderOptions":
        payload = payload or {}
        aspect = RenderAspect(payload.get("aspect", RenderAspect.BOTH))
        music_path = payload.get("music_path")
        return cls(
            aspect=aspect,
            template=str(payload.get("template", "topcoder-star")),
            output_dir=Path(payload.get("output_dir", "outputs")),
            work_dir=Path(payload.get("work_dir", "work")),
            music_path=Path(music_path) if music_path else None,
            keep_intermediates=bool(payload.get("keep_intermediates", False)),
            music_volume=float(payload.get("music_volume", 0.55)),
            music_lead_volume=float(payload.get("music_lead_volume", 1.1)),
            music_intro_seconds=float(payload.get("music_intro_seconds", 2.0)),
            music_outro_seconds=float(payload.get("music_outro_seconds", 1.6)),
        )


@dataclass
class CaptionSegment:
    start: float
    end: float
    text: str


@dataclass
class RenderResult:
    job_id: str
    input_uri: str
    outputs: dict[str, str]
    captions: dict[str, str]
    manifest_path: str
    duration_seconds: float
    estimated_cost_usd: float
    output_file_sizes_bytes: dict[str, int] = field(default_factory=dict)
    timings: dict[str, float] = field(default_factory=dict)
    adapters: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


_COLOR_NAMES = {
    "red",
    "yellow",
    "blue",
    "green",
    "gray",
    "grey",
    "orange",
    "purple",
    "white",
    "black",
}


def _is_color(value: str) -> bool:
    if value.lower() in _COLOR_NAMES:
        return True
    return bool(re.fullmatch(r"#?[0-9a-fA-F]{6}", value))


def _rating_color_from_score(value: Any) -> str | None:
    if value is None:
        return None
    try:
        rating = int(float(value))
    except (TypeError, ValueError):
        return None
    if rating >= 2200:
        return "red"
    if rating >= 1500:
        return "yellow"
    if rating >= 1200:
        return "blue"
    if rating >= 900:
        return "green"
    return "gray"


def _parse_track(value: Any) -> Track:
    normalized = str(value).strip().lower().replace("_", " ")
    aliases = {
        "dev": Track.DEV,
        "development": Track.DEV,
        "design": Track.DESIGN,
        "data": Track.DATA_SCIENCE,
        "data science": Track.DATA_SCIENCE,
        "datascience": Track.DATA_SCIENCE,
    }
    if normalized not in aliases:
        raise ValueError(f"unsupported track: {value}")
    return aliases[normalized]
