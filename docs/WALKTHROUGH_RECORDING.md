# Walkthrough Video — Recording Plan

The current deliverable is hosted at:
**https://drive.google.com/file/d/1bL3winhCKszunqS0fq0QmXNUKLGIqGOx/view?usp=sharing**

This file is kept in the repo as the script that produced it, in case a re-record is needed. It produces a 2-3 minute screen recording that proves the pipeline works end-to-end and shows the reviewer where each output lives.

The plan is intentionally tight: every second on screen earns a scoring point. Don't ad-lib — follow the cues.

## Target

- **Length:** 2:00–2:45 total
- **Hosting:** upload to Google Drive (or any reviewer-accessible link); update the URL in `README.md`, `SUBMISSION.md`, and the table in `challenge-notes/04-verification-evidence.md`
- **Resolution:** 1280×720 minimum (1920×1080 preferred)
- **Tooling:** any screen recorder (macOS QuickTime "New Screen Recording", OBS, Loom, ScreenStudio). Capture system audio if you can — the music bed is part of the demo.

## Pre-flight (run once, before recording)

```bash
# 1. Working directory: project root
cd "/Users/Dileepa/WebstormProjects/TC/AI-Powered Topcoder Member Profile Video Pipeline/.claude/worktrees/bold-chatterjee-0c6885"

# 2. Fresh venv + install (skip if already installed)
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# 3. Confirm FFmpeg is on PATH
ffmpeg -version | head -1

# 4. Export the OpenAI key (use the key from SUBMISSION.md)
export OPENAI_API_KEY=sk-...

# 5. Wipe the previous demo-output/after so the run is clean on camera
rm -rf demo-output/after
```

Now have these tabs/windows ready:
1. A terminal at the project root with the venv active.
2. A second terminal for the API curl (don't open it yet).
3. Browser at `http://127.0.0.1:8000/docs` — but don't navigate until step 5.
4. Finder/Explorer at `demo-output/` for showing output files.
5. The repo `README.md` open in your editor for one quick scroll.

## Shot list

Aim for ~15 seconds per step. Read the cue line aloud (one sentence, conversational). Don't read commands — let viewers see them.

### 0:00 — Title card (5 s)

- Show a fullscreen title slide or just the README's first line:
  > "AI-Powered Topcoder Member Profile Video Pipeline"
- Voiceover: *"This is a 30-second walkthrough of the Topcoder member profile intro pipeline."*

### 0:05 — Repo tour (15 s)

- Drag `demo-output/topcoder_star_before_after.mp4` into preview, play it muted with captions on.
- Voiceover: *"The pipeline turns a raw 15–30 second member clip into a branded, captioned, audio-leveled profile intro. Here's the before-and-after."*

### 0:20 — Architecture in one breath (10 s)

- Open `docs/ARCHITECTURE.md`, scroll the Mermaid diagram into view.
- Voiceover: *"It's a FastAPI service plus an FFmpeg worker. AI handles speech-to-text via OpenAI; everything else — branding, audio cleanup, music ducking, captions burn-in — is deterministic FFmpeg."*

### 0:30 — Run the demo from the CLI (35 s)

- Switch to terminal 1. Type, don't paste:
  ```bash
  python scripts/run_demo.py
  ```
- Show the live progress (probe → audio → captions → render).
- When it finishes, run:
  ```bash
  ls demo-output/after
  cat demo-output/after/manifest.json | head -30
  ```
- Voiceover (during the render): *"One command renders both 16:9 desktop and 9:16 mobile MP4s, plus SRT captions and a manifest."*
- Voiceover (showing manifest): *"Note the transcription adapter — OpenAI's `gpt-4o-transcribe-diarize` was used because the API key is set."*

### 1:05 — Open the rendered output (15 s)

- Open `demo-output/after/profile_landscape.mp4` in QuickTime / browser.
- Let it play 8–10 seconds with sound on so the music bed and ducking are audible.
- Skip to ~20 seconds in to show the lower-third (handle, rating color, track icon, skills).
- Voiceover: *"That's the desktop output — handle, red rating bar, Dev track icon, skills line, captions, and a music bed that ducks under the voice."*

### 1:20 — Mobile output (10 s)

- Quick swap to `demo-output/after/profile_vertical.mp4` — play 5 seconds.
- Voiceover: *"And here's the same render in 1080×1920 for mobile and social."*

### 1:30 — API path via Swagger UI (40 s)

- Switch to terminal 1, run:
  ```bash
  uvicorn app.main:app --reload
  ```
- Browser → `http://127.0.0.1:8000/docs`
- Click `POST /render` → "Try it out".
- For `video`, pick `demo-output/before_raw_intro.mp4` (or any 15–30 s clip).
- For `metadata_json`, paste:
  ```json
  {"handle":"dileepa","rating":1500,"rating_color":"yellow","top_track":"dev","skills":["Python","AI","FastAPI"]}
  ```
- Click Execute. Copy the returned `job_id`.
- Click `GET /jobs/{job_id}` → enter the id → Execute.
- Re-execute until `"status": "succeeded"`.
- Click the path under `result.download_urls.outputs.landscape` (or paste it after the origin in a new tab).
- Voiceover: *"Same pipeline through the upload API. POST a video plus metadata, poll the job, download the rendered MP4 from the returned URL. The deployed URL works the same way."*

### 2:10 — Deployed URL + cost (15 s)

- Browser → `https://topcoder-profile-video-pipeline.onrender.com/docs`
- Show that the API is live.
- Voiceover: *"This is the live deployment. The full render runs locally because Render's free tier has 512 MB; that's documented in `docs/DEPLOYMENT.md`."*
- Cut to `docs/TOOLING_BUDGET.md` table — highlight the `$0.0047` per 30 s figure.
- Voiceover: *"Direct variable cost is under half a cent per profile, well below the forum's $1 target."*

### 2:25 — Wrap (5 s)

- Cut to `SUBMISSION.md`.
- Voiceover: *"Source, evidence, and review notes are in this repo. Thanks for watching."*

## After Recording

```bash
# Trim and convert if needed
ffmpeg -i path/to/recording.mov -c:v libx264 -preset slow -crf 23 \
  -c:a aac -b:a 192k -movflags +faststart \
  -vf "scale='min(1920,iw)':-2" \
  walkthrough.mp4

# Sanity check size and duration
du -h walkthrough.mp4
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 \
  walkthrough.mp4
```

Target: under 60 MB, between 2:00 and 2:45.

Upload to Google Drive (or any reviewer-accessible link), set sharing to "Anyone with the link → Viewer", and update the URL in:

- `README.md` (Reviewer Setup section)
- `SUBMISSION.md` (Walkthrough Video section)
- `challenge-notes/04-verification-evidence.md` (Demo video row)
- `challenge-notes/05-submission-freeze-checklist.md` (Tests section)

## Common Pitfalls

- **Don't reveal the API key on screen.** Set it via `export` before starting the recording, or paste it from a clipboard manager that doesn't echo to the terminal. If the key flashes on screen, blur it in post.
- **Mute system notifications** before recording (Slack, Mail, calendar pings).
- **Close personal browser tabs** before sharing the screen.
- **Speak slowly.** 15 seconds feels short while you're recording; it's plenty for one sentence.
- **Use a wired connection or trusted Wi-Fi** so the live deployed URL doesn't stall on camera.
- **One take is fine** if it covers the shot list. Polish is nice but not scored.
