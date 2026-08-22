from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from mindvault.db.models import Conversation, Document, DocumentChunk, KnowledgeBase
from mindvault.embeddings.base import EmbeddingProvider
from mindvault.services.settings import SettingsService
from mindvault.vectorstore.base import VectorStore


@dataclass
class ChunkMatch:
    chunk_id: str
    document_id: str
    filename: str
    score: float
    text: str
    page_start: int | None
    page_end: int | None
    section: str | None


class SearchService:
    def __init__(
        self,
        session_factory: sessionmaker,
        embeddings: EmbeddingProvider,
        store: VectorStore,
        settings_svc: SettingsService,
    ) -> None:
        self.session_factory = session_factory
        self.embeddings = embeddings
        self.store = store
        self.settings_svc = settings_svc

    def _allowed_chunk_ids(
        self,
        *,
        knowledge_base_id: str | None,
        document_ids: list[str] | None,
        file_types: list[str] | None,
    ) -> set[str]:
        with self.session_factory() as session:
            query = select(DocumentChunk.id).join(Document, DocumentChunk.document_id == Document.id)
            if knowledge_base_id:
                query = query.where(Document.knowledge_base_id == knowledge_base_id)
            if document_ids:
                query = query.where(Document.id.in_(document_ids))
            if file_types:
                query = query.where(Document.extension.in_(file_types))
            return set(session.execute(query).scalars().all())

    def search(
        self,
        query: str,
        *,
        knowledge_base_id: str | None = None,
        document_ids: list[str] | None = None,
        file_types: list[str] | None = None,
        top_k: int | None = None,
    ) -> list[ChunkMatch]:
        query = (query or "").strip()
        if not query:
            return []
        effective = self.settings_svc.get_effective()
        k = top_k or effective["retrieval"]["top_k"]

        allowed = self._allowed_chunk_ids(
            knowledge_base_id=knowledge_base_id,
            document_ids=document_ids,
            file_types=file_types,
        )
        if not allowed:
            return []

        vector = self.embeddings.embed([query])[0]
        hits = self.store.query(vector, top_k=max(k * 4, k))
        hits = [h for h in hits if h.id in allowed]

        if not hits:
            return []

        chunk_ids = [h.id for h in hits]
        with self.session_factory() as session:
            rows = session.execute(
                select(DocumentChunk, Document)
                .join(Document, DocumentChunk.document_id == Document.id)
                .where(DocumentChunk.id.in_(chunk_ids))
            ).all()

        by_id = {chunk.id: (chunk, doc) for chunk, doc in rows}
        matches: list[ChunkMatch] = []
        for hit in hits:
            pair = by_id.get(hit.id)
            if pair is None:
                continue
            chunk, doc = pair
            matches.append(
                ChunkMatch(
                    chunk_id=chunk.id,
                    document_id=doc.id,
                    filename=doc.filename,
                    score=hit.score,
                    text=chunk.text,
                    page_start=chunk.page_start,
                    page_end=chunk.page_end,
                    section=chunk.section,
                )
            )
        return matches[:k]

    def global_search(
        self,
        query: str,
        *,
        top_docs: int = 5,
        top_conversations: int = 5,
        top_kbs: int = 5,
    ) -> dict[str, object]:
        """Search documents, conversations, and knowledge bases."""
        q = (query or "").strip().lower()
        results: dict[str, object] = {"documents": [], "conversations": [], "knowledge_bases": []}
        if not q:
            return results

        with self.session_factory() as session:
            docs = session.execute(
                select(Document).where(Document.filename.ilike(f"%{q}%")).order_by(Document.updated_at.desc()).limit(top_docs)
            ).scalars().all()
            conversations = session.execute(
                select(Conversation).where(Conversation.title.ilike(f"%{q}%")).order_by(Conversation.updated_at.desc()).limit(top_conversations)
            ).scalars().all()
            kbs = session.execute(
                select(KnowledgeBase).where(KnowledgeBase.name.ilike(f"%{q}%")).limit(top_kbs)
            ).scalars().all()

        results["documents"] = [{"id": d.id, "filename": d.filename, "status": d.status} for d in docs]
        results["conversations"] = [{"id": c.id, "title": c.title} for c in conversations]
        results["knowledge_bases"] = [{"id": k.id, "name": k.name} for k in kbs]
        return results