from app.branding import build_brand_package, normalize_hex
from app.models import MemberMetadata


def test_brand_package_uses_track_icon_and_rating_color() -> None:
    metadata = MemberMetadata.from_dict(
        {
            "handle": "coder",
            "rating_color": "yellow",
            "tracks": ["Design"],
            "top_skills": ["Figma", "UX"],
        }
    )

    brand = build_brand_package(metadata)

    assert brand.primary_color == "#FFC107"
    assert brand.icon_text == "◈"
    assert brand.caption_font == "DejaVu Serif"
    assert brand.skills_label == "Figma  •  UX"
    assert len(brand.tracks) > 0
    assert brand.tracks[0].icon_path.name == "track-design.png"
    assert brand.tracks[0].name == "DESIGN"
    assert brand.logo_wordmark_path is not None
    assert brand.logo_wordmark_path.name == "logo.min.png"
    assert brand.logo_mark_path is not None
    assert brand.logo_mark_path.name == "logo.min.png"


def test_normalize_hex_preserves_hex_values() -> None:
    assert normalize_hex("29A7DF") == "#29A7DF"
