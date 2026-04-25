# Submission Freeze Checklist

## Code And Behavior

- [x] Latest code changes are complete
- [x] README matches actual behavior
- [x] Known AI or service failure paths report truthfully in docs/manifests
- [x] Deterministic fallback behavior is documented
- [x] Latest forum clarifications are reflected in code or docs
- [ ] Actual public deployed URL still requires external hosting/account access; Docker, Render blueprint, and local review path are ready

## Tests

- [x] `pytest`
- [x] `python scripts/run_demo.py`
- [x] `python scripts/create_before_after_demo.py`
- [x] `python scripts/create_demo_video.py`
- [x] Targeted grep for `TODO|FIXME|eslint-disable`

## Evidence

- [x] Required demo video artifacts are captured from latest build
- [x] Raw logs are saved
- [x] Evidence index is updated

## Patch Packaging

- [ ] Final ZIP can be extracted and still run install/build/demo flow
- [x] No secrets or local `.env` files are included
- [x] No stale screenshots or stale zips remain

## Final Sanity Check

- [ ] Requirements matrix shows all scored requirements as covered (R15 is partially implemented: deploy config exists, but no actual public URL has been created in this workspace)
- [x] Reviewer-risk log has been reviewed one last time
