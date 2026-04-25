# Forum Deltas

| Date | Clarification | Impact | Status |
| --- | --- | --- | --- |
| 2026-04-23 | Balance cost and quality. | The solution should not optimize for maximum quality at any cost; it should present a business-aware tradeoff. | Applied |
| 2026-04-23 | Expected processing volume is maybe `1k+`. | Architecture should be cloud-scalable, but does not need to assume all 1.5M members render at once. | Applied |
| 2026-04-23 | Participants should create or generate raw videos if sample clips are not provided. | Generated reviewer-safe sample clips are allowed and should be documented clearly. | Applied |
| 2026-04-23 | Topcoder branding can be sourced from the Topcoder site. | Branding should stay aligned with Topcoder colors/visual language and should be easy to swap for official assets. | Applied |
| 2026-04-23 | External tools such as LLMs or APIs are allowed. | OpenAI transcription and other cloud APIs are valid implementation choices. | Applied |
| 2026-04-24 | Storage can be local or cloud. | The design should support local reviewer runs and cloud-native deployment paths. | Applied |
| 2026-04-24 | Cost for a 30-second video should probably be below `$1`. | Cost analysis and tool selection should explicitly show the pipeline stays well below this target. | Applied |
| 2026-04-24 | Track list, rating colors, and track icons can be mocked. | The `topcoder-star` theme may define practical Dev, Design, and Data Science mock mappings instead of requiring private Topcoder taxonomy data. | Applied |
| 2026-04-24 | Video length is strictly 15-30 seconds. | The pipeline should reject clips materially outside the 15-30 second window. | Applied |
| 2026-04-24 | File size target is roughly 10-30 MB, later clarified as probably below 30 MB. | Rendered MP4 outputs should be measured and rejected if they exceed 30 MB. | Applied |
| 2026-04-24 | Review will likely use 2-3 videos, one pipeline execution per video. | Free-plan/API feasibility can be estimated around low review volume rather than many repeated runs. | Applied |
| 2026-04-24 | Deployment can be anywhere as long as it can be used for review. | Docker/local setup and any reachable hosting platform are acceptable review paths. | Applied |
| 2026-04-25 | 720p is enough if quality is good, and cloud hosting cost is not required in the report. | Landscape render targets 1280x720, and the budget report excludes recurring hosting expenditure. | Applied |
