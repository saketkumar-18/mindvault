from __future__ import annotations

import json
from collections.abc import Iterator

from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from mindvault.db.models import Conversation, Message, gen_id
from mindvault.errors import NotFoundError, ValidationFailed
from mindvault.rag.rag_service import RAGService


class ChatService:
    def __init__(self, session_factory: sessionmaker, rag: RAGService) -> None:
        self.session_factory = session_factory
        self.rag = rag

    # -- conversation CRUD ------------------------------------------------
    def create_conversation(self, title: str | None = None, knowledge_base_id: str | None = None) -> Conversation:
        with self.session_factory.begin() as session:
            conv = Conversation(
                title=(title or "").strip() or "New conversation",
                knowledge_base_id=knowledge_base_id,
            )
            session.add(conv)
            session.flush()
            return conv

    def list_conversations(self) -> list[Conversation]:
        from sqlalchemy.orm import selectinload

        with self.session_factory() as session:
            rows = session.execute(
                select(Conversation)
                .options(selectinload(Conversation.messages))
                .order_by(Conversation.updated_at.desc())
            ).scalars().all()
            return rows

    def get_conversation(self, conversation_id: str) -> Conversation:
        from sqlalchemy.orm import selectinload

        with self.session_factory() as session:
            conv = session.execute(
                select(Conversation)
                .options(selectinload(Conversation.messages))
                .where(Conversation.id == conversation_id)
            ).scalar_one_or_none()
            if conv is None:
                raise NotFoundError(f"Conversation '{conversation_id}' not found.")
            return conv

    def rename_conversation(self, conversation_id: str, title: str) -> Conversation:
        title = (title or "").strip()
        if not title:
            raise ValidationFailed("Conversation title is required.")
        with self.session_factory.begin() as session:
            conv = session.get(Conversation, conversation_id)
            if conv is None:
                raise NotFoundError(f"Conversation '{conversation_id}' not found.")
            conv.title = title
            session.flush()
            return conv

    def delete_conversation(self, conversation_id: str) -> None:
        with self.session_factory.begin() as session:
            conv = session.get(Conversation, conversation_id)
            if conv is None:
                raise NotFoundError(f"Conversation '{conversation_id}' not found.")
            session.delete(conv)

    def list_messages(self, conversation_id: str) -> list[Message]:
        with self.session_factory() as session:
            conv = session.get(Conversation, conversation_id)
            if conv is None:
                raise NotFoundError(f"Conversation '{conversation_id}' not found.")
            return list(conv.messages)

    def _history(self, conversation_id: str, limit: int = 12) -> list[dict[str, str]]:
        with self.session_factory() as session:
            conv = session.get(Conversation, conversation_id)
            if conv is None:
                return []
            return [
                {"role": m.role, "content": m.content}
                for m in conv.messages[-limit:]
                if m.content
            ]

    # -- answering -------------------------------------------------------
    def ask_stream(
        self,
        conversation_id: str,
        question: str,
        *,
        knowledge_base_id: str | None = None,
        persist: bool = True,
    ) -> Iterator[dict[str, object]]:
        question = (question or "").strip()
        if not question:
            raise ValidationFailed("Message cannot be empty.")

        with self.session_factory.begin() as session:
            conv = session.get(Conversation, conversation_id)
            if conv is None:
                raise NotFoundError(f"Conversation '{conversation_id}' not found.")
            if conv.title == "New conversation":
                conv.title = question[:60]
            if persist:
                session.add(Message(conversation_id=conversation_id, role="user", content=question))

        history = self._history(conversation_id)

        sources_payload: list[dict[str, object]] = []
        model = ""

        for event in self.rag.answer_stream(
            question,
            knowledge_base_id=knowledge_base_id or self.get_conversation(conversation_id).knowledge_base_id,
            history=history,
        ):
            event_type = event.get("type")
            if event_type == "sources":
                sources_payload = list(event.get("sources", []))
            elif event_type == "done":
                model = str(event.get("model", ""))
                text = str(event.get("text", ""))
                if persist and text:
                    with self.session_factory.begin() as session:
                        session.add(
                            Message(
                                id=gen_id(),
                                conversation_id=conversation_id,
                                role="assistant",
                                content=text,
                                sources_json=json.dumps(sources_payload),
                                model=model,
                            )
                        )
                event = dict(event)
                event["message_id"] = self._last_message_id(conversation_id) if persist else None
                yield event
                continue
            yield event

    def _last_message_id(self, conversation_id: str) -> str | None:
        with self.session_factory() as session:
            last = session.execute(
                select(Message)
                .where(Message.conversation_id == conversation_id)
                .order_by(Message.created_at.desc())
                .limit(1)
            ).scalar_one_or_none()
            return last.id if last else None

    def regenerate(self, conversation_id: str) -> Iterator[dict[str, object]]:
        """Re-run the last user question, dropping trailing assistant replies."""
        with self.session_factory() as session:
            conv = session.get(Conversation, conversation_id)
            if conv is None:
                raise NotFoundError(f"Conversation '{conversation_id}' not found.")
            messages = list(conv.messages)
            if not messages:
                raise ValidationFailed("No messages to regenerate.")
            # Drop any trailing assistant messages.
            while messages and messages[-1].role == "assistant":
                session.delete(messages[-1])
                messages.pop()
            last = messages[-1]
            question = last.content
            session.commit()

        yield from self.ask_stream(conversation_id, question, persist=True)