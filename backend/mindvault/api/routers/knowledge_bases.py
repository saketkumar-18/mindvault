from __future__ import annotations

from fastapi import APIRouter, Request

from mindvault.api.deps import get_container

router = APIRouter(prefix="/api/knowledge-bases")


@router.post("")
def create_kb(request: Request, name: str, description: str | None = None) -> dict[str, object]:
    kb = get_container(request).knowledge_base_service.create(name, description)
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
def update_kb(request: Request, kb_id: str, name: str | None = None) -> dict[str, object]:
    if name:
        get_container(request).knowledge_base_service.rename(kb_id, name)
    return {"id": kb_id, "name": name}


@router.delete("/{kb_id}")
def delete_kb(request: Request, kb_id: str) -> dict[str, str]:
    get_container(request).knowledge_base_service.delete(kb_id)
    return {"status": "ok"}


@router.post("/{kb_id}/documents")
def add_documents(request: Request, kb_id: str, document_ids: list[str]) -> dict[str, str]:
    get_container(request).knowledge_base_service.add_documents(kb_id, document_ids)
    return {"status": "ok"}


@router.delete("/{kb_id}/documents/{document_id}")
def remove_document(request: Request, kb_id: str, document_id: str) -> dict[str, str]:
    get_container(request).knowledge_base_service.remove_document(kb_id, document_id)
    return {"status": "ok"}