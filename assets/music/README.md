# Music Assets

This folder ships a bundled royalty-free music track that the pipeline uses by default for the "Hype Factor" / background music requirement, plus a synthetic FFmpeg fallback for offline / no-asset environments.

## Bundled Track

`topcoder-bed.m4a` — a 45-second AAC excerpt of:

> **"Technology" by eliveta** — Pixabay track ID 474054.
> [Pixabay Content License](https://pixabay.com/service/license-summary/) — free for commercial use, **no attribution required**.
> Source: [https://pixabay.com/music/upbeat-technology-474054/](https://pixabay.com/music/upbeat-technology-474054/).

The excerpt was trimmed from the original Pixabay MP3 (start = 8 s, length = 45 s), fade-in/fade-out applied, and loudness-normalized to -20 LUFS so it sits comfortably behind voice when sidechain-ducked.

**Attribution requirement:** none — the Pixabay Content License does not require attribution. See [CREDITS.md](CREDITS.md) for the optional courtesy credit string.

## Pipeline Behavior

- **Default:** when this file is present, `app/pipeline.py` and `app/audio.py` use it as `music_path` automatically.
- **Override:** pass a custom `music_path` in `render_options` to use a different licensed track for production.
- **Fallback:** if the bundled file is missing (e.g., it was stripped from a packaged ZIP), the pipeline falls back to `app/audio.generate_music_bed`, which synthesizes a quiet melodic bed with FFmpeg's `lavfi`. The synth fallback is hum-free but is not as polished as a real composition — replace it with a licensed track for production use.

## Adding Your Own Track

Drop any `.mp3`, `.wav`, `.m4a`, or `.aac` file into this folder, then either:

1. Rename it to `topcoder-bed.m4a` to use it as the default; **or**
2. Reference it explicitly via `render_options.music_path` per call.

The renderer loops the track to fit the clip duration and applies sidechain ducking under the voice.
