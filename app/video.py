from __future__ import annotations

from pathlib import Path

from app.branding import BrandPackage
from app.ffmpeg import escape_drawtext, escape_filter_path, run_ffmpeg
from app.models import MemberMetadata, RenderAspect


def render_profile_video(
    *,
    input_video: Path,
    mixed_audio: Path,
    captions_ass: Path,
    output_video: Path,
    metadata: MemberMetadata,
    brand: BrandPackage,
    aspect: RenderAspect,
    duration_seconds: float,
) -> Path:
    output_video.parent.mkdir(parents=True, exist_ok=True)
    width, height = (1280, 720) if aspect == RenderAspect.LANDSCAPE else (1080, 1920)
    vf = _video_filter(
        width=width,
        height=height,
        metadata=metadata,
        brand=brand,
        captions_ass=captions_ass,
        duration_seconds=duration_seconds,
        vertical=aspect == RenderAspect.VERTICAL,
    )
    maxrate = "6M"
    bufsize = "12M"
    run_ffmpeg(
        [
            "-i",
            str(input_video),
            "-i",
            str(mixed_audio),
            "-filter_complex",
            vf,
            "-map",
            "[vout]",
            "-map",
            "1:a",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-preset",
            "veryfast",
            "-crf",
            "20",
            "-maxrate",
            maxrate,
            "-bufsize",
            bufsize,
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
            "-shortest",
            str(output_video),
        ],
        timeout=600,
    )
    return output_video


def _video_filter(
    *,
    width: int,
    height: int,
    metadata: MemberMetadata,
    brand: BrandPackage,
    captions_ass: Path,
    duration_seconds: float,
    vertical: bool,
) -> str:
    handle = escape_drawtext(f"@{metadata.handle}")
    rating = escape_drawtext(metadata.display_rating())
    # track is now handled by track_layers loop

    skills = escape_drawtext(brand.skills_label)
    icon_text = escape_drawtext(brand.icon_text)
    background = brand.background_color
    surface = brand.surface_color
    primary = brand.primary_color
    accent = brand.accent_color
    secondary = brand.secondary_color
    muted = brand.muted_color
    ass_path = escape_filter_path(captions_ass)
    # We now handle multiple track icons in the logo_overlays loop

    logo_wordmark_path = (
        escape_filter_path(brand.logo_wordmark_path) if brand.logo_wordmark_path else None
    )
    outro_start = max(duration_seconds - 1.4, 0.0)

    handle_size = 58 if vertical else 44
    meta_size = 34 if vertical else 26
    icon_size = 56 if vertical else 40
    lower_y = "h-380" if vertical else "h-270"
    lower_y_box = "ih-380" if vertical else "ih-270"
    lower_y_overlay = "H-380" if vertical else "H-270"
    lower_panel_height = 280 if vertical else 240
    accent_bar_height = 245 if vertical else 205
    handle_y = f"{lower_y}+45" if vertical else f"{lower_y}+40"
    rating_y = f"{lower_y}+53" if vertical else f"{lower_y}+48"
    track_y = f"{lower_y}+140" if vertical else f"{lower_y}+110"
    skill_y = f"{lower_y}+200" if vertical else f"{lower_y}+150"
    icon_y = f"{lower_y_overlay}+129" if vertical else f"{lower_y_overlay}+103"
    reveal_time = 1.55
    lower_enable = f"between(t,0.75,{outro_start:.2f})"
    main_logo_enable = f"between(t,0.85,{outro_start:.2f})"
    handle_x = _expr(f"if(lt(t,{reveal_time}),82-({reveal_time}-t)*240,82)")
    icon_x = _expr(f"if(lt(t,{reveal_time}),82-({reveal_time}-t)*240,82)")
    text_x = _expr(f"if(lt(t,{reveal_time}),156-({reveal_time}-t)*240,156)")
    rating_x = _expr(f"if(lt(t,{reveal_time}),w-tw-82+({reveal_time}-t)*240,w-tw-82)")

    icon_gap = 12


    intro_handle_y = _expr("if(lt(t,0.95),(h-th)/2-46-(0.95-t)*120,(h-th)/2-46)")
    intro_sub_y = _expr("if(lt(t,0.95),(h-th)/2+36-(0.95-t)*90,(h-th)/2+36)")
    outro_handle_y = _expr(
        f"(h-th)/2-36+if(lt(t,{outro_start + 0.6:.2f}),({outro_start + 0.6:.2f}-t)*70,0)"
    )
    outro_sub_y = _expr(
        f"(h-th)/2+42+if(lt(t,{outro_start + 0.6:.2f}),({outro_start + 0.6:.2f}-t)*50,0)"
    )
    if vertical:
        wordmark_width = 210        # 75% of previous 280
        center_wordmark_width = 350
        top_logo_x = "52"
        top_logo_y = "48"
        intro_logo_y = "96"
    else:
        wordmark_width = 150        # 75% of previous 200
        center_wordmark_width = 280
        top_logo_x = "24"           # floats in corner — no strip above it
        top_logo_y = "12"
        intro_logo_y = "36"

    badge_size = 78 if vertical else 62
    icon_badge_filter = ""
    track_text_box = ""
    fallback_icon_layer = ""

    # Portrait keeps the solid branding strip + accent bars to hide the raw frame
    # edge behind the wider logo and rating bar. Landscape has no top strip; the
    # lower-third panel below is the only main-content scrim.
    if vertical:
        top_strip_filter = (
            f"drawbox=x=0:y=0:w=iw:h=ih:color={background}@0.16:t=fill,"
            f"drawbox=x=0:y=0:w=iw:h=22:color={surface}@0.92:t=fill,"
            f"drawbox=x=0:y=22:w=iw*0.22:h=8:color={accent}@0.95:t=fill,"
            f"drawbox=x=iw*0.22:y=22:w=iw*0.18:h=8:color={secondary}@0.92:t=fill,"
            f"drawbox=x=iw*0.40:y=22:w=iw*0.14:h=8:color={primary}@0.95:t=fill,"
        )
    else:
        top_strip_filter = ""

    logo_prefix = ""
    logo_overlays = ""
    working_label = "vbase"
    if logo_wordmark_path:
        logo_prefix += (
            f"movie='{logo_wordmark_path}',format=rgba,colorchannelmixer=aa=0.6,"
            f"scale={wordmark_width}:-1[wordmark_small];"
            f"movie='{logo_wordmark_path}',format=rgba,"
            f"scale={center_wordmark_width}:-1[wordmark_center];"
        )
        logo_overlays += (
            f"[{working_label}][wordmark_small]overlay=x={top_logo_x}:y={top_logo_y}:enable='{main_logo_enable}'[vlogo1];"
            f"[vlogo1][wordmark_center]overlay=x=(W-w)/2:y={intro_logo_y}:enable='lt(t,0.85)+gte(t,{outro_start})'[vlogo2];"
        )
        working_label = "vlogo2"
    track_layers = ""
    segment_x = icon_x
    for i, t_brand in enumerate(brand.tracks):
        if t_brand.icon_path:
            icon_label = f"track_icon_{i}"
            vlogo_label = f"vlogo_track_{i}"
            safe_path = escape_filter_path(t_brand.icon_path)
            logo_prefix += f"movie='{safe_path}',scale={icon_size}:-1[{icon_label}];"
            logo_overlays += (
                f"[{working_label}][{icon_label}]overlay=x={segment_x}:y={icon_y}:enable='{lower_enable}'[{vlogo_label}];"
            )
            working_label = vlogo_label

        # Draw track name after icon
        text_start_x = f"{segment_x}+{icon_size + icon_gap}" if t_brand.icon_path else segment_x
        track_layers += (
            f"drawtext=font='DejaVu Sans':text='{escape_drawtext(t_brand.name)}':x={text_start_x}:y={track_y}:"
            f"fontsize={meta_size}:fontcolor={t_brand.accent_color}{track_text_box}:enable='{lower_enable}',"
        )

        # Advance segment_x for next track
        char_w = 18 if vertical else 14
        segment_w = (icon_size + icon_gap if t_brand.icon_path else 0) + (len(t_brand.name) * char_w) + 40
        segment_x = f"{segment_x}+{segment_w}"


    return (
        f"{logo_prefix}"
        f"[0:v]split=2[base][fg];"
        f"[base]scale={width}:{height}:force_original_aspect_ratio=increase,"
        f"crop={width}:{height},boxblur=24:2,eq=brightness=0.02:saturation=1.12[bg];"
        f"[fg]scale={width}:{height}:force_original_aspect_ratio=decrease[person];"
        f"[bg][person]overlay=(W-w)/2:(H-h)/2,"
        "eq=contrast=1.06:saturation=1.08:gamma=1.02,unsharp=5:5:0.55,"
        f"{top_strip_filter}"
        f"drawbox=x=0:y={lower_y_box}:w=iw:h={lower_panel_height}:color={background}@0.74:t=fill:enable='{lower_enable}',"
        f"drawbox=x=54:y={lower_y_box}:w=9:h={accent_bar_height}:color={primary}@1:t=fill:enable='{lower_enable}',"
        f"{icon_badge_filter}"
        f"drawtext=font='DejaVu Sans':text='{handle}':x={handle_x}:y={handle_y}:"
        f"fontsize={handle_size}:fontcolor=white:shadowcolor={background}@0.6:shadowx=2:shadowy=2:enable='{lower_enable}',"
        f"{track_layers}"
        f"drawtext=font='DejaVu Sans':text='{rating}':x={rating_x}:y={rating_y}:"
        f"fontsize={meta_size}:fontcolor=white:box=1:boxcolor={primary}@0.82:boxborderw=12:enable='{lower_enable}',"
        f"drawtext=font='DejaVu Sans':text='{skills}':x={handle_x}+12:y={skill_y}:"
        f"fontsize={meta_size}:fontcolor={muted}@0.95:enable='{lower_enable}',"
        f"drawbox=x=0:y=0:w=iw:h=ih:color={surface}@0.86:t=fill:enable='lt(t,0.85)',"
        f"drawbox=x=0:y=0:w=iw*0.30:h=12:color={accent}@0.95:t=fill:enable='lt(t,0.85)',"
        f"drawbox=x=iw*0.30:y=0:w=iw*0.18:h=12:color={secondary}@0.92:t=fill:enable='lt(t,0.85)',"
        f"drawtext=font='DejaVu Sans':text='TOPCODER STAR':x=(w-tw)/2:y={intro_handle_y}:"
        f"fontsize={70 if vertical else 54}:fontcolor=white:enable='lt(t,0.85)',"
        f"drawtext=font='DejaVu Sans':text='PROFILE INTRO':x=(w-tw)/2:y={intro_sub_y}:"
        f"fontsize={36 if vertical else 30}:fontcolor={accent}:enable='lt(t,0.85)',"
        f"drawbox=x=0:y=0:w=iw:h=ih:color={surface}@0.78:t=fill:enable='gte(t,{outro_start})',"
        f"drawtext=font='DejaVu Sans':text='{handle}':x=(w-tw)/2:y={outro_handle_y}:"
        f"fontsize={64 if vertical else 52}:fontcolor=white:enable='gte(t,{outro_start})',"
        f"drawtext=font='DejaVu Sans':text='READY FOR THE NEXT CHALLENGE':x=(w-tw)/2:y={outro_sub_y}:"
        f"fontsize={32 if vertical else 28}:fontcolor={accent}:enable='gte(t,{outro_start})'"
        f"[vbase];"
        f"{logo_overlays}"
        f"[{working_label}]"
        f"ass='{ass_path}',"
        "format=yuv420p[vout]"
    )


def _expr(value: str) -> str:
    return value.replace(",", "\\,")
