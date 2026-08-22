from __future__ import annotations

from fastapi import APIRouter, Request

from mindvault.api.deps import get_container
from mindvault.errors import NotFoundError

router = APIRouter(prefix="/api/jobs")


@router.get("")
def list_jobs(request: Request) -> dict[str, object]:
    jobs = get_container(request).jobs.list()
    return {
        "jobs": [
            {
                "id": j.id,
                "kind": j.kind,
                "status": j.status,
                "progress": j.progress,
                "message": j.message,
                "document_id": j.document_id,
                "error": j.error,
                "created_at": j.created_at.isoformat(),
                "finished_at": j.finished_at.isoformat() if j.finished_at else None,
            }
            for j in jobs
        ]
    }


@router.post("/{job_id}/cancel")
def cancel_job(request: Request, job_id: str) -> dict[str, object]:
    try:
        cancelled = get_container(request).jobs.cancel(job_id)
    except NotFoundError:
        raise
    return {"id": job_id, "cancelled": cancelled}