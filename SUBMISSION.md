# Submission Notes

This file captures the bits a reviewer needs that don't belong in source code: deployed URL, API key handover plan, and how to verify the package end-to-end.

## Deployed URL

- Live: **`https://topcoder-profile-video-pipeline.onrender.com`**
- Verified endpoints: `/`, `/health`, `/docs`
- Evidence: [submission-evidence/raw/deployment-smoke-live.txt](submission-evidence/raw/deployment-smoke-live.txt)

## Walkthrough Video

- **Demo Video (how to run the app):** [https://drive.google.com/file/d/1bL3winhCKszunqS0fq0QmXNUKLGIqGOx/view?usp=sharing](https://drive.google.com/file/d/1bL3winhCKszunqS0fq0QmXNUKLGIqGOx/view?usp=sharing)
- **Topcoder Star Before/After demo:** [demo-output/topcoder_star_before_after.mp4](demo-output/topcoder_star_before_after.mp4)
- **Bundled rendered samples:** [demo-output/after/profile_landscape.mp4](demo-output/after/profile_landscape.mp4) (16:9 desktop), [demo-output/after/profile_vertical.mp4](demo-output/after/profile_vertical.mp4) (9:16 mobile)
- **Recording script used to make the walkthrough:** [docs/WALKTHROUGH_RECORDING.md](docs/WALKTHROUGH_RECORDING.md)

> Render free tier (512 MB) may OOM on a full FFmpeg render. For full pipeline verification, please run locally via Docker or `uvicorn` per [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md). The forum confirmed the deployment platform choice does not affect scoring as long as the reviewer can use the app.

## OpenAI API Key Handover

Forum confirmation (Standlove, 2026-04-25): *"please provide clear instructions and api keys"* when the reviewer cannot run on the deployed free tier.

The OpenAI key authorized for review is delivered through the **Topcoder challenge submission notes** (the form text field that accompanies this ZIP). The actual key value is *not* committed to this Git repository — GitHub's secret-scanning push protection blocks live keys, and OpenAI's secret-scanning partner program may auto-revoke any key it sees in a public commit. The key lives in the submission notes only; the rest of the package, including the SUBMISSION.md inside the offline ZIP for reviewer convenience, references it as a placeholder.

Reviewer flow:

1. Copy the key from the Topcoder submission notes.
2. Export it in your shell:
   ```bash
   export OPENAI_API_KEY=sk-proj-...
   ```
3. Run the demo or start the API per the [Reviewer Setup section in the README](README.md#reviewer-setup).
4. The pipeline auto-selects `gpt-4o-transcribe-diarize` (timestamped/diarized captions). Without the key, it transparently falls back to deterministic scripted captions and records a warning in `manifest.json`.

**Authorized usage budget:** the forum scoped review to roughly 2-3 videos × 1 run each. At `gpt-4o-transcribe-diarize` pricing (`$0.006/min`) this is well under `$0.05` total — the supplied key has more than enough headroom for that scope.

**Pre-recorded evidence (no key needed to verify):** the OpenAI path was already exercised end-to-end and saved to:
- [submission-evidence/raw/openai-run-manifest.json](submission-evidence/raw/openai-run-manifest.json) — shows `transcription: openai-gpt-4o-transcribe-diarize`, no warnings
- [submission-evidence/raw/openai-run-captions.srt](submission-evidence/raw/openai-run-captions.srt) — actual synced captions transcribed from the bundled clip

If the key has been rotated or rate-limited by the time review starts, please ping the submitter through the challenge messaging channel for a refreshed key — the budget impact of one re-run is negligible. The submitter intends to rotate this key after the review window closes.

## Recommended Reviewer Path

1. **Quick liveness check** (no setup): visit `https://topcoder-profile-video-pipeline.onrender.com/docs` to confirm the API is up.
2. **Full pipeline verification** (recommended):
   ```bash
   git clone <repo>
   cd <repo>
   python3 -m venv .venv && source .venv/bin/activate
   pip install -e ".[dev]"
   export OPENAI_API_KEY=sk-...   # from submission notes
   .venv/bin/python scripts/run_demo.py
   ```
   Outputs land in `demo-output/after/` — see [docs/DEMO.md](docs/DEMO.md) for the full check list.
3. **Try your own clip via Swagger UI**: see [README.md → Reviewer Setup](README.md#reviewer-setup).

## Bundled Music

The default music bed is a real licensed track:

> "Technology" by **eliveta** — Pixabay Content License (free for commercial use, **no attribution required**)
> Source: [https://pixabay.com/music/upbeat-technology-474054/](https://pixabay.com/music/upbeat-technology-474054/)
> File: [assets/music/topcoder-bed.m4a](assets/music/topcoder-bed.m4a) (45 s stereo AAC, ~540 KB)
> Full credits + license details: [assets/music/CREDITS.md](assets/music/CREDITS.md)

The pipeline records which track ran in `manifest.json` under `adapters.music`. The bundled file is automatically picked up by `app/pipeline.py` when `render_options.music_path` is not supplied; production callers can override it with their own licensed track, and `app/audio.generate_music_bed` is kept as a no-asset FFmpeg fallback.

## Submission Package Contents

- Source: `app/`, `tests/`, `scripts/`, `samples/`, `assets/`
- Docs: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), [docs/TOOLING_BUDGET.md](docs/TOOLING_BUDGET.md), [docs/DEMO.md](docs/DEMO.md), [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
- Demo artifacts (in repo): [demo-output/topcoder_star_before_after.mp4](demo-output/topcoder_star_before_after.mp4), [demo-output/after/profile_landscape.mp4](demo-output/after/profile_landscape.mp4), [demo-output/after/profile_vertical.mp4](demo-output/after/profile_vertical.mp4)
- Demo walkthrough video (Google Drive): [https://drive.google.com/file/d/1bL3winhCKszunqS0fq0QmXNUKLGIqGOx/view?usp=sharing](https://drive.google.com/file/d/1bL3winhCKszunqS0fq0QmXNUKLGIqGOx/view?usp=sharing)
- Traceability: [challenge-notes/](challenge-notes/)
- Evidence: [submission-evidence/](submission-evidence/)

## What This Submission Already Verified

- 23/23 unit/API tests pass on Python 3.14 ([submission-evidence/raw/tests.log](submission-evidence/raw/tests.log))
- Local end-to-end render produced 1280×720 / 1080×1920 H.264 MP4s, both under 30 MB ([submission-evidence/raw/output-probe.txt](submission-evidence/raw/output-probe.txt))
- Local upload-render-download path against the same Docker image ([submission-evidence/raw/deployment-smoke.txt](submission-evidence/raw/deployment-smoke.txt))
- Live deployed root/health/docs ([submission-evidence/raw/deployment-smoke-live.txt](submission-evidence/raw/deployment-smoke-live.txt))
- Direct variable cost per 30-second profile estimated at `$0.0047` — well below the forum-confirmed `$1` target ([docs/TOOLING_BUDGET.md](docs/TOOLING_BUDGET.md))
