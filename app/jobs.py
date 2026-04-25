from __future__ import annotations

import traceback
from dataclasses import dataclass, field
from enum import StrEnum
from threading import Lock
from typing import Any


class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


@dataclass
class JobRecord:
    job_id: str
    status: JobStatus = JobStatus.QUEUED
    result: dict[str, Any] | None = None
    error: str | None = None
    logs: list[str] = field(default_factory=list)


class JobStore:
    def __init__(self) -> None:
        self._records: dict[str, JobRecord] = {}
        self._lock = Lock()

    def create(self, job_id: str) -> JobRecord:
        with self._lock:
            record = JobRecord(job_id=job_id)
            self._records[job_id] = record
            return record

    def set_running(self, job_id: str) -> None:
        with self._lock:
            self._records[job_id].status = JobStatus.RUNNING

    def set_succeeded(self, job_id: str, result: dict[str, Any]) -> None:
        with self._lock:
            self._records[job_id].status = JobStatus.SUCCEEDED
            self._records[job_id].result = result

    def set_failed(self, job_id: str, exc: BaseException) -> None:
        with self._lock:
            self._records[job_id].status = JobStatus.FAILED
            self._records[job_id].error = str(exc)
            self._records[job_id].logs.append(traceback.format_exc())

    def get(self, job_id: str) -> JobRecord | None:
        with self._lock:
            return self._records.get(job_id)
