from __future__ import annotations


def estimate_profile_cost(
    duration_seconds: float,
    *,
    use_openai: bool,
    transcribe_model: str | None = None,
    use_fargate: bool = True,
) -> float:
    """Estimate direct per-profile processing cost for a 30 second class workload.

    This excludes fixed costs such as NAT gateways, ALBs, or long-term archival storage.
    """

    minutes = max(duration_seconds / 60.0, 0.25)
    transcription = 0.0
    if use_openai:
        transcription_rate = 0.003
        if transcribe_model:
            normalized = transcribe_model.lower()
            if (
                normalized.startswith("gpt-4o-transcribe")
                or normalized.startswith("gpt-4o-transcribe-diarize")
                or normalized.startswith("whisper-1")
            ):
                transcription_rate = 0.006
        transcription = minutes * transcription_rate

    # Assumes one Linux/X86 Fargate worker with 2 vCPU / 4 GB for 60 seconds.
    fargate = 0.0
    if use_fargate:
        seconds = 60
        fargate = (2 * 0.000011244 * seconds) + (4 * 0.000001235 * seconds)

    # Three S3 PUTs and two GETs are materially below one cent, but keep a visible estimate.
    s3_requests_and_storage = 0.00005
    return round(transcription + fargate + s3_requests_and_storage, 5)
