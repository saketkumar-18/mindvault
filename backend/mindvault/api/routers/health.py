from __future__ import annotations

from fastapi import APIRouter, Request

from mindvault.api.deps import get_container
from mindvault.services.container import ServiceContainer

router = APIRouter()


def _health(container: ServiceContainer) -> dict[str, object]:
    model_resolution = container.models_service.list_models()["current"]
    return {
        "status": "ok",
        "database": True,
        "vector_store": container.store.count(),
        "model": model_resolution,
        "version": "0.3.0",
    }


@router.get("/health")
def health(request: Request) -> dict[str, object]:
    return _health(get_container(request.app))


@router.get("/api/health")
def api_health(request: Request) -> dict[str, object]:
    return _health(get_container(request.app))


@router.get("/liveness")
def liveness() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/api/liveness")
def api_liveness() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/readiness")
def readiness(request: Request) -> dict[str, object]:
    return _health(get_container(request.app))


@router.get("/api/readiness")
def api_readiness(request: Request) -> dict[str, object]:
    return _health(get_container(request.app))