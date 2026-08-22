from __future__ import annotations

from fastapi import APIRouter, Body, Request

from mindvault.api.deps import get_container

router = APIRouter(prefix="/api")


@router.post("/search")
def search(
    request: Request,
    query: str = Body(...),
    knowledge_base_id: str | None = Body(None),
    document_ids: list[str] | None = Body(None),
    file_types: list[str] | None = Body(None),
    top_k: int | None = Body(None),
    global_scope: bool = Body(False),
) -> dict[str, object]:
    container = get_container(request)
    if global_scope:
        return container.search_service.global_search(query)
    matches = container.search_service.search(
        query,
        knowledge_base_id=knowledge_base_id,
        document_ids=document_ids,
        file_types=file_types,
        top_k=top_k,
    )
    return {
        "results": [
            {
                "chunk_id": m.chunk_id,
                "document_id": m.document_id,
                "filename": m.filename,
                "score": round(m.score, 4),
                "text": m.text,
                "page_start": m.page_start,
                "page_end": m.page_end,
                "section": m.section,
            }
            for m in matches
        ]
    }