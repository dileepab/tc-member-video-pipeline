from __future__ import annotations

from pathlib import Path

from app.ffmpeg import has_audio_stream, run_ffmpeg


def clean_voice_track(input_video: Path, output_audio: Path, duration: float) -> Path:
    output_audio.parent.mkdir(parents=True, exist_ok=True)
    if has_audio_stream(input_video):
        # Voice cleanup chain — order matters:
        #   1. Steep 2-pole highpass at 120 Hz to remove sub-bass rumble.
        #      Vocal fundamentals start ~85 Hz (deep male voice) but losing
        #      sub-120 Hz keeps voice intelligibility while killing room rumble.
        #   2. Notch filters at 50/60 Hz and their first three harmonics —
        #      catches AC mains hum from either 50 Hz or 60 Hz electrical
        #      systems regardless of where the clip was recorded.
        #   3. Lowpass at 12 kHz to cut hiss above intelligible vocal range.
        #   4. afftdn FFT denoiser, more aggressive nf=-30 to suppress
        #      broadband background noise (room tone, AC hum, fans).
        #   5. Loudnorm to consistent -16 LUFS broadcast target.
        run_ffmpeg(
            [
                "-i",
                str(input_video),
                "-vn",
                "-af",
                (
                    "highpass=f=120:poles=2,"
                    "bandreject=f=50:width_type=h:w=4,"
                    "bandreject=f=60:width_type=h:w=4,"
                    "bandreject=f=100:width_type=h:w=6,"
                    "bandreject=f=120:width_type=h:w=6,"
                    "bandreject=f=150:width_type=h:w=8,"
                    "bandreject=f=180:width_type=h:w=8,"
                    "lowpass=f=12000,"
                    "afftdn=nf=-30,"
                    "loudnorm=I=-16:TP=-1.5:LRA=11"
                ),
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
    """Render a quiet, melodic music bed with FFmpeg's lavfi synthesis.

    Designed specifically to avoid any "AC hum" perception:

    - Zero pure sine tones below 440 Hz.
    - All percussion is high-passed noise (>200 Hz center), so no sub-bass
      tonal content can ring at frequencies that sound like mains hum.
    - The only tonal layer is a four-note A-minor arpeggio (A4-C5-E5-A5)
      plucked with a short envelope — the ear hears melody, not drone.
    - A master ``highpass=200 Hz`` cuts everything below 200 Hz hard, so any
      residual low-frequency artifact from the synthesis chain is removed.

    Layers (beat = 0.5 s, bar = 2 s):
    - tom-snap: bandpassed noise around 250 Hz, envelope on every beat → reads as a soft drum hit
    - hat:      high-passed white noise, 8th-note gate
    - snap:     bandpassed noise around 1.7 kHz on the backbeat
    - arp1-4:   A4 / C5 / E5 / A5 plucks, sequenced through the bar

    Forum guidance: synthetic music is acceptable; for the most polished
    output, production callers should pass ``music_path`` in ``RenderOptions``
    pointing at a licensed track.
    """

    output_audio.parent.mkdir(parents=True, exist_ok=True)
    length = max(duration, 3.0)
    fade_out_start = max(length - 0.8, 0.5)
    run_ffmpeg(
        [
            "-f", "lavfi", "-t", str(length),
            "-i", "anoisesrc=color=white:sample_rate=48000:amplitude=0.8",
            "-f", "lavfi", "-t", str(length),
            "-i", "anoisesrc=color=white:sample_rate=48000:amplitude=0.8",
            "-f", "lavfi", "-t", str(length),
            "-i", "anoisesrc=color=pink:sample_rate=48000:amplitude=0.9",
            "-f", "lavfi", "-t", str(length),
            "-i", "sine=frequency=440:sample_rate=48000",
            "-f", "lavfi", "-t", str(length),
            "-i", "sine=frequency=523.25:sample_rate=48000",
            "-f", "lavfi", "-t", str(length),
            "-i", "sine=frequency=659.25:sample_rate=48000",
            "-f", "lavfi", "-t", str(length),
            "-i", "sine=frequency=880:sample_rate=48000",
            "-filter_complex",
            (
                # Tom-snap: noise burst centered at 250 Hz, never a sustained tone
                "[0:a]bandpass=f=260:width_type=h:w=160,"
                "volume='0.40*exp(-25*mod(t,0.5))':eval=frame[tom];"
                # Hi-hat: high-passed noise, 8th-note gate
                "[1:a]highpass=f=6000,"
                "volume='if(lt(mod(t,0.25),0.035),0.22,0)':eval=frame[hat];"
                # Snap on backbeat
                "[2:a]bandpass=f=1700:width_type=h:w=1300,"
                "volume='if(lt(mod(t+0.5,1.0),0.05),0.40,0)':eval=frame[snap];"
                # Arpeggio: each note plucked in its 0.5 s slot of a 2 s bar
                "[3:a]volume='if(lt(mod(t,2.0),0.5),0.12*exp(-6*mod(t,0.5)),0)':eval=frame[arp1];"
                "[4:a]volume='if(between(mod(t,2.0),0.5,1.0),0.12*exp(-6*mod(t,0.5)),0)':eval=frame[arp2];"
                "[5:a]volume='if(between(mod(t,2.0),1.0,1.5),0.12*exp(-6*mod(t,0.5)),0)':eval=frame[arp3];"
                "[6:a]volume='if(gte(mod(t,2.0),1.5),0.12*exp(-6*mod(t,0.5)),0)':eval=frame[arp4];"
                "[tom][hat][snap][arp1][arp2][arp3][arp4]"
                "amix=inputs=7:duration=first:normalize=0,"
                "highpass=f=200,"
                "aresample=48000,"
                "afade=t=in:st=0:d=0.5,"
                f"afade=t=out:st={fade_out_start:.2f}:d=0.7[mix]"
            ),
            "-map", "[mix]",
            "-c:a", "aac",
            "-b:a", "160k",
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

    # Note: we intentionally skip a final loudnorm on the mixed track because
    # single-pass loudnorm aggressively boosts quiet sections — that would
    # pump the music up during the silent intro/outro window and re-introduce
    # the perception of low-frequency drone.  The voice was already loudnorm'd
    # to -16 LUFS upstream, the music is already loudness-targeted in the bed
    # generator, and a soft alimiter at the end protects against clipping
    # without changing perceived dynamics.
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
            "alimiter=limit=0.95:level=disabled[aout]",
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
