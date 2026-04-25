# Demo

## Local Before/After Demo

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
.venv/bin/python scripts/run_demo.py
```

Expected outputs:

- `demo-output/after/profile_landscape.mp4`
- `demo-output/after/profile_vertical.mp4`
- `demo-output/after/captions.srt`
- `demo-output/after/manifest.json`

By default, `scripts/run_demo.py` prefers the bundled 29-second sample clip `demo-output/Profile_Intro_Video_Generated.mp4`. If that file is absent, it generates `demo-output/before_raw_intro.mp4` as a reproducible 18-second fallback reviewer input. Custom inputs must be 15-30 seconds long.

To re-render with a custom input clip and output path:

```bash
.venv/bin/python scripts/run_demo.py \
  --input path/to/your-clip.mp4 \
  --output-dir demo-output/custom-after \
  --work-dir demo-output/custom-work
```

## API Demo

First create the reproducible sample raw clip:

```bash
.venv/bin/python scripts/generate_sample.py
```

Start the API:

```bash
uvicorn app.main:app --reload
```

Submit the job:

```bash
curl -X POST http://127.0.0.1:8000/jobs \
  -H "Content-Type: application/json" \
  -d @samples/job_local.json
```

Poll the returned status URL until `status` is `succeeded`.

To test the API with the optional real sample clip instead, submit `samples/job_real_sample.json`.

## Demo Video Artifact

Generate the required Topcoder Star before/after showcase video:

```bash
.venv/bin/python scripts/create_before_after_demo.py
```

That writes `demo-output/topcoder_star_before_after.mp4`, with the raw clip and polished profile intro shown side by side.

The "how to run the app" walkthrough is a real screen recording, hosted at:
**https://drive.google.com/file/d/1bL3winhCKszunqS0fq0QmXNUKLGIqGOx/view?usp=sharing**

Recording instructions are in [WALKTHROUGH_RECORDING.md](WALKTHROUGH_RECORDING.md) if a fresh take is ever needed.

## How To Check The Implementation

1. Run the tests.

```bash
.venv/bin/python -m pytest
```

You should see all tests pass.

2. Run the reproducible local demo.

```bash
.venv/bin/python scripts/run_demo.py
```

Check that these files exist:

- `demo-output/after/profile_landscape.mp4`
- `demo-output/after/profile_vertical.mp4`
- `demo-output/after/captions.srt`
- `demo-output/after/manifest.json`
- `demo-output/topcoder_star_before_after.mp4`

3. Verify the output dimensions.

```bash
ffprobe -v error -select_streams v:0 -show_entries stream=width,height,duration -of csv=p=0 demo-output/after/profile_landscape.mp4
ffprobe -v error -select_streams v:0 -show_entries stream=width,height,duration -of csv=p=0 demo-output/after/profile_vertical.mp4
```

Expected:

- `1280,720,<input_duration>` for landscape
- `1080,1920,<input_duration>` for vertical

The bundled sample currently renders to `29.000000` seconds. The generated fallback sample renders to `18.000000` seconds.

4. Verify the output sizes.

```bash
du -h demo-output/after/profile_landscape.mp4 demo-output/after/profile_vertical.mp4
```

Each rendered MP4 should be below 30 MB. The run also fails early if the source clip is outside the clarified 15-30 second video-length window.

5. Verify the AI/non-AI path from the manifest.

```bash
cat demo-output/after/manifest.json
```

Check `adapters.transcription`:

- `fallback-scripted` means offline reviewer mode
- `openai-gpt-4o-transcribe-diarize` means the default timestamped OpenAI transcription path was used
- `output_file_sizes_bytes` records the size of each rendered MP4

If OpenAI returns a billing/quota error such as `insufficient_quota`, the run should still complete and `manifest.json` should include a warning plus `adapters.transcription_requested`.

6. Verify the API job flow.

```bash
python scripts/generate_sample.py
.venv/bin/uvicorn app.main:app --port 8001
curl -X POST http://127.0.0.1:8001/jobs \
  -H "Content-Type: application/json" \
  -d @samples/job_local.json
curl http://127.0.0.1:8001/jobs/<job_id>
```

The implementation is working when the final job response shows `status` as `succeeded`.

7. Visually verify the branding layer.

- The top-left Topcoder wordmark is visible without a white background box.
- The lower-third shows the member handle, the rating badge color, a per-track icon badge, the track label, and the skills line.
- Captions sit above the lower-third instead of covering it.

## Review Notes

The documented reviewer path is intentionally reproducible from a clean checkout by using the bundled 29-second sample clip when available and the generated 18-second fallback otherwise. Production runs use the exact same render path with an uploaded user video and optional licensed music file.
