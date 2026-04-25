# Submission Evidence

This folder collects reviewer-facing evidence generated from the current build.

## Layout

- `raw/tests.log` - full pytest output
- `raw/tests-summary.txt` - short test summary
- `raw/demo-run.json` - output from `python scripts/run_demo.py`
- `raw/api-job-response.json` - response from `POST /jobs`
- `raw/api-job-final.json` - final status from `GET /jobs/{job_id}`
- `raw/deployment-smoke.txt` - hosted-style API smoke test evidence
- `raw/before-after-demo.txt` - notes about the generated Topcoder Star before/after video
- `raw/demo-video.txt` - notes about the generated walkthrough video artifact
- `raw/real-sample-run.json` - optional run summary using the provided real sample clip

## Primary Artifacts

- `demo-output/before_raw_intro.mp4`
- `demo-output/after/profile_landscape.mp4`
- `demo-output/after/profile_vertical.mp4`
- `demo-output/after/captions.srt`
- `demo-output/after/manifest.json`
- `demo-output/topcoder_star_before_after.mp4`
- `demo-output/run_app_demo.mp4`
- `demo-output/real-sample-after/profile_landscape.mp4`
