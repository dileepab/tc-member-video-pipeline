# Submission Evidence

This folder collects reviewer-facing evidence generated from the current build.

## Layout

- `raw/tests.log` - full pytest output
- `raw/tests-summary.txt` - short test summary
- `raw/demo-run.json` - output from `python scripts/run_demo.py`
- `raw/api-job-response.json` - response from `POST /jobs`
- `raw/api-job-final.json` - final status from `GET /jobs/{job_id}`
- `raw/deployment-smoke.txt` - hosted-style API smoke test evidence (local Docker image, full upload/render/download)
- `raw/deployment-smoke-live.txt` - live deployed URL smoke test (`https://topcoder-profile-video-pipeline.onrender.com`, root/health/docs)
- `raw/openai-run-manifest.json` - manifest from a real OpenAI `gpt-4o-transcribe-diarize` run (synced captions, no fallback)
- `raw/openai-run-captions.srt` - SRT captions actually transcribed by OpenAI from the bundled sample clip
- `raw/before-after-demo.txt` - notes about the generated Topcoder Star before/after video

## Primary Artifacts

- `demo-output/before_raw_intro.mp4`
- `demo-output/after/profile_landscape.mp4`
- `demo-output/after/profile_vertical.mp4`
- `demo-output/after/captions.srt`
- `demo-output/after/manifest.json`
- `demo-output/topcoder_star_before_after.mp4`
- Walkthrough video (Google Drive): https://drive.google.com/file/d/1bL3winhCKszunqS0fq0QmXNUKLGIqGOx/view?usp=sharing
