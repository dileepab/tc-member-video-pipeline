# Music Credits

## Bundled Background Music

The default music bed `topcoder-bed.m4a` is a derivative excerpt of:

- **Title:** "Technology" (Pixabay track ID 474054)
- **Artist:** eliveta
- **Source:** [https://pixabay.com/music/upbeat-technology-474054/](https://pixabay.com/music/upbeat-technology-474054/)
- **License:** [Pixabay Content License](https://pixabay.com/service/license-summary/) — free for commercial use, **no attribution required**.
- **Modifications:** trimmed to 45 seconds (start = 8 s of source), fade-in (0.5 s) and fade-out (1.5 s) applied, loudness normalized to -20 LUFS, encoded to stereo AAC at 96 kbps.

## Attribution

The Pixabay Content License does **not** require attribution for use in this pipeline or in rendered profile videos. A courtesy credit is welcome but not legally required. Suggested optional credit:

> Background music: "Technology" by eliveta — Pixabay.

## Synthetic Fallback

When `assets/music/topcoder-bed.m4a` is absent (e.g., stripped from a packaged ZIP), `app/audio.generate_music_bed` synthesizes a quiet bed with FFmpeg `lavfi` (no licensing required). The fallback is intentionally minimal — replace it with a real track for production use.

## Replacing The Default

To swap the bundled bed for a different track:

1. Drop the new file into `assets/music/`.
2. Convert and rename it to `topcoder-bed.m4a`:
   ```bash
   ffmpeg -y -i path/to/your-track.mp3 \
     -ss 0 -t 45 \
     -af "afade=t=in:st=0:d=0.5,afade=t=out:st=43.5:d=1.5,loudnorm=I=-20:TP=-1.5:LRA=11" \
     -c:a aac -b:a 96k -ac 2 -ar 48000 \
     assets/music/topcoder-bed.m4a
   ```
3. Update this `CREDITS.md` with the new track's title, artist, source URL, and license.
4. Update the adapter string in [app/pipeline.py](../../app/pipeline.py) (search for `music_source = "bundled-...`) so the rendered manifest reports the correct track.
