from __future__ import annotations

import json
import shutil
import uuid
from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.config import Settings, get_settings
from app.jobs import JobStore
from app.models import MemberMetadata, RenderOptions
from app.pipeline import ProfileVideoPipeline, _result_to_dict

app = FastAPI(
    title="Topcoder Profile Intro Video Pipeline",
    description="Renders branded Topcoder member profile videos from raw clips and metadata.",
    version="0.1.0",
)
_settings = get_settings()
_settings.output_dir.mkdir(parents=True, exist_ok=True)
app.mount("/outputs", StaticFiles(directory=str(_settings.output_dir)), name="outputs")


@lru_cache(maxsize=1)
def _get_jobs() -> JobStore:
    """Return the process-lifetime JobStore singleton.

    Using a cached factory (instead of a bare module-level assignment) means
    tests can call ``_get_jobs.cache_clear()`` between cases to get a fresh
    store, and any future config-driven initialisation won't be pinned at
    import time.
    """
    return JobStore()


class JobRequest(BaseModel):
    source_uri: str = Field(..., examples=["samples/raw_intro.mp4", "s3://bucket/raw/member.mp4"])
    output_uri: str | None = Field(None, examples=["outputs/review-job", "s3://bucket/rendered/job"])
    metadata: dict[str, Any]
    render_options: dict[str, Any] = Field(default_factory=dict)


def _pipeline() -> ProfileVideoPipeline:
    return ProfileVideoPipeline(get_settings())


@app.get("/")
def root() -> dict[str, Any]:
    return {
        "name": "Topcoder Profile Intro Video Pipeline",
        "status": "ok",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "upload_render": "POST /render",
            "create_job": "POST /jobs",
            "job_status": "GET /jobs/{job_id}",
            "outputs": "/outputs/{job_id}/{filename}",
        },
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/jobs")
def create_job(payload: JobRequest, background_tasks: BackgroundTasks) -> dict[str, str]:
    try:
        metadata = MemberMetadata.from_dict(payload.metadata)
        options = _render_options_from_payload(payload.render_options)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    job_id = uuid.uuid4().hex[:12]
    _get_jobs().create(job_id)
    background_tasks.add_task(
        _run_job,
        job_id,
        payload.source_uri,
        payload.output_uri,
        metadata,
        options,
    )
    return {"job_id": job_id, "status_url": f"/jobs/{job_id}"}


@app.get("/jobs/{job_id}")
def get_job(job_id: str) -> dict[str, Any]:
    record = _get_jobs().get(job_id)
    if not record:
        raise HTTPException(status_code=404, detail="job not found")
    return {
        "job_id": record.job_id,
        "status": record.status,
        "result": record.result,
        "error": record.error,
        "logs": record.logs[-1:] if record.logs else [],
    }


@app.post("/render")
async def render_upload(
    background_tasks: BackgroundTasks,
    video: UploadFile = File(...),
    metadata_json: str = Form(...),
    render_options_json: str = Form("{}"),
) -> dict[str, Any]:
    try:
        metadata = MemberMetadata.from_dict(json.loads(metadata_json))
        options = _render_options_from_payload(json.loads(render_options_json))
    except (ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    job_id = uuid.uuid4().hex[:12]
    work_dir = options.work_dir / job_id
    output_dir = options.output_dir / job_id
    work_dir.mkdir(parents=True, exist_ok=True)
    input_path = work_dir / (video.filename or "upload.mp4")
    with input_path.open("wb") as output_file:
        shutil.copyfileobj(video.file, output_file)

    _get_jobs().create(job_id)
    background_tasks.add_task(
        _run_upload_job,
        job_id,
        input_path,
        video.filename or "upload.mp4",
        metadata,
        options,
        output_dir,
        work_dir,
    )
    return {
        "job_id": job_id,
        "status": "queued",
        "status_url": f"/jobs/{job_id}",
        "poll_hint": "GET /jobs/{job_id} until status=succeeded, then download from download_urls",
    }


def _render_options_from_payload(payload: dict[str, Any], settings: Settings | None = None) -> RenderOptions:
    settings = settings or get_settings()
    payload = dict(payload or {})
    payload.setdefault("output_dir", str(settings.output_dir))
    payload.setdefault("work_dir", str(settings.render_workdir))
    payload.setdefault("template", settings.template_name)
    return RenderOptions.from_dict(payload)


def _with_output_urls(result: dict[str, Any]) -> dict[str, Any]:
    output_urls: dict[str, str] = {}
    caption_urls: dict[str, str] = {}
    for key, value in result.get("outputs", {}).items():
        url = _local_output_url(str(value))
        if url:
            output_urls[key] = url
    for key, value in result.get("captions", {}).items():
        url = _local_output_url(str(value))
        if url:
            caption_urls[key] = url
    if output_urls or caption_urls:
        result["download_urls"] = {"outputs": output_urls, "captions": caption_urls}
    return result


def _local_output_url(path_value: str, settings: Settings | None = None) -> str | None:
    settings = settings or get_settings()
    try:
        path = Path(path_value).resolve()
        output_root = settings.output_dir.resolve()
        relative = path.relative_to(output_root)
    except ValueError:
        return None
    return "/outputs/" + relative.as_posix()


def _run_job(
    job_id: str,
    source_uri: str,
    output_uri: str | None,
    metadata: MemberMetadata,
    options: RenderOptions,
) -> None:
    _get_jobs().set_running(job_id)
    try:
        result = _pipeline().process_uri(
            source_uri=source_uri,
            metadata=metadata,
            options=options,
            output_uri=output_uri,
            job_id=job_id,
        )
        _get_jobs().set_succeeded(job_id, _with_output_urls(_result_to_dict(result)))
    except Exception as exc:
        _get_jobs().set_failed(job_id, exc)


def _run_upload_job(
    job_id: str,
    input_path: Path,
    filename: str,
    metadata: MemberMetadata,
    options: RenderOptions,
    output_dir: Path,
    work_dir: Path,
) -> None:
    _get_jobs().set_running(job_id)
    try:
        result = _pipeline().process_file(
            input_video=input_path,
            metadata=metadata,
            options=RenderOptions(
                aspect=options.aspect,
                template=options.template,
                output_dir=output_dir,
                work_dir=work_dir,
                music_path=options.music_path,
                keep_intermediates=options.keep_intermediates,
                music_volume=options.music_volume,
                music_lead_volume=options.music_lead_volume,
                music_intro_seconds=options.music_intro_seconds,
                music_outro_seconds=options.music_outro_seconds,
            ),
            job_id=job_id,
            input_uri=f"upload://{filename}",
        )
        _get_jobs().set_succeeded(job_id, _with_output_urls(_result_to_dict(result)))
    except Exception as exc:
        _get_jobs().set_failed(job_id, exc)
