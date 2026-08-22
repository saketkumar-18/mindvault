from __future__ import annotations

from fastapi import APIRouter, Body, Request
from pydantic import BaseModel, Field

from mindvault.api.deps import get_container

router = APIRouter(prefix="/api/study")


class CompareRequest(BaseModel):
    document_ids: list[str] = Field(min_length=2, max_length=5)


class ResumeAnalysisRequest(BaseModel):
    resume_document_id: str
    job_description_document_id: str


@router.post("/generate")
def generate(
    request: Request,
    kind: str = Body(...),
    document_id: str | None = Body(None),
    knowledge_base_id: str | None = Body(None),
) -> dict[str, object]:
    material = get_container(request).study_service.generate(
        kind, document_id=document_id, knowledge_base_id=knowledge_base_id
    )
    return {"id": material.id, "kind": material.kind, "title": material.title, "content": material.content_json}


@router.post("/compare")
def compare(request: Request, payload: CompareRequest) -> dict[str, object]:
    material = get_container(request).study_service.compare(payload.document_ids)
    return {"id": material.id, "kind": material.kind, "title": material.title, "content": material.content_json}


@router.post("/resume-analysis")
def resume_analysis(request: Request, payload: ResumeAnalysisRequest) -> dict[str, object]:
    material = get_container(request).study_service.resume_analysis(
        payload.resume_document_id, payload.job_description_document_id
    )
    return {"id": material.id, "kind": material.kind, "title": material.title, "content": material.content_json}


@router.get("/materials")
def list_materials(request: Request) -> dict[str, object]:
    rows = get_container(request).study_service.list()
    return {
        "materials": [
            {
                "id": m.id,
                "kind": m.kind,
                "title": m.title,
                "document_id": m.document_id,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in rows
        ]
    }


@router.get("/materials/{material_id}")
def get_material(request: Request, material_id: str) -> dict[str, object]:
    m = get_container(request).study_service.get(material_id)
    return {"id": m.id, "kind": m.kind, "title": m.title, "content": m.content_json}


@router.delete("/materials/{material_id}")
def delete_material(request: Request, material_id: str) -> dict[str, str]:
    get_container(request).study_service.delete(material_id)
    return {"status": "ok"}