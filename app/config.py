from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    render_workdir: Path = Path(os.getenv("TOPCODER_RENDER_WORKDIR", "work"))
    output_dir: Path = Path(os.getenv("TOPCODER_OUTPUT_DIR", "outputs"))
    template_name: str = os.getenv("TOPCODER_TEMPLATE", "topcoder-star")
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY") or None
    openai_transcribe_model: str = os.getenv(
        "OPENAI_TRANSCRIBE_MODEL", "gpt-4o-transcribe-diarize"
    )
    aws_region: str = os.getenv("AWS_REGION", "us-east-1")


def get_settings() -> Settings:
    return Settings()
