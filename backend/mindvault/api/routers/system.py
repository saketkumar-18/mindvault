from __future__ import annotations

from fastapi import APIRouter, Request

from mindvault.api.deps import get_container

router = APIRouter(prefix="/api/system")


@router.get("/info")
def system_info(request: Request) -> dict[str, object]:
    return get_container(request).system_service.system_info()


@router.get("/stats")
def stats(request: Request) -> dict[str, object]:
    return get_container(request).system_service.stats()


@router.get("/first-run")
def first_run(request: Request) -> dict[str, object]:
    return get_container(request).system_service.first_run_state()


@router.post("/first-run/complete")
def complete_first_run(request: Request) -> dict[str, str]:
    get_container(request).system_service.mark_first_run_complete()
    return {"status": "ok"}


@router.delete("/data")
def clear_all_data(request: Request, confirm: str = ""):
    """Clear all application data: documents, conversations, indexes, settings."""
    if confirm.lower() != "delete":
        from mindvault.errors import ValidationFailed

        raise ValidationFailed("Send confirm=DELETE to confirm.")
    container = get_container(request)
    container.document_service._delete_all_documents()
    container.store.save()

    from mindvault.db.models import AppSetting, Conversation, StudyMaterial

    with container.session_factory.begin() as session:
        for table in (StudyMaterial.__table__, Conversation.__table__, AppSetting.__table__):
            session.execute(table.delete())
    return {"status": "ok", "message": "All data cleared."}