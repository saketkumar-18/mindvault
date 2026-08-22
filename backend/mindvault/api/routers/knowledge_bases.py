from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel

from mindvault.api.deps import get_container

router = APIRouter(prefix="/api/knowledge-bases")


class KBCreateRequest(BaseModel):
    name: str
    description: str | None = None


class KBUpdateRequest(BaseModel):
    name: str | None = None


class KBAddDocumentsRequest(BaseModel):
    document_ids: list[str]


@router.post("")
def create_kb(request: Request, payload: KBCreateRequest) -> dict[str, object]:
    kb = get_container(request).knowledge_base_service.create(payload.name, payload.description)
    return {"id": kb.id, "name": kb.name}


@router.get("")
def list_kbs(request: Request) -> dict[str, object]:
    kbs = get_container(request).knowledge_base_service.list()
    return {
        "knowledge_bases": [
            {
                "id": k.id,
                "name": k.name,
                "description": k.description,
                "created_at": k.created_at.isoformat() if k.created_at else None,
            }
            for k in kbs
        ]
    }


@router.get("/{kb_id}")
def get_kb(request: Request, kb_id: str) -> dict[str, object]:
    kb = get_container(request).knowledge_base_service.get(kb_id)
    stats = get_container(request).knowledge_base_service.statistics(kb_id)
    return {"id": kb.id, "name": kb.name, "description": kb.description, "statistics": stats}


@router.patch("/{kb_id}")
def update_kb(request: Request, kb_id: str, payload: KBUpdateRequest) -> dict[str, object]:
    if payload.name:
        get_container(request).knowledge_base_service.rename(kb_id, payload.name)
    return {"id": kb_id, "name": payload.name}


@router.delete("/{kb_id}")
def delete_kb(request: Request, kb_id: str) -> dict[str, str]:
    get_container(request).knowledge_base_service.delete(kb_id)
    return {"status": "ok"}


@router.post("/{kb_id}/documents")
def add_documents(request: Request, kb_id: str, payload: KBAddDocumentsRequest) -> dict[str, str]:
    get_container(request).knowledge_base_service.add_documents(kb_id, payload.document_ids)
    return {"status": "ok"}


@router.delete("/{kb_id}/documents/{document_id}")
def remove_document(request: Request, kb_id: str, document_id: str) -> dict[str, str]:
    get_container(request).knowledge_base_service.remove_document(kb_id, document_id)
    return {"status": "ok"}