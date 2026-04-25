# Verification Evidence Plan

| Requirement | What Must Be Shown | Source Command / Action | Output File | Captured | Notes |
| --- | --- | --- | --- | --- | --- |
| Before clip | Raw generated 18-second input exists | `python scripts/generate_sample.py` | `demo-output/before_raw_intro.mp4` | Yes | Reproducible reviewer input. |
| After desktop render | Branded landscape output with overlays/captions/audio | `python scripts/run_demo.py` | `demo-output/after/profile_landscape.mp4` | Yes | Render completed locally from the bundled 29-second sample. |
| After mobile render | Branded vertical output | `python scripts/run_demo.py` | `demo-output/after/profile_vertical.mp4` | Yes | Render completed locally from the bundled 29-second sample. |
| Captions | SRT and ASS generated | `python scripts/run_demo.py` | `demo-output/after/captions.srt`, `captions.ass` | Yes | Offline fallback captions used because no API key was configured. |
| Tests | Unit/API smoke tests pass | `.venv/bin/python -m pytest` | `submission-evidence/raw/tests.log` | Yes | 23 tests passed on Python 3.14.3. |
| Forum output limits | Duration, dimensions, codec, and file sizes are within clarified limits | `ffprobe`, `du -h`, `manifest.json` | `demo-output/after/manifest.json` | Yes | 29-second H.264 MP4 outputs: 1280x720 at about 5 MB and 1080x1920 at about 7 MB. |
| API run | `/jobs` accepts local/S3-style job request | `.venv/bin/uvicorn app.main:app --port 8001` plus curl | `submission-evidence/raw/api-job-response.json`, `api-job-final.json` | Yes | Verified locally with generated sample source. |
| Deployment smoke | Hosted-style API root, health, docs, upload render, and output download work | `PORT=8013 ... uvicorn` plus `scripts/smoke_deployment.py http://127.0.0.1:8013` | `submission-evidence/raw/deployment-smoke.txt` | Yes | Verified root/docs/health, multipart upload render, and `/outputs/...` MP4 download locally. |
| Topcoder Star demo | Before/after transformation is shown in one reviewer-friendly video | `python scripts/create_before_after_demo.py` | `demo-output/topcoder_star_before_after.mp4` | Yes | Side-by-side raw clip and polished output. |
| Demo video | Walkthrough video showing how to run the app exists | `python scripts/create_demo_video.py` | `demo-output/run_app_demo.mp4` | Yes | Generated from the current build. |
| Optional real sample | Pipeline accepts the provided real sample clip | `python scripts/run_demo.py --input demo-output/Profile_Intro_Video_Generated.mp4 --output-dir demo-output/real-sample-after --work-dir demo-output/real-sample-work` | `submission-evidence/raw/real-sample-run.json` | Yes | Useful supplemental proof, not the primary reviewer path. |
