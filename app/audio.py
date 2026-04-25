from __future__ import annotations

from pathlib import Path

from app.ffmpeg import has_audio_stream, run_ffmpeg


def clean_voice_track(input_video: Path, output_audio: Path, duration: float) -> Path:
    output_audio.parent.mkdir(parents=True, exist_ok=True)
    if has_audio_stream(input_video):
        run_ffmpeg(
            [
                "-i",
                str(input_video),
                "-vn",
                "-af",
                "highpass=f=80,lowpass=f=12000,afftdn=nf=-25,loudnorm=I=-16:TP=-1.5:LRA=11",
                "-c:a",
                "aac",
                "-b:a",
                "160k",
                str(output_audio),
            ]
        )
    else:
        run_ffmpeg(
            [
                "-f",
                "lavfi",
                "-t",
                str(max(duration, 1.0)),
                "-i",
                "anullsrc=r=48000:cl=stereo",
                "-c:a",
                "aac",
                str(output_audio),
            ]
        )
    return output_audio


def generate_music_bed(output_audio: Path, duration: float) -> Path:
    output_audio.parent.mkdir(parents=True, exist_ok=True)
    length = max(duration, 3.0)
    run_ffmpeg(
        [
            "-f",
            "lavfi",
            "-t",
            str(length),
            "-i",
            "sine=frequency=110:sample_rate=48000",
            "-f",
            "lavfi",
            "-t",
            str(length),
            "-i",
            "sine=frequency=220:sample_rate=48000",
            "-f",
            "lavfi",
            "-t",
            str(length),
            "-i",
            "sine=frequency=880:sample_rate=48000",
            "-filter_complex",
            "[0:a]volume=0.08[a0];"
            "[1:a]volume=0.055[a1];"
            "[2:a]volume=0.025,atrim=0:0.08,asetpts=PTS-STARTPTS,aloop=loop=-1:size=3840[hat];"
            "[a0][a1][hat]amix=inputs=3:duration=first:normalize=0,"
            "afade=t=in:st=0:d=0.3,afade=t=out:st="
            f"{max(length - 0.8, 0.5)}:d=0.7[mix]",
            "-map",
            "[mix]",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            str(output_audio),
        ]
    )
    return output_audio


def mix_voice_and_music(
    voice_audio: Path,
    music_audio: Path,
    output_audio: Path,
    *,
    duration: float = 0.0,
    music_volume: float = 0.55,
    music_lead_volume: float = 1.1,
    music_intro_seconds: float = 2.0,
    music_outro_seconds: float = 1.6,
) -> Path:
    """Mix the cleaned voice with a music bed.

    The music is sidechain-compressed against the voice so it ducks
    automatically while the speaker is talking.  On top of that we apply a
    time-varying volume curve so the bed is audibly louder during the silent
    intro and outro windows than under speech — without that boost the music
    is essentially inaudible until the voice stops at the very end of the
    clip.  The curve is expressed in seconds against the voice timeline.
    """

    output_audio.parent.mkdir(parents=True, exist_ok=True)

    # Build a piecewise volume expression for the music.  Inside the intro and
    # outro windows we use ``music_lead_volume``; everywhere else (under voice)
    # we use ``music_volume``.  When ``duration`` is unknown (0) or the lead
    # boost is disabled, fall back to a constant volume — preserves the
    # previous behaviour for callers that don't pass the new args.
    if music_lead_volume <= 0 or music_lead_volume == music_volume or duration <= 0:
        volume_filter = f"volume={music_volume:.3f}"
    else:
        intro_end = max(music_intro_seconds, 0.0)
        outro_start = max(duration - music_outro_seconds, intro_end + 0.5)
        # ``eval=frame`` re-evaluates the expression every audio frame so the
        # piecewise values switch cleanly at the boundaries.
        vol_expr = (
            f"if(lt(t,{intro_end:.3f}),{music_lead_volume:.3f},"
            f"if(gt(t,{outro_start:.3f}),{music_lead_volume:.3f},{music_volume:.3f}))"
        )
        volume_filter = f"volume='{vol_expr}':eval=frame"

    run_ffmpeg(
        [
            "-i",
            str(voice_audio),
            "-stream_loop",
            "-1",
            "-i",
            str(music_audio),
            "-filter_complex",
            "[1:a][0:a]sidechaincompress=threshold=0.025:ratio=8:attack=20:release=450,"
            f"{volume_filter}[ducked];"
            "[0:a][ducked]amix=inputs=2:duration=first:normalize=0,"
            "loudnorm=I=-16:TP=-1.5:LRA=11[aout]",
            "-map",
            "[aout]",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            str(output_audio),
        ]
    )
    return output_audio
