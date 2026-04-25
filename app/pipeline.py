from __future__ import annotations

import json
import shutil
import time
import uuid
from pathlib import Path

from app.audio import clean_voice_track, generate_music_bed, mix_voice_and_music
from app.branding import build_brand_package
from app.captions import write_ass, write_srt
from app.config import Settings
from app.costing import estimate_profile_cost
from app.ffmpeg import probe_duration
from app.models import MemberMetadata, RenderAspect, RenderOptions, RenderResult
from app.storage import adapter_for_uri
from app.transcription import FallbackTranscriptProvider, choose_transcript_provider
from app.video import render_profile_video


class ProfileVideoPipeline:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def process_uri(
        self,
        *,
        source_uri: str,
        metadata: MemberMetadata,
        options: RenderOptions,
        output_uri: str | None = None,
        job_id: str | None = None,
    ) -> RenderResult:
        job_id = job_id or uuid.uuid4().hex[:12]
        job_workdir = options.work_dir / job_id
        job_output_dir = options.output_dir / job_id
        job_workdir.mkdir(parents=True, exist_ok=True)
        job_output_dir.mkdir(parents=True, exist_ok=True)

        input_path = job_workdir / "raw_input.mp4"
        adapter_for_uri(source_uri, region=self.settings.aws_region).download(source_uri, input_path)
        result = self.process_file(
            input_video=input_path,
            metadata=metadata,
            options=RenderOptions(
                aspect=options.aspect,
                template=options.template,
                output_dir=job_output_dir,
                work_dir=job_workdir,
                music_path=options.music_path,
                keep_intermediates=options.keep_intermediates,
                music_volume=options.music_volume,
                music_lead_volume=options.music_lead_volume,
                music_intro_seconds=options.music_intro_seconds,
                music_outro_seconds=options.music_outro_seconds,
            ),
            job_id=job_id,
            input_uri=source_uri,
        )

        if output_uri:
            output_adapter = adapter_for_uri(output_uri, region=self.settings.aws_region)
            for aspect, path in result.outputs.items():
                suffix = Path(path).name
                target = output_uri.rstrip("/") + "/" + suffix
                result.outputs[aspect] = output_adapter.upload(Path(path), target)
            for caption_type, path in result.captions.items():
                suffix = Path(path).name
                target = output_uri.rstrip("/") + "/" + suffix
                result.captions[caption_type] = output_adapter.upload(Path(path), target)
            manifest_target = output_uri.rstrip("/") + "/manifest.json"
            local_manifest = job_output_dir / "manifest.json"
            result.manifest_path = manifest_target
            local_manifest.write_text(json.dumps(_result_to_dict(result), indent=2), encoding="utf-8")
            result.manifest_path = output_adapter.upload(local_manifest, manifest_target)

        if not options.keep_intermediates:
            shutil.rmtree(job_workdir, ignore_errors=True)

        return result

    def process_file(
        self,
        *,
        input_video: Path,
        metadata: MemberMetadata,
        options: RenderOptions,
        job_id: str | None = None,
        input_uri: str | None = None,
    ) -> RenderResult:
        job_id = job_id or uuid.uuid4().hex[:12]
        options.work_dir.mkdir(parents=True, exist_ok=True)
        options.output_dir.mkdir(parents=True, exist_ok=True)

        timings: dict[str, float] = {}
        started = time.perf_counter()
        duration = probe_duration(input_video)
        timings["probe_seconds"] = time.perf_counter() - started

        _validate_duration(duration)

        started = time.perf_counter()
        voice = clean_voice_track(input_video, options.work_dir / "voice_clean.m4a", duration)
        music = options.music_path or generate_music_bed(options.work_dir / "music_bed.m4a", duration)
        mixed = mix_voice_and_music(
            voice,
            music,
            options.work_dir / "voice_music_mix.m4a",
            duration=duration,
            music_volume=options.music_volume,
            music_lead_volume=options.music_lead_volume,
            music_intro_seconds=options.music_intro_seconds,
            music_outro_seconds=options.music_outro_seconds,
        )
        timings["audio_seconds"] = time.perf_counter() - started

        provider = choose_transcript_provider(self.settings.openai_transcribe_model)
        started = time.perf_counter()
        segments, transcription_adapter, warnings, requested_transcription_adapter = (
            self._transcribe_with_fallback(
                provider=provider,
                voice=voice,
                metadata=metadata,
                duration=duration,
            )
        )
        brand = build_brand_package(metadata, template=options.template)
        srt_path = write_srt(segments, options.output_dir / "captions.srt")

        # Generate a separate ASS file per render resolution.  PlayRes must match
        # the actual video dimensions so libass scales the font and margins
        # correctly — a mismatch is what caused the oversized portrait captions.
        _aspect_dims: dict[RenderAspect, tuple[int, int]] = {
            RenderAspect.LANDSCAPE: (1280, 720),
            RenderAspect.VERTICAL: (1080, 1920),
        }
        _ass_paths: dict[RenderAspect, Path] = {}
        for _asp, (_w, _h) in _aspect_dims.items():
            _suffix = "portrait" if _asp == RenderAspect.VERTICAL else "landscape"
            _ass_paths[_asp] = write_ass(
                segments,
                options.output_dir / f"captions_{_suffix}.ass",
                primary_color=brand.primary_color,
                accent_color=brand.accent_color,
                font_name=brand.caption_font,
                width=_w,
                height=_h,
                box_background=True,
                min_start_seconds=0.85,
            )
        # Expose the landscape version as the canonical captions.ass download.
        ass_path = options.output_dir / "captions.ass"
        shutil.copyfile(_ass_paths[RenderAspect.LANDSCAPE], ass_path)
        timings["caption_seconds"] = time.perf_counter() - started

        outputs: dict[str, str] = {}
        output_file_sizes: dict[str, int] = {}
        render_aspects = (
            [RenderAspect.LANDSCAPE, RenderAspect.VERTICAL]
            if options.aspect == RenderAspect.BOTH
            else [options.aspect]
        )
        started = time.perf_counter()
        for aspect in render_aspects:
            output_path = options.output_dir / f"profile_{aspect.value}.mp4"
            render_profile_video(
                input_video=input_video,
                mixed_audio=mixed,
                captions_ass=_ass_paths.get(aspect, ass_path),
                output_video=output_path,
                metadata=metadata,
                brand=brand,
                aspect=aspect,
                duration_seconds=duration,
            )
            outputs[aspect.value] = str(output_path)
            output_file_sizes[aspect.value] = _validate_output_file_size(output_path)
        timings["render_seconds"] = time.perf_counter() - started

        estimated_cost = estimate_profile_cost(
            duration,
            use_openai=transcription_adapter.startswith("openai"),
            transcribe_model=requested_transcription_adapter
            if requested_transcription_adapter.startswith("openai")
            else transcription_adapter,
            use_fargate=True,
        )
        manifest_path = options.output_dir / "manifest.json"
        adapters = {
            "transcription": transcription_adapter,
            "renderer": "ffmpeg-libx264-libass",
            "audio": "ffmpeg-afftdn-loudnorm-sidechaincompress",
        }
        if requested_transcription_adapter != transcription_adapter:
            adapters["transcription_requested"] = requested_transcription_adapter
        result = RenderResult(
            job_id=job_id,
            input_uri=input_uri or str(input_video),
            outputs=outputs,
            captions={"srt": str(srt_path), "ass": str(ass_path)},
            manifest_path=str(manifest_path),
            duration_seconds=duration,
            estimated_cost_usd=estimated_cost,
            output_file_sizes_bytes=output_file_sizes,
            timings=timings,
            adapters=adapters,
            warnings=warnings,
        )
        manifest_path.write_text(json.dumps(_result_to_dict(result), indent=2), encoding="utf-8")
        return result

    def _transcribe_with_fallback(
        self,
        *,
        provider: object,
        voice: Path,
        metadata: MemberMetadata,
        duration: float,
    ) -> tuple[list, str, list[str], str]:
        requested_name = str(getattr(provider, "name", "unknown"))
        try:
            segments = provider.transcribe(voice, metadata, duration)
            return segments, requested_name, [], requested_name
        except Exception as exc:
            if not requested_name.startswith("openai"):
                raise

            fallback = FallbackTranscriptProvider()
            segments = fallback.transcribe(voice, metadata, duration)
            error_message = " ".join(str(exc).split())
            if len(error_message) > 240:
                error_message = error_message[:237] + "..."
            warning = (
                f"OpenAI transcription failed and the pipeline fell back to scripted captions. "
                f"Reason: {exc.__class__.__name__}: {error_message}"
            )
            return segments, fallback.name, [warning], requested_name


_MIN_DURATION = 15.0
_MAX_DURATION = 30.0
_DURATION_TOLERANCE = 0.25
_MAX_OUTPUT_BYTES = 30 * 1024 * 1024


def _validate_duration(duration: float) -> None:
    """Raise ValueError when the clip falls outside the accepted window.

    Forum guidance confirmed that the video length is strict at 15-30 seconds.
    A tiny tolerance absorbs muxing/probing round-off for nominal 15 or 30
    second clips without accepting materially off-spec inputs.
    """
    if duration < (_MIN_DURATION - _DURATION_TOLERANCE):
        raise ValueError(
            f"Input video is too short ({duration:.1f} s); "
            "accepted duration is 15-30 seconds."
        )
    if duration > (_MAX_DURATION + _DURATION_TOLERANCE):
        raise ValueError(
            f"Input video is too long ({duration:.1f} s); "
            "accepted duration is 15-30 seconds. "
            "Trim the clip and resubmit."
        )


def _validate_output_file_size(path: Path, max_bytes: int = _MAX_OUTPUT_BYTES) -> int:
    size = path.stat().st_size
    if size > max_bytes:
        max_mb = max_bytes / (1024 * 1024)
        actual_mb = size / (1024 * 1024)
        raise ValueError(
            f"Rendered output {path.name} is {actual_mb:.1f} MB; "
            f"maximum accepted output size is {max_mb:.0f} MB."
        )
    return size


def _result_to_dict(result: RenderResult) -> dict:
    return {
        "job_id": result.job_id,
        "input_uri": result.input_uri,
        "outputs": result.outputs,
        "captions": result.captions,
        "manifest_path": result.manifest_path,
        "duration_seconds": round(result.duration_seconds, 3),
        "estimated_cost_usd": result.estimated_cost_usd,
        "output_file_sizes_bytes": result.output_file_sizes_bytes,
        "timings": {key: round(value, 3) for key, value in result.timings.items()},
        "adapters": result.adapters,
        "warnings": result.warnings,
    }
