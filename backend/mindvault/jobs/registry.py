from __future__ import annotations

import threading
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime

from mindvault.errors import NotFoundError

_JOB_KINDS = {"index", "reindex", "rebuild_index", "generate", "embed"}


@dataclass
class Job:
    id: str
    kind: str
    status: str = "queued"
    progress: float = 0.0
    message: str = ""
    document_id: str | None = None
    error: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    started_at: datetime | None = None
    finished_at: datetime | None = None
    cancelled: bool = False


class JobRegistry:
    """Thread-safe registry of in-process background jobs."""

    def __init__(self, executor=None) -> None:
        self._jobs: dict[str, Job] = {}
        self._lock = threading.RLock()
        self._executor = executor

    def submit(self, job_id: str, fn: Callable[[], None], executor=None) -> None:
        self.start(job_id)
        target = executor or self._executor
        if target is None:
            raise RuntimeError("No executor configured for JobRegistry.")

        def _run() -> None:
            try:
                fn()
                if not self.is_cancelled(job_id):
                    self.complete(job_id)
            except Exception as exc:  # noqa: BLE001
                if not self.is_cancelled(job_id):
                    self.fail(job_id, str(exc))
                else:
                    self.fail(job_id, "Cancelled")

        target.submit(_run)

    # -- CRUD ------------------------------------------------------------
    def create(self, kind: str, *, document_id: str | None = None) -> Job:
        if kind not in _JOB_KINDS:
            raise ValueError(f"Unknown job kind: {kind}")
        job = Job(id=uuid.uuid4().hex, kind=kind, document_id=document_id)
        with self._lock:
            self._jobs[job.id] = job
        return job

    def get(self, job_id: str) -> Job:
        with self._lock:
            job = self._jobs.get(job_id)
        if job is None:
            raise NotFoundError(f"Job '{job_id}' not found.")
        return job

    def list(self) -> list[Job]:
        with self._lock:
            jobs = sorted(self._jobs.values(), key=lambda j: j.created_at, reverse=True)
        return jobs

    # -- transitions -----------------------------------------------------
    def start(self, job_id: str) -> None:
        job = self.get(job_id)
        with self._lock:
            job.status = "processing"
            job.started_at = job.started_at or datetime.now(UTC)

    def update(self, job_id: str, progress: float | None = None, message: str | None = None) -> None:
        job = self.get(job_id)
        with self._lock:
            if progress is not None:
                job.progress = max(0.0, min(1.0, progress))
            if message is not None:
                job.message = message

    def complete(self, job_id: str) -> None:
        job = self.get(job_id)
        with self._lock:
            job.status = "completed"
            job.progress = 1.0
            job.finished_at = datetime.now(UTC)

    def fail(self, job_id: str, error: str) -> None:
        job = self.get(job_id)
        with self._lock:
            job.status = "failed"
            job.error = error
            job.finished_at = datetime.now(UTC)

    def cancel(self, job_id: str) -> bool:
        job = self.get(job_id)
        with self._lock:
            was_active = job.status in ("queued", "processing")
            if was_active:
                job.cancelled = True
                job.status = "cancelled"
                job.message = "Cancelled by user."
                job.finished_at = datetime.now(UTC)
        return was_active

    def is_cancelled(self, job_id: str) -> bool:
        job = self.get(job_id)
        with self._lock:
            return job.cancelled