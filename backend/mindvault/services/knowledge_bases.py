from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import sessionmaker

from mindvault.db.models import Conversation, Document, DocumentChunk, KnowledgeBase
from mindvault.errors import ConflictError, NotFoundError, ValidationFailed


class KnowledgeBaseService:
    def __init__(self, session_factory: sessionmaker) -> None:
        self.session_factory = session_factory

    def create(self, name: str, description: str | None = None) -> KnowledgeBase:
        name = (name or "").strip()
        if not name:
            raise ValidationFailed("Knowledge base name is required.")
        with self.session_factory.begin() as session:
            existing = session.execute(
                select(KnowledgeBase).where(KnowledgeBase.name == name)
            ).scalar_one_or_none()
            if existing:
                raise ConflictError(f"Knowledge base '{name}' already exists.")
            kb = KnowledgeBase(name=name, description=description)
            session.add(kb)
            session.flush()
            return kb

    def list(self) -> list[KnowledgeBase]:
        with self.session_factory() as session:
            rows = session.execute(select(KnowledgeBase).order_by(KnowledgeBase.name)).scalars().all()
            return rows

    def get(self, knowledge_base_id: str) -> KnowledgeBase:
        with self.session_factory() as session:
            kb = session.get(KnowledgeBase, knowledge_base_id)
            if kb is None:
                raise NotFoundError(f"Knowledge base '{knowledge_base_id}' not found.")
            return kb

    def rename(self, knowledge_base_id: str, name: str) -> KnowledgeBase:
        name = (name or "").strip()
        if not name:
            raise ValidationFailed("Knowledge base name is required.")
        with self.session_factory.begin() as session:
            kb = session.get(KnowledgeBase, knowledge_base_id)
            if kb is None:
                raise NotFoundError(f"Knowledge base '{knowledge_base_id}' not found.")
            duplicate = session.execute(
                select(KnowledgeBase).where(KnowledgeBase.name == name, KnowledgeBase.id != knowledge_base_id)
            ).scalar_one_or_none()
            if duplicate:
                raise ConflictError(f"Knowledge base '{name}' already exists.")
            kb.name = name
            session.flush()
            return kb

    def delete(self, knowledge_base_id: str) -> None:
        """Delete the KB. Documents are unassigned (kept), conversations stay."""
        with self.session_factory.begin() as session:
            kb = session.get(KnowledgeBase, knowledge_base_id)
            if kb is None:
                raise NotFoundError(f"Knowledge base '{knowledge_base_id}' not found.")
            session.execute(
                Document.__table__.update()
                .where(Document.knowledge_base_id == kb.id)
                .values(knowledge_base_id=None)
            )
            session.execute(
                Conversation.__table__.update()
                .where(Conversation.knowledge_base_id == kb.id)
                .values(knowledge_base_id=None)
            )
            session.delete(kb)

    def add_documents(self, knowledge_base_id: str, document_ids: list[str]) -> None:
        with self.session_factory.begin() as session:
            kb = session.get(KnowledgeBase, knowledge_base_id)
            if kb is None:
                raise NotFoundError(f"Knowledge base '{knowledge_base_id}' not found.")
            for doc_id in document_ids:
                doc = session.get(Document, doc_id)
                if doc is None:
                    raise NotFoundError(f"Document '{doc_id}' not found.")
                doc.knowledge_base_id = knowledge_base_id

    def remove_document(self, knowledge_base_id: str, document_id: str) -> None:
        with self.session_factory.begin() as session:
            kb = session.get(KnowledgeBase, knowledge_base_id)
            if kb is None:
                raise NotFoundError(f"Knowledge base '{knowledge_base_id}' not found.")
            doc = session.get(Document, document_id)
            if doc is None or doc.knowledge_base_id != knowledge_base_id:
                raise NotFoundError(f"Document '{document_id}' is not in this knowledge base.")
            doc.knowledge_base_id = None

    def statistics(self, knowledge_base_id: str) -> dict[str, object]:
        with self.session_factory() as session:
            kb = session.get(KnowledgeBase, knowledge_base_id)
            if kb is None:
                raise NotFoundError(f"Knowledge base '{knowledge_base_id}' not found.")
            doc_count = session.execute(
                select(func.count()).select_from(Document).where(Document.knowledge_base_id == knowledge_base_id)
            ).scalar_one()
            chunk_count = session.execute(
                select(func.count())
                .select_from(DocumentChunk)
                .join(Document, DocumentChunk.document_id == Document.id)
                .where(Document.knowledge_base_id == knowledge_base_id)
            ).scalar_one()
            total_bytes = session.execute(
                select(func.coalesce(func.sum(Document.size_bytes), 0)).where(
                    Document.knowledge_base_id == knowledge_base_id
                )
            ).scalar_one()
            return {"document_count": doc_count, "chunk_count": chunk_count, "total_bytes": int(total_bytes)}
