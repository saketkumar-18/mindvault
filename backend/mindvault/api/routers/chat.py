from __future__ import annotations

import json
from collections.abc import Iterator

from fastapi import APIRouter, Body, Request
from fastapi.responses import StreamingResponse

from mindvault.api.deps import get_container

router = APIRouter(prefix="/api")


def _sse(events: Iterator[dict[str, object]]) -> StreamingResponse:
    def generate():
        for event in events:
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/chat")
def chat(
    request: Request,
    conversation_id: str | None = Body(None),
    message: str = Body(...),
    knowledge_base_id: str | None = Body(None),
    stream: bool = Body(True),
) -> object:
    container = get_container(request)
    if not conversation_id:
        conversation_id = container.chat_service.create_conversation(
            title=message[:60], knowledge_base_id=knowledge_base_id
        ).id
    container.chat_service.get_conversation(conversation_id)

    events = container.chat_service.ask_stream(
        conversation_id, message, knowledge_base_id=knowledge_base_id, persist=True
    )
    if stream:
        return _sse(events)

    result: dict[str, object] = {"conversation_id": conversation_id}
    for event in events:
        event_type = event.get("type")
        if event_type == "token":
            result["text"] = result.get("text", "") + str(event.get("text", ""))
        elif event_type == "sources":
            result["sources"] = event.get("sources", [])
        elif event_type == "done":
            result["text"] = event.get("text", "")
            result["sources"] = event.get("sources", [])
            result["model"] = event.get("model")
            result["provider"] = event.get("provider")
            result["grounded"] = event.get("grounded")
            result["message_id"] = event.get("message_id")
        elif event_type == "error":
            result["error"] = {"message": event.get("message"), "suggestion": event.get("suggestion")}
    return result


@router.post("/chat/{conversation_id}/stop")
def stop_generation(request: Request, conversation_id: str) -> dict[str, str]:
    get_container(request).chat_service.get_conversation(conversation_id)
    return {"status": "stopped"}


@router.post("/chat/{conversation_id}/regenerate")
def regenerate(request: Request, conversation_id: str, stream: bool = True) -> object:
    container = get_container(request)
    events = container.chat_service.regenerate(conversation_id)
    if stream:
        return _sse(events)
    result: dict[str, object] = {"conversation_id": conversation_id}
    for event in events:
        if event.get("type") == "token":
            result["text"] = result.get("text", "") + str(event.get("text", ""))
        elif event.get("type") == "done":
            result["text"] = event.get("text", "")
            result["sources"] = event.get("sources", [])
            result["model"] = event.get("model")
    return result


@router.post("/conversations")
def create_conversation(
    request: Request, title: str | None = None, knowledge_base_id: str | None = None
) -> dict[str, object]:
    conv = get_container(request).chat_service.create_conversation(title, knowledge_base_id)
    return {"id": conv.id, "title": conv.title}


@router.get("/conversations")
def list_conversations(request: Request) -> dict[str, object]:
    convs = get_container(request).chat_service.list_conversations()
    return {
        "conversations": [
            {
                "id": c.id,
                "title": c.title,
                "knowledge_base_id": c.knowledge_base_id,
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "updated_at": c.updated_at.isoformat() if c.updated_at else None,
                "message_count": len(c.messages),
            }
            for c in convs
        ]
    }


@router.get("/conversations/{conversation_id}")
def get_conversation(request: Request, conversation_id: str) -> dict[str, object]:
    conv = get_container(request).chat_service.get_conversation(conversation_id)
    return {
        "id": conv.id,
        "title": conv.title,
        "knowledge_base_id": conv.knowledge_base_id,
        "created_at": conv.created_at.isoformat() if conv.created_at else None,
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "sources": json.loads(m.sources_json) if m.sources_json else [],
                "model": m.model,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in conv.messages
        ],
    }


@router.patch("/conversations/{conversation_id}")
def rename_conversation(request: Request, conversation_id: str, title: str) -> dict[str, object]:
    conv = get_container(request).chat_service.rename_conversation(conversation_id, title)
    return {"id": conv.id, "title": conv.title}


@router.delete("/conversations/{conversation_id}")
def delete_conversation(request: Request, conversation_id: str) -> dict[str, str]:
    get_container(request).chat_service.delete_conversation(conversation_id)
    return {"status": "ok"}