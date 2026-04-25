from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from app.models import MemberMetadata


@dataclass(frozen=True)
class TrackBranding:
    name: str
    icon_path: Path | None
    accent_color: str


@dataclass(frozen=True)
class BrandPackage:
    background_color: str
    surface_color: str
    primary_color: str
    accent_color: str
    secondary_color: str
    muted_color: str
    icon_text: str
    skills_label: str
    caption_font: str
    tracks: list[TrackBranding]
    logo_wordmark_path: Path | None
    logo_mark_path: Path | None


def build_brand_package(metadata: MemberMetadata, template: str = "topcoder-star") -> BrandPackage:
    theme = load_theme(template)
    primary_track_name = metadata.tracks[0].value
    primary_track_theme = theme.get("tracks", {}).get(primary_track_name, {})
    base_theme = theme.get("base", {})
    skills = "  •  ".join(metadata.top_skills[:4]) if metadata.top_skills else "Topcoder Member"

    tracks_branding = []
    for track in metadata.tracks[:1]:
        t_theme = theme.get("tracks", {}).get(track.value, {})
        tracks_branding.append(TrackBranding(
            name=track.value.upper(),
            icon_path=_asset_path(t_theme.get("iconAsset")),
            accent_color=normalize_hex(t_theme.get("accent", "#29A7DF"), theme=theme)
        ))

    return BrandPackage(
        background_color=normalize_hex(base_theme.get("background", "#0A0A0A"), theme=theme),
        surface_color=normalize_hex(base_theme.get("surface", "#0B3D56"), theme=theme),
        primary_color=normalize_hex(metadata.rating_color, theme=theme),
        accent_color=normalize_hex(primary_track_theme.get("accent", "#29A7DF"), theme=theme),
        secondary_color=normalize_hex(base_theme.get("secondary", "#60267D"), theme=theme),
        muted_color=normalize_hex(base_theme.get("muted", "#E9ECEF"), theme=theme),
        icon_text=str(primary_track_theme.get("icon", "[]")),
        skills_label=skills,
        caption_font=str(primary_track_theme.get("captionFont", "DejaVu Sans")),
        tracks=tracks_branding,
        logo_wordmark_path=_asset_path(theme.get("assets", {}).get("logoWordmark")),
        logo_mark_path=_asset_path(theme.get("assets", {}).get("logoMark")),
    )


@lru_cache(maxsize=8)
def load_theme(template: str) -> dict:
    assets_dir = Path(__file__).resolve().parents[1] / "assets" / "branding"
    candidates = [
        assets_dir / f"{template}.json",
        assets_dir / "topcoder-star.json",
        assets_dir / "topcoder_theme.json",
    ]
    for path in candidates:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    return {}


def normalize_hex(value: str, *, theme: dict | None = None) -> str:
    theme = theme or {}
    rating_colors = {
        str(name).lower(): color
        for name, color in (theme.get("ratingColors", {}) or {}).items()
    }
    named = {
        "red": "#EF3A3A",
        "yellow": "#F2C94C",
        "blue": "#2D9CDB",
        "green": "#27AE60",
        "gray": "#8C8C8C",
        "grey": "#8C8C8C",
        "orange": "#F2994A",
        "purple": "#9B51E0",
        "teal": "#00797A",
        "cyan": "#3DDBD9",
        "white": "#FFFFFF",
        "black": "#000000",
    }
    palette = {**named, **rating_colors}
    if value.lower() in palette:
        return palette[value.lower()]
    return value if value.startswith("#") else f"#{value}"


def _asset_path(value: str | None) -> Path | None:
    if not value:
        return None
    path = Path(__file__).resolve().parents[1] / value
    return path if path.exists() else None
