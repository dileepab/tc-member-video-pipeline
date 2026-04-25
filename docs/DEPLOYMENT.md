# Deployment

## Container

Build:

```bash
docker build -t topcoder-profile-video-pipeline .
```

Run:

```bash
docker run --rm -p 8000:8000 topcoder-profile-video-pipeline
```

Smoke-check the API:

```bash
curl http://127.0.0.1:8000/health
```

Expected:

```json
{"status":"ok"}
```

The forum confirmed the deployment platform does not affect scoring as long as the reviewer can use it. This container can run on Render, Fly.io, ECS/Fargate, a VM, or a local reviewer machine.

## Render Blueprint

This repo includes `render.yaml` for a one-service Docker deployment. The container honors Render's `PORT` environment variable and exposes:

- `GET /health` for readiness checks
- `POST /jobs` for URI-based render jobs
- `POST /render` for multipart upload render jobs
- `GET /outputs/{job_id}/{filename}` for downloading rendered MP4/caption artifacts
- `/docs` for FastAPI's built-in OpenAPI UI

Recommended Render setup:

1. Push this repo to GitHub.
2. In Render, create a new Blueprint from the repo.
3. Use `render.yaml` as-is.
4. Add `OPENAI_API_KEY` only if you want live OpenAI captions; otherwise the deterministic caption fallback is expected.
5. Open the deployed root URL and confirm it returns the API index.
6. Open `/docs` and use `POST /render` with a 15-30 second English MP4 and `samples/member_metadata.json`.

After deployment, run:

```bash
.venv/bin/python scripts/smoke_deployment.py https://YOUR-SERVICE.onrender.com --skip-render
```

For a full render smoke test, first ensure `demo-output/before_raw_intro.mp4` exists:

```bash
.venv/bin/python scripts/generate_sample.py
.venv/bin/python scripts/smoke_deployment.py https://YOUR-SERVICE.onrender.com
```

The full smoke test uploads a sample clip to `POST /render`, polls `GET /jobs/{job_id}`, and downloads the returned landscape MP4 from `/outputs/...`.

Free tiers may be too memory- or CPU-constrained for FFmpeg render jobs. If a hosted free-tier job times out, the same Docker image can still be reviewed locally with the commands above, which matches the forum clarification that deployment platform choice does not affect scoring as long as the reviewer can use the app.

## AWS Reference Deployment

Recommended services:

- S3 bucket for raw uploads and final rendered assets.
- API Gateway or ALB in front of the FastAPI service.
- ECS/Fargate service for API plus separate on-demand worker tasks.
- SQS for render requests.
- DynamoDB for job status.
- CloudWatch for structured logs and render timing metrics.

## Environment

Set:

```bash
OPENAI_API_KEY=...
OPENAI_TRANSCRIBE_MODEL=gpt-4o-transcribe-diarize
AWS_REGION=us-east-1
TOPCODER_RENDER_WORKDIR=/tmp/work
TOPCODER_OUTPUT_DIR=/tmp/outputs
```

For production, prefer IAM task roles over static AWS keys.

## Manual Testing via Swagger UI

The deployed app ships a full interactive API explorer at `/docs`. Reviewers can test the pipeline end-to-end without any CLI tools:

1. Open **`https://topcoder-profile-video-pipeline.onrender.com/docs`**
2. Click **`POST /render`** → **"Try it out"**
3. Under `video`, click **"Choose File"** and upload a 15-30 second English MP4 clip (use `demo-output/before_raw_intro.mp4` from the repo if needed)
4. Under `metadata_json`, paste:
   ```json
   {
     "handle": "dileepa",
     "rating": 1500,
     "rating_color": "yellow",
     "top_track": "dev",
     "skills": ["Python", "AI", "FastAPI"]
   }
   ```
5. Leave `render_options_json` as `{}` for both landscape and vertical, or use `{"aspect":"landscape"}` for a faster single-output smoke test
6. Click **"Execute"** — returns a `job_id` instantly
7. Click **`GET /jobs/{job_id}`** → **"Try it out"**, enter the `job_id`, click **"Execute"**
8. Poll until `"status": "succeeded"` — `result.download_urls` includes the downloadable MP4/caption paths
9. Open the output URL directly in your browser. Prefix the relative path returned in `download_urls.outputs.landscape` with the deployment origin:
   ```
   https://topcoder-profile-video-pipeline.onrender.com/outputs/{job_id}/profile_landscape.mp4
   ```
   Or download via curl:
   ```bash
   curl https://topcoder-profile-video-pipeline.onrender.com/outputs/{job_id}/profile_landscape.mp4 -o output.mp4
   ```
   When running locally instead, use `http://127.0.0.1:8000` as the origin.

The same works for `profile_vertical.mp4`, `captions.srt`, and `manifest.json`.

> **Note:** Free-tier Render instances have 512 MB RAM. If the render job returns a 502, run the same test locally using the Docker container or `uvicorn` as described above — the forum confirmed deployment platform does not affect scoring.

## Review Note

The deployed URL is **`https://topcoder-profile-video-pipeline.onrender.com`**.

- `GET /health` → `{"status":"ok"}` confirms the service is running
- `GET /docs` → interactive Swagger UI for manual testing
- Full video rendering may exceed free-tier memory limits; use the local Docker path for full pipeline verification if needed
