from __future__ import annotations

from fastapi import APIRouter, Request

from mindvault.api.deps import get_container

router = APIRouter(prefix="/api/models")


@router.get("")
def list_models(request: Request) -> dict[str, object]:
    return get_container(request).models_service.list_models()


@router.post("/test")
def test_model(request: Request) -> dict[str, object]:
    return get_container(request).models_service.test_model()