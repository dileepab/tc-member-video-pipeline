from app.models import MemberMetadata, RenderAspect, RenderOptions, Track


def test_member_metadata_accepts_top_tracks_alias() -> None:
    metadata = MemberMetadata.from_dict(
        {
            "handle": "coder",
            "rating_color": "red",
            "top_tracks": ["Dev", "data science"],
            "top_skills": ["Python", "AWS"],
        }
    )

    assert metadata.handle == "coder"
    assert metadata.tracks == [Track.DEV, Track.DATA_SCIENCE]


def test_render_options_defaults_to_both() -> None:
    options = RenderOptions.from_dict({})

    assert options.aspect == RenderAspect.BOTH


def test_member_metadata_display_rating_falls_back_to_named_label() -> None:
    metadata = MemberMetadata.from_dict(
        {
            "handle": "coder",
            "rating_color": "yellow",
            "tracks": ["Dev"],
            "top_skills": [],
        }
    )

    assert metadata.display_rating() == "YELLOW RATED"
