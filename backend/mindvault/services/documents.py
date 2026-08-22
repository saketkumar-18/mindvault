from __future__ import annotations

import hashlib
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from mindvault.config import Settings
from mindvault.db.models import Document, DocumentChunk, gen_id
from mindvault.domain.chunker import ChunkSpec, chunk_document
from mindvault.embeddings.base import EmbeddingProvider
from mindvault.errors import ConflictError, NotFoundError, ValidationFailed
from mindvault.jobs.registry import JobRegistry
from mindvault.logging_setup import get_logger
from mindvault.parsers.registry import ParserRegistry
from mindvault.security.files import sanitize_display_name, validate_upload
from mindvault.services.settings import SettingsService
from mindvault.vectorstore.base import VectorStore

logger = get_logger("mindvault.documents")


@dataclass
class UploadResult:
    document_id: str
    duplicate_of: str | None = None


class DocumentService:
    def __init__(
        self,
        settings: Settings,
        session_factory: sessionmaker,
        jobs: JobRegistry,
        embeddings: EmbeddingProvider,
        store: VectorStore,
        settings_svc: SettingsService,
    ) -> None:
        self.settings = settings
        self.session_factory = session_factory
        self.jobs = jobs
        self.embeddings = embeddings
        self.store = store
        self.settings_svc = settings_svc
        self.parsers = ParserRegistry()
        self.documents_dir = settings.documents_path

    # -- upload ----------------------------------------------------------
    def store_upload(
        self,
        filename: str,
        data: bytes,
        *,
        knowledge_base_id: str | None = None,
        mime_type: str | None = None,
        duplicate_ok: bool = False,
        replace_id: str | None = None,
    ) -> UploadResult:
        """Validate, persist and enqueue an uploaded document."""
        from mindvault.db.models import KnowledgeBase

        display, ext = validate_upload(
            filename,
            len(data),
            max_size=self.settings.max_upload_bytes,
            allowed_extensions=self.settings.allowed_extension_set,
        )

        # Content hashing for duplicate detection.
        content_hash = hashlib.sha256(data).hexdigest()

        with self.session_factory.begin() as session:
            existing = (
                session.execute(
                    select(Document).where(Document.content_hash == content_hash)
                )
                .scalar_one_or_none()
            )
            if existing is not None and not duplicate_ok and existing.id != replace_id:
                raise ConflictError(
                    "This document already exists.",
                    details={"existing_id": existing.id},
                    suggestion="Cancel, replace the existing document, or create a duplicate.",
                )

            if knowledge_base_id:
                kb = session.get(KnowledgeBase, knowledge_base_id)
                if kb is None:
                    raise NotFoundError(f"Knowledge base '{knowledge_base_id}' not found.")

            if replace_id:
                self._delete_document_record(replace_id)

            from mindvault.db.models import gen_id

            document_id = gen_id()
            stored_name = f"{document_id}.{ext}"
            target = self.documents_dir / stored_name
            self.documents_dir.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)

            doc = Document(
                id=document_id,
                knowledge_base_id=knowledge_base_id,
                filename=display,
                stored_name=stored_name,
                extension=ext,
                mime_type=mime_type,
                size_bytes=len(data),
                content_hash=content_hash,
                status="pending",
            )
            session.add(doc)
            session.flush()
            job = self.jobs.create("index", document_id=document_id)
            doc.last_job_id = job.id

        self.jobs.submit(job.id, lambda: self._run_index(job.id), self.jobs._executor)
        return UploadResult(document_id=document_id)

    # -- indexing --------------------------------------------------------
    def _run_index(self, job_id: str) -> None:
        job = self.jobs.get(job_id)
        document_id = job.document_id
        if document_id is None:
            self.jobs.fail(job_id, "Missing document_id.")
            return

        with self.session_factory() as session:
            doc = session.get(Document, document_id)
            if doc is None:
                self.jobs.fail(job_id, "Document was deleted while indexing.")
                return
            doc.status = "indexing"
            session.commit()

        effective = self.settings_svc.get_effective()
        spec = ChunkSpec(
            size=effective["retrieval"]["chunk_size"],
            overlap=effective["retrieval"]["chunk_overlap"],
        )

        try:
            source = self.documents_dir / doc.stored_name
            parsed = self.parsers.parse(source, doc.extension, max_pages=self.settings.max_pages)
            chunks = chunk_document(parsed, spec)

            # Clean any existing chunks (retry scenario).
            self._remove_document_vectors(document_id)

            texts = [c.text for c in chunks]
            vectors = self.embeddings.embed(texts) if texts else []
            chunk_ids = [gen_id() for _ in chunks]

            with self.session_factory.begin() as session:
                fresh = session.get(Document, document_id)
                if fresh is None:
                    raise ValidationFailed("Document was deleted while indexing.")
                for chunk, chunk_id in zip(chunks, chunk_ids, strict=False):
                    session.add(
                        DocumentChunk(
                            id=chunk_id,
                            document_id=document_id,
                            ordinal=chunk.ordinal,
                            text=chunk.text,
                            page_start=chunk.page_start,
                            page_end=chunk.page_end,
                            section=chunk.section,
                            start_char=chunk.start_char,
                            end_char=chunk.end_char,
                        )
                    )
                fresh.chunk_count = len(chunks)
                fresh.page_count = max((p.number or 1) for p in parsed.pages) if parsed.pages else None
                fresh.status = "indexed"
                fresh.error = None

            if vectors:
                self.store.add(chunk_ids, vectors)
                self.store.save()

            self.jobs.update(job_id, progress=1.0, message="Indexed")
        except Exception as exc:
            logger.error("Indexing failed for document %s: %s", document_id, exc)
            with self.session_factory.begin() as session:
                doc = session.get(Document, document_id)
                if doc is not None:
                    doc.status = "failed"
                    doc.error = str(exc)[:2000]
            raise

    def _remove_document_vectors(self, document_id: str) -> None:
        with self.session_factory.begin() as session:
            chunks = session.execute(
                select(DocumentChunk).where(DocumentChunk.document_id == document_id)
            ).scalars().all()
            ids = [c.id for c in chunks]
            for chunk in chunks:
                session.delete(chunk)
        if ids:
            self.store.remove(ids)
            self.store.save()

    def _delete_document_record(self, document_id: str) -> None:
        with self.session_factory() as session:
            doc = session.get(Document, document_id)
            if doc is None:
                raise NotFoundError(f"Document '{document_id}' not found.")
            stored = doc.stored_name
            session.delete(doc)
            session.commit()
        stored_path = self.documents_dir / stored
        if stored_path.exists():
            stored_path.unlink(missing_ok=True)
        self._remove_document_vectors(document_id)

    # -- CRUD ------------------------------------------------------------
    def delete(self, document_id: str) -> None:
        # Cancel any active indexing job for the document.
        with self.session_factory() as session:
            doc = session.get(Document, document_id)
            if doc is None:
                raise NotFoundError(f"Document '{document_id}' not found.")
            job_id = doc.last_job_id
        if job_id:
            self.jobs.cancel(job_id)
        self._delete_document_record(document_id)

    def reindex(self, document_id: str) -> str:
        with self.session_factory() as session:
            doc = session.get(Document, document_id)
            if doc is None:
                raise NotFoundError(f"Document '{document_id}' not found.")
            job = self.jobs.create("reindex", document_id=document_id)
            doc.last_job_id = job.id
            doc.status = "pending"
            doc.error = None
            session.commit()
        self.jobs.submit(job.id, lambda: self._run_index(job.id), self.jobs._executor)
        return job.id

    def rename(self, document_id: str, new_name: str) -> None:
        display = sanitize_display_name(new_name)
        with self.session_factory.begin() as session:
            doc = session.get(Document, document_id)
            if doc is None:
                raise NotFoundError(f"Document '{document_id}' not found.")
            doc.filename = display

    def _delete_all_documents(self) -> None:
        """Delete every document, its chunks, vectors and stored files."""
        with self.session_factory.begin() as session:
            doc_ids = list(session.execute(select(Document.id)).scalars().all())
            session.execute(DocumentChunk.__table__.delete())
            session.execute(Document.__table__.delete())
        if doc_ids:
            all_ids = self.store.ids()
            self.store.remove(all_ids)
            self.store.save()
        if self.documents_dir.exists():
            for file in self.documents_dir.iterdir():
                if file.is_file():
                    file.unlink(missing_ok=True)