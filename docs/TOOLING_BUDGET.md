# Tooling And Budget Report

Pricing references were checked on April 24, 2026.

Forum clarifications also matter here:

- participants should balance cost and quality
- expected processing volume is roughly `1k+`
- a 30-second render should probably cost below `$1`
- external APIs are allowed
- storage can be local or cloud
- reviewers expect roughly 2-3 test videos, each processed once
- 720p output is enough if quality is good
- rendered files should probably stay below 30 MB
- cloud hosting cost does not need to be included in the report

## Tool Choices

| Need | Selected Tool | Why |
| --- | --- | --- |
| Orchestration | FastAPI + container worker | Simple API surface, easy ECS/Fargate deployment, works locally for review |
| Rendering | FFmpeg | Lowest marginal cost, fast, deterministic, supports captions, audio filters, overlays, H.264/AAC MP4, 720p landscape output, and mobile/social encodes |
| Transcription | OpenAI `gpt-4o-transcribe-diarize` | Current official docs say this model returns speaker-aware segments with `start` and `end` metadata, which is better for synchronized captions |
| Storage | S3 | Native presigned upload pattern and durable asset hosting |
| Worker compute | ECS/Fargate | Scales per job without managing render hosts |
| Optional broadcast transcoding | AWS Elemental MediaConvert | Useful if Topcoder later needs full ABR/HLS packaging, but not needed for this 30-second MP4 profile asset |

## Per 30-Second Video Estimate

| Cost Item | Assumption | Estimated Cost |
| --- | --- | ---: |
| OpenAI transcription | 0.5 min x `$0.006/min` | `$0.0030` |
| Fargate worker | 2 vCPU / 4 GB for 60 seconds, US East Linux/x86 rates | `$0.0016` |
| S3 requests and short-term storage | raw input, two MP4 outputs, manifest | `< $0.0001` |
| FFmpeg rendering license/API cost | self-hosted open-source worker | `$0.0000` |
| Total direct variable cost | excludes NAT/ALB/logging fixed costs | about `$0.0047` |

At this design point, the answer is much closer to `$0.05` than `$5.00`; the variable cost is under one cent per 30-second profile before fixed infrastructure overhead, and comfortably below the forum's “probably below `$1`” guidance.

The recurring hosting bill is intentionally excluded because the forum confirmed cloud hosting expenditure does not need to be included. The estimate focuses on direct per-render usage. At the clarified review load of roughly 2-3 videos processed once each, the expected direct variable verification cost remains well under one cent.

## Latency Estimate

| Stage | Expected Latency |
| --- | ---: |
| Upload to S3 | 1-5 seconds depending on network |
| Transcription | 1-4 seconds for 30 seconds of audio |
| Audio cleanup + ducking | 2-5 seconds |
| Two FFmpeg renders | 15-45 seconds on a 2 vCPU worker |
| Total | roughly 25-60 seconds |

For near-real-time UX, return a job ID immediately and update the profile when the manifest is ready. For the clarified expected scale of roughly `1k+` renders, split landscape and vertical renders into parallel worker tasks and keep the worker tier stateless.

## Official Pricing Sources

- OpenAI pricing page lists `gpt-4o-mini-transcribe` at an estimated `$0.003 / minute`, and both `gpt-4o-transcribe` and `gpt-4o-transcribe-diarize` at about `$0.006 / minute`.
- AWS Fargate pricing explains per-second billing and gives US East Linux/x86 rates of `$0.000011244` per vCPU-second and `$0.000001235` per GB-second.
- AWS S3 pricing states there is no minimum charge and request/storage costs are usage-based.
- AWS Elemental MediaConvert Professional tier examples show `$0.0120` per normalized minute for the first 50,000 normalized minutes in US West, before additional S3 or transfer charges.

## Scale Notes

- For the forum's likely near-term scale of roughly `1k+` renders, the direct variable processing cost is only a few dollars.
- For 1.5M members at one render each, direct variable processing at about `$0.0047` is roughly `$7,050`, plus storage, egress, logs, orchestration, retries, and support overhead.
- Re-rendering for template changes is feasible, but should be event-driven and rate-limited.
- The largest cost risk is not AI transcription; it is fixed cloud networking, video egress, and repeated renders.
