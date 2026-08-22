from __future__ import annotations

from fastapi import APIRouter, File, Form, Request, UploadFile

from mindvault.api.deps import get_container
from mindvault.db.models import Document
from mindvault.errors import NotFoundError, ValidationFailed

router = APIRouter(prefix="/api/documents")


@router.post("")
def upload_document(
    request: Request,
    file: UploadFile = File(...),
    knowledge_base_id: str | None = Form(None),
    replace: str | None = Form(None),
    duplicate: bool = Form(False),
) -> dict[str, object]:
    container = get_container(request)
    data = file.file.read()
    if not data:
        raise ValidationFailed("Uploaded file is empty.")
    result = container.document_service.store_upload(
        file.filename or "unnamed",
        data,
        knowledge_base_id=knowledge_base_id,
        mime_type=file.content_type,
        duplicate_ok=duplicate,
        replace_id=replace,
    )
    return {"id": result.document_id, "duplicate_of": result.duplicate_of}


@router.get("")
def list_documents(
    request: Request,
    knowledge_base_id: str | None = None,
    status: str | None = None,
    file_type: str | None = None,
    q: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> dict[str, object]:
    from sqlalchemy import func, select

    container = get_container(request)
    query = select(Document)
    if knowledge_base_id:
        query = query.where(Document.knowledge_base_id == knowledge_base_id)
    if status:
        query = query.where(Document.status == status)
    if file_type:
        query = query.where(Document.extension == file_type)
    if q:
        query = query.where(Document.filename.ilike(f"%{q}%"))
    query = query.order_by(Document.updated_at.desc()).offset(offset).limit(limit)
    with container.session_factory() as session:
        docs = session.execute(query).scalars().all()
        total = container.session_factory().execute(
            select(func.count()).select_from(Document)
        ).scalar_one()
    return {
        "documents": [
            {
                "id": d.id,
                "filename": d.filename,
                "extension": d.extension,
                "size_bytes": d.size_bytes,
                "status": d.status,
                "error": d.error,
                "page_count": d.page_count,
                "chunk_count": d.chunk_count,
                "knowledge_base_id": d.knowledge_base_id,
                "created_at": d.created_at.isoformat() if d.created_at else None,
                "updated_at": d.updated_at.isoformat() if d.updated_at else None,
            }
            for d in docs
        ],
        "total": total,
    }


@router.get("/{document_id}")
def get_document(request: Request, document_id: str) -> dict[str, object]:
    with get_container(request).session_factory() as session:
        doc = session.get(Document, document_id)
        if doc is None:
            raise NotFoundError(f"Document '{document_id}' not found.")
        return {
            "id": doc.id,
            "filename": doc.filename,
            "extension": doc.extension,
            "mime_type": doc.mime_type,
            "size_bytes": doc.size_bytes,
            "content_hash": doc.content_hash,
            "status": doc.status,
            "error": doc.error,
            "page_count": doc.page_count,
            "chunk_count": doc.chunk_count,
            "knowledge_base_id": doc.knowledge_base_id,
            "created_at": doc.created_at.isoformat() if doc.created_at else None,
            "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
        }


@router.get("/{document_id}/download")
def download_document(request: Request, document_id: str):
    from starlette.responses import Response

    data, filename = get_container(request).export_service.download_document(document_id)
    return Response(
        content=data,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.patch("/{document_id}")
def update_document(request: Request, document_id: str, filename: str | None = None):
    container = get_container(request)
    if filename:
        container.document_service.rename(document_id, filename)
    return {"status": "ok"}


@router.delete("/{document_id}")
def delete_document(request: Request, document_id: str) -> dict[str, str]:
    get_container(request).document_service.delete(document_id)
    return {"status": "ok"}


@router.post("/{document_id}/reindex")
def reindex_document(request: Request, document_id: str) -> dict[str, object]:
    job_id = get_container(request).document_service.reindex(document_id)
    return {"job_id": job_id}


@router.get("/{document_id}/chunks")
def get_chunks(request: Request, document_id: str, limit: int = 100, offset: int = 0) -> dict[str, object]:
    from sqlalchemy import func, select

    container = get_container(request)
    with container.session_factory() as session:
        doc = session.get(Document, document_id)
        if doc is None:
            raise NotFoundError(f"Document '{document_id}' not found.")
        from mindvault.db.models import DocumentChunk

        query = (
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.ordinal)
            .offset(offset)
            .limit(limit)
        )
        chunks = session.execute(query).scalars().all()
        total = session.execute(
            select(func.count()).select_from(DocumentChunk).where(DocumentChunk.document_id == document_id)
        ).scalar_one()
        return {
            "chunks": [
                {
                    "id": c.id,
                    "ordinal": c.ordinal,
                    "text": c.text,
                    "page_start": c.page_start,
                    "page_end": c.page_end,
                    "section": c.section,
                }
                for c in chunks
            ],
            "total": total,
        }