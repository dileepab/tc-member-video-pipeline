# AI-Powered Topcoder Member Profile Video Pipeline

This repository is a proof-of-concept pipeline for turning a raw 15-30 second Topcoder member intro clip into a branded, captioned, audio-leveled profile video.

The PoC is designed to be reviewer-friendly:

- It runs locally with FFmpeg and no paid API keys.
- It supports cloud-native orchestration through FastAPI plus local or S3 URIs.
- It has optional OpenAI transcription for production-quality captions.
- It renders H.264/AAC MP4 desktop (`1280x720`) and mobile/social (`1080x1920`) outputs from the same branding template.
- It enforces the clarified 15-30 second input window and checks each rendered MP4 stays below 30 MB.
- It includes Docker and Render blueprint deployment paths for API-only review.
- The default brand theme now uses public Topcoder logo/icon assets plus colors observed on `https://www.topcoder.com/` on April 24, 2026.

## Stack

- **Backend API:** Python 3.11+ / FastAPI
- **Video rendering:** FFmpeg filter graphs with libx264, libass captions, official Topcoder PNG/SVG-derived overlays, and dynamic drawtext layers
- **Audio cleanup:** FFmpeg `afftdn`, high/low pass filters, `loudnorm`, and sidechain music ducking
- **Captions:** OpenAI `gpt-4o-transcribe-diarize` by default for synchronized caption segments when `OPENAI_API_KEY` is present; deterministic fallback captions for offline demos
- **Storage:** Local filesystem and optional AWS S3 via `boto3`
- **Deployment target:** Containerized ECS/Fargate worker or any Docker host with FFmpeg

## Where AI Fits

AI is used for the **transcription and caption intelligence** part of the pipeline, not for the full video edit.

- The worker first extracts and cleans the voice track with FFmpeg.
- `app/transcription.py` then chooses the caption provider.
- If `OPENAI_API_KEY` is present, the pipeline sends the cleaned audio to OpenAI. The default model is `gpt-4o-transcribe-diarize` because it returns timestamped segments for synchronized captions.
- The returned timed transcript segments are converted into `captions.srt` and styled `captions.ass`.
- FFmpeg then renders the final branded video using deterministic overlays, intro/outro motion, music ducking, and aspect-ratio exports.

That means the current PoC splits responsibilities like this:

- **AI-driven:** speech-to-text and synchronized caption generation
- **Deterministic post-production:** audio cleanup, background blur/focus, branding, track icons, rating color, intro/outro, music mix, and final render

If no API key is configured, the app still runs end to end by falling back to metadata-driven scripted captions for reviewer-safe local verification.

If an OpenAI key is configured but the account has no available quota or billing, the pipeline now falls back to scripted captions and records a warning in `manifest.json` instead of crashing.

## Reviewer Setup

> The deployed URL at `https://topcoder-profile-video-pipeline.onrender.com` may be slow or unavailable on the free tier. Local setup is fully supported per forum confirmation — please use the steps below.

**Prerequisites:** Python 3.11+, FFmpeg

```bash
# 1. Clone and install
git clone https://github.com/dileepab/tc-member-video-pipeline.git
cd tc-member-video-pipeline
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# 2. Add the OpenAI API key (provided separately in the submission notes)
export OPENAI_API_KEY=sk-...

# 3. Start the API server
uvicorn app.main:app --reload
```

### Test with your own video via Swagger UI

1. Open **`http://127.0.0.1:8000/docs`** in your browser
2. Click **`POST /render`** → **"Try it out"**
3. Under `file`, click **"Choose File"** and upload a 15–30 second MP4 clip
4. Under `metadata_json`, paste:
   ```json
   {"handle": "your_handle", "rating": 1500, "rating_color": "yellow", "tracks": ["dev"], "skills": ["Python", "AI", "FastAPI"]}
   ```
5. Click **"Execute"** — returns a `job_id` instantly
6. Click **`GET /jobs/{job_id}`** → **"Try it out"**, enter the `job_id`, click **"Execute"**
7. Poll until `"status": "succeeded"`
8. Click **`GET /outputs/{job_id}/{filename}`** → **"Try it out"**
9. Enter the `job_id` and `profile_landscape.mp4` as the filename → **"Execute"** to download the rendered video

The same works for `profile_vertical.mp4`, `captions.srt`, and `manifest.json`.

### Run the pre-built demo instead

```bash
.venv/bin/python scripts/run_demo.py
```

Output videos will be written to `demo-output/after/`. See `demo-output/topcoder_star_before_after.mp4` for the before/after showcase and `demo-output/run_app_demo.mp4` for a walkthrough.

---

## Quick Start

Install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Confirm FFmpeg is available:

```bash
ffmpeg -version
```

Run the end-to-end demo:

```bash
.venv/bin/python scripts/run_demo.py
```

That default command uses the bundled 29-second sample clip `demo-output/Profile_Intro_Video_Generated.mp4` when it is present and falls back to a reproducible 18-second generated clip otherwise. Any custom input must be 15-30 seconds long.

To test with a real sample clip instead:

```bash
.venv/bin/python scripts/run_demo.py \
  --input demo-output/Profile_Intro_Video_Generated.mp4 \
  --output-dir demo-output/real-sample-after \
  --work-dir demo-output/real-sample-work
```

Run the API:

```bash
uvicorn app.main:app --reload
```

Open:

- `http://127.0.0.1:8000/` for the API index
- `http://127.0.0.1:8000/docs` for FastAPI's OpenAPI UI
- `http://127.0.0.1:8000/health` for deployment health checks

Create the required before/after Topcoder Star showcase video:

```bash
.venv/bin/python scripts/create_before_after_demo.py
```

Create the run-app walkthrough video:

```bash
.venv/bin/python scripts/create_demo_video.py
```

Submit a local render job:

```bash
curl -X POST http://127.0.0.1:8000/jobs \
  -H "Content-Type: application/json" \
  -d @samples/job_local.json
```

For deployed review, `POST /render` returns `download_urls` for rendered files under `/outputs/...`.

## Environment

Copy `.env.example` if you want cloud-backed transcription or S3 IO.

```bash
cp .env.example .env
```

No environment variables are required for the local demo.

## Verification

Run the core checks:

```bash
.venv/bin/python -m pytest
.venv/bin/python scripts/run_demo.py
.venv/bin/python scripts/create_before_after_demo.py
.venv/bin/python scripts/create_demo_video.py
```

Check the rendered output dimensions:

```bash
ffprobe -v error -select_streams v:0 -show_entries stream=width,height,duration -of csv=p=0 demo-output/after/profile_landscape.mp4
ffprobe -v error -select_streams v:0 -show_entries stream=width,height,duration -of csv=p=0 demo-output/after/profile_vertical.mp4
```

Expected:

- `1280,720,<input_duration>` for landscape
- `1080,1920,<input_duration>` for vertical

The bundled sample clip currently renders to `29.000000` seconds. The generated fallback sample renders to `18.000000` seconds.

Check rendered file sizes:

```bash
du -h demo-output/after/profile_landscape.mp4 demo-output/after/profile_vertical.mp4
```

Each rendered MP4 should be below the forum-confirmed 30 MB target. The manifest also records `output_file_sizes_bytes`.

Check which caption provider ran:

```bash
cat demo-output/after/manifest.json
```

Look for:

- `"transcription": "fallback-scripted"` for offline verification
- `"transcription": "openai-gpt-4o-transcribe-diarize"` when the default synced-caption OpenAI path is used

If OpenAI billing/quota is unavailable, `manifest.json` will show:

- `"transcription": "fallback-scripted"`
- `"transcription_requested": "openai-gpt-4o-transcribe-diarize"`
- a warning message explaining the fallback reason

To verify the API path:

```bash
python scripts/generate_sample.py
.venv/bin/uvicorn app.main:app --port 8001
curl -X POST http://127.0.0.1:8001/jobs \
  -H "Content-Type: application/json" \
  -d @samples/job_local.json
curl http://127.0.0.1:8001/jobs/<job_id>
```

The implementation is behaving correctly when:

- tests pass
- landscape and vertical videos are generated
- each rendered MP4 is below 30 MB
- captions files exist
- `manifest.json` includes timings, outputs, and adapter names
- the `/jobs` endpoint reaches `status: "succeeded"`
- the rendered lower-third shows the member handle, rating color, track icon, track label, and skills without overlapping captions

## Deliverables

- Architecture: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- Tooling and budget report: [docs/TOOLING_BUDGET.md](docs/TOOLING_BUDGET.md)
- Demo instructions: [docs/DEMO.md](docs/DEMO.md)
- Deployment notes: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
- Challenge traceability notes: [challenge-notes/](challenge-notes/)

## Output

Each completed job writes:

- `profile_landscape.mp4`
- `profile_vertical.mp4`
- `captions.srt`
- `captions.ass`
- `manifest.json`

The demo scripts also write:

- `demo-output/topcoder_star_before_after.mp4`
- `demo-output/run_app_demo.mp4`

The manifest includes render timings, selected adapters, output paths, per-output file sizes, and an estimated per-profile cost.
