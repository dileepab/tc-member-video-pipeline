# Submission Freeze Checklist

## Code And Behavior

- [x] Latest code changes are complete
- [x] README matches actual behavior
- [x] Known AI or service failure paths report truthfully in docs/manifests
- [x] Deterministic fallback behavior is documented
- [x] Latest forum clarifications are reflected in code or docs
- [x] Actual public deployed URL is live: `https://topcoder-profile-video-pipeline.onrender.com` (root/health/docs verified 2026-04-26; full render available locally per docs/DEPLOYMENT.md because the free tier may OOM on FFmpeg renders)

## Tests

- [x] `pytest` — 23/23 passing on Python 3.14.3
- [x] `python scripts/run_demo.py` (run with OPENAI_API_KEY for the live AI path; manifest at `submission-evidence/raw/openai-run-manifest.json` confirms `transcription: openai-gpt-4o-transcribe-diarize` and `music: bundled-eliveta-technology-pixabay-content-license`)
- [x] `python scripts/create_before_after_demo.py`
- [x] Walkthrough video: real screen recording at https://drive.google.com/file/d/1bL3winhCKszunqS0fq0QmXNUKLGIqGOx/view?usp=sharing (the legacy slide-only `scripts/create_demo_video.py` artifact is intentionally excluded from the final ZIP)
- [x] Targeted grep for `TODO|FIXME|eslint-disable` — clean

## Evidence

- [x] Required demo video artifacts are captured from latest build
- [x] Raw logs are saved
- [x] Evidence index is updated

## Patch Packaging

- [x] Final ZIP can be extracted and still run install/build/demo flow (verified: `demo-output/before_raw_intro.mp4` and `demo-output/Profile_Intro_Video_Generated.mp4` are committed so reviewer flow runs without `scripts/generate_sample.py`; `pyproject.toml` and `pip install -e ".[dev]"` reproduce the env)
- [x] No secrets or local `.env` files are included
- [x] No stale screenshots or stale zips remain

## Final Sanity Check

- [x] Requirements matrix shows all scored requirements as covered (R15 closed: live URL `https://topcoder-profile-video-pipeline.onrender.com` verified for index/health/docs; full FFmpeg render runs locally because Render free tier may OOM)
- [x] Reviewer-risk log has been reviewed one last time
