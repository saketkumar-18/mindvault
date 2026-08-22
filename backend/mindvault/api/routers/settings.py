from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, Request

from mindvault.api.deps import get_container

router = APIRouter(prefix="/api")


@router.get("/settings")
def get_settings(request: Request) -> dict[str, Any]:
    container = get_container(request)
    return {
        "settings": container.settings_service.get_effective(),
        "rebuild_required": container.settings_service.get_section("embeddings").get("rebuild_required", False),
    }


@router.put("/settings")
def put_settings(request: Request, updates: dict[str, Any] = Body(...)) -> dict[str, Any]:
    container = get_container(request)
    return {"settings": container.settings_service.put(updates)}


@router.post("/settings/reset")
def reset_settings(request: Request) -> dict[str, Any]:
    container = get_container(request)
    from sqlalchemy import delete

    from mindvault.db.models import AppSetting

    with container.session_factory.begin() as session:
        session.execute(delete(AppSetting))
    return {"settings": container.settings_service.get_effective()}