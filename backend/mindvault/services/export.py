from __future__ import annotations

import json
import zipfile
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from mindvault.db.models import Document, KnowledgeBase
from mindvault.errors import NotFoundError
from mindvault.security.files import resolve_under


class ExportService:
    """Data export so users always own their data (portable JSON)."""

    def __init__(self, session_factory: sessionmaker, documents_dir: Path) -> None:
        self.session_factory = session_factory
        self.documents_dir = documents_dir

    def conversations_json(self) -> dict[str, object]:
        from mindvault.db.models import Conversation

        with self.session_factory() as session:
            convs = session.execute(select(Conversation).order_by(Conversation.created_at)).scalars().all()
            result = []
            for conv in convs:
                result.append(
                    {
                        "id": conv.id,
                        "title": conv.title,
                        "knowledge_base_id": conv.knowledge_base_id,
                        "created_at": conv.created_at.isoformat() if conv.created_at else None,
                        "messages": [
                            {
                                "id": m.id,
                                "role": m.role,
                                "content": m.content,
                                "sources": json.loads(m.sources_json) if m.sources_json else None,
                                "model": m.model,
                                "created_at": m.created_at.isoformat() if m.created_at else None,
                            }
                            for m in conv.messages
                        ],
                    }
                )
            return {"exported_at": datetime.now(UTC).isoformat(), "conversations": result}

    def knowledge_bases_json(self) -> dict[str, object]:
        with self.session_factory() as session:
            kbs = session.execute(select(KnowledgeBase).order_by(KnowledgeBase.name)).scalars().all()
            result = []
            for kb in kbs:
                result.append(
                    {
                        "id": kb.id,
                        "name": kb.name,
                        "description": kb.description,
                        "documents": [
                            {
                                "id": d.id,
                                "filename": d.filename,
                                "extension": d.extension,
                                "size_bytes": d.size_bytes,
                                "status": d.status,
                                "created_at": d.created_at.isoformat() if d.created_at else None,
                            }
                            for d in kb.documents
                        ],
                    }
                )
            return {"exported_at": datetime.now(UTC).isoformat(), "knowledge_bases": result}

    def download_document(self, document_id: str) -> tuple[bytes, str]:
        with self.session_factory() as session:
            doc = session.get(Document, document_id)
            if doc is None:
                raise NotFoundError(f"Document '{document_id}' not found.")
            path = resolve_under(self.documents_dir, doc.stored_name)
        if not path.exists():
            raise NotFoundError("Document file is missing from storage.")
        return path.read_bytes(), doc.filename

    def all_data_zip(self) -> BytesIO:
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("conversations.json", json.dumps(self.conversations_json(), indent=2, ensure_ascii=False))
            zf.writestr("knowledge_bases.json", json.dumps(self.knowledge_bases_json(), indent=2, ensure_ascii=False))
        buffer.seek(0)
        return buffer