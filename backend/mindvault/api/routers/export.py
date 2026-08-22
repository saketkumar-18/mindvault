from __future__ import annotations

import json

from fastapi import APIRouter, Request
from fastapi.responses import Response

from mindvault.api.deps import get_container

router = APIRouter(prefix="/api/export")


def _json_response(data: dict[str, object], filename: str) -> Response:
    return Response(
        content=json.dumps(data, indent=2, ensure_ascii=False),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/conversations")
def export_conversations(request: Request) -> Response:
    return _json_response(get_container(request).export_service.conversations_json(), "conversations.json")


@router.get("/knowledge-bases")
def export_kbs(request: Request) -> Response:
    return _json_response(get_container(request).export_service.knowledge_bases_json(), "knowledge_bases.json")


@router.get("/all")
def export_all(request: Request) -> Response:
    buffer = get_container(request).export_service.all_data_zip()
    return Response(
        content=buffer.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="mindvault-export.zip"'},
    )