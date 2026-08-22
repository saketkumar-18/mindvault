from __future__ import annotations

import json
import re
from typing import Any

from sqlalchemy.orm import sessionmaker

from mindvault.config import Settings
from mindvault.db.models import StudyMaterial, gen_id
from mindvault.errors import NotFoundError, ValidationFailed
from mindvault.llm.base import LLMRequest
from mindvault.llm.registry import resolve_llm
from mindvault.rag.rag_service import RAGContext, RAGService
from mindvault.services.search import ChunkMatch
from mindvault.services.settings import SettingsService

STUDY_KINDS = {
    "summary": "Generate a concise summary, key points, and topics of the document.",
    "flashcards": 'Generate flashcards. Output JSON: [{"front":"...","back":"..."}]',
    "mcq": (
        "Generate multiple-choice questions. Output JSON: "
        '[{"question":"...","options":["A)","B)","C)","D)"],"answer":"A)"}]'
    ),
    "short_answer": 'Generate short-answer questions. Output JSON: [{"question":"...","answer":"..."}]',
    "interview": "Generate interview-style questions and expected answers. Output JSON: "
    '[{"question":"...","answer":"..."}]',
    "concepts": "List the most important concepts and terms with short explanations.",
    "revision": "Create structured revision notes with headings and bullet points.",
}

SYSTEM = (
    "You are a study assistant generating material strictly from the user's document evidence provided below.\n"
    "Base every output only on the provided documents. Do not invent facts. "
    "When asked for JSON, output ONLY valid JSON."
)


def _extract_json(text: str) -> Any:
    match = re.search(r"\[.*\]|\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("No JSON found in model output.")
    return json.loads(match.group(0))


class StudyService:
    def __init__(
        self,
        settings: Settings,
        session_factory: sessionmaker,
        rag: RAGService,
        settings_svc: SettingsService,
    ) -> None:
        self.settings = settings
        self.session_factory = session_factory
        self.rag = rag
        self.settings_svc = settings_svc

    def generate(
        self,
        kind: str,
        *,
        document_id: str | None = None,
        knowledge_base_id: str | None = None,
    ) -> StudyMaterial:
        if kind not in STUDY_KINDS:
            raise ValidationFailed(f"Unknown study kind '{kind}'. Valid: {', '.join(STUDY_KINDS)}")
        if not document_id and not knowledge_base_id:
            raise ValidationFailed("Provide a document_id or knowledge_base_id.")

        resolution = resolve_llm(self.settings, self.settings_svc)
        if resolution.provider is None or resolution.status == "unavailable":
            raise NotFoundError(
                "Your local AI model is not currently available.",
            )

        # Retrieve the document's own chunks directly so the generation is
        # always grounded in its actual content.
        from sqlalchemy import select

        from mindvault.db.models import DocumentChunk

        if document_id:
            chunks = []
            with self.session_factory() as session:
                rows = (
                    session.execute(
                        select(DocumentChunk)
                        .where(DocumentChunk.document_id == document_id)
                        .order_by(DocumentChunk.ordinal)
                        .limit(200)
                    )
                    .scalars()
                    .all()
                )
                for chunk in rows:
                    chunks.append(
                        ChunkMatch(
                            chunk_id=chunk.id,
                            document_id=document_id,
                            filename=document_id,
                            score=1.0,
                            text=chunk.text,
                            page_start=chunk.page_start,
                            page_end=chunk.page_end,
                            section=chunk.section,
                        )
                    )
        else:
            chunks = self.rag.retrieve(
                "document contents overview",
                knowledge_base_id=knowledge_base_id,
            ).chunks

        if not chunks:
            raise ValidationFailed("No indexed content found to generate study material from.")

        # Pack all selected chunks into a pseudo-context.
        context = RAGContext(chunks=chunks, citations=[])
        prompt = self.rag._build_prompt(STUDY_KINDS[kind], context)
        request = LLMRequest(
            messages=[{"role": "user", "content": prompt}],
            system=SYSTEM,
            temperature=0.3,
            max_tokens=self.settings_svc.get_effective()["ai"]["max_tokens"],
        )
        text = "".join(resolution.provider.generate(request))

        # Try to parse structured JSON for list-based kinds.
        content: dict[str, Any] = {"text": text}
        if kind in ("flashcards", "mcq", "short_answer", "interview"):
            try:
                content["items"] = _extract_json(text)
            except (ValueError, json.JSONDecodeError):
                content["items"] = None
                content["parse_warning"] = "Model output was not valid JSON; showing raw text."

        title = self._title(kind, document_id, knowledge_base_id)
        with self.session_factory.begin() as session:
            material = StudyMaterial(
                id=gen_id(),
                kind=kind,
                title=title,
                content_json=json.dumps(content, ensure_ascii=False),
                document_id=document_id,
                knowledge_base_id=knowledge_base_id,
            )
            session.add(material)
            session.flush()
            return material

    def _title(self, kind: str, document_id: str | None, knowledge_base_id: str | None) -> str:
        scope = ""
        with self.session_factory() as session:
            if document_id:
                from mindvault.db.models import Document

                doc = session.get(Document, document_id)
                if doc:
                    scope = doc.filename
            elif knowledge_base_id:
                from mindvault.db.models import KnowledgeBase

                kb = session.get(KnowledgeBase, knowledge_base_id)
                if kb:
                    scope = kb.name
        return f"{kind} — {scope or 'document'}"

    def list(self) -> list[StudyMaterial]:
        with self.session_factory() as session:
            rows = session.query(StudyMaterial).order_by(StudyMaterial.created_at.desc()).all()
            return rows

    def get(self, material_id: str) -> StudyMaterial:
        with self.session_factory() as session:
            material = session.get(StudyMaterial, material_id)
            if material is None:
                raise NotFoundError(f"Study material '{material_id}' not found.")
            return material

    def delete(self, material_id: str) -> None:
        with self.session_factory.begin() as session:
            material = session.get(StudyMaterial, material_id)
            if material is None:
                raise NotFoundError(f"Study material '{material_id}' not found.")
            session.delete(material)

    # -- multi-document: comparison & resume analysis ----------------------
    def _chunks_for(self, document_ids: list[str], limit: int = 120) -> list[ChunkMatch]:
        """Load chunks for one or more documents, tagged with their filename."""
        from sqlalchemy import select

        from mindvault.db.models import Document, DocumentChunk

        chunks: list[ChunkMatch] = []
        with self.session_factory() as session:
            for doc_id in document_ids:
                doc = session.get(Document, doc_id)
                if doc is None:
                    raise NotFoundError(f"Document '{doc_id}' not found.")
                rows = (
                    session.execute(
                        select(DocumentChunk)
                        .where(DocumentChunk.document_id == doc_id)
                        .order_by(DocumentChunk.ordinal)
                        .limit(limit)
                    )
                    .scalars()
                    .all()
                )
                for chunk in rows:
                    chunks.append(
                        ChunkMatch(
                            chunk_id=chunk.id,
                            document_id=doc_id,
                            filename=doc.filename,
                            score=1.0,
                            text=chunk.text,
                            page_start=chunk.page_start,
                            page_end=chunk.page_end,
                            section=chunk.section,
                        )
                    )
        return chunks

    def _generate_raw(self, system_prompt: str, user_prompt: str) -> str:
        resolution = resolve_llm(self.settings, self.settings_svc)
        if resolution.provider is None or resolution.status == "unavailable":
            raise NotFoundError("Your local AI model is not currently available.")
        request = LLMRequest(
            messages=[{"role": "user", "content": user_prompt}],
            system=system_prompt,
            temperature=0.2,
            max_tokens=self.settings_svc.get_effective()["ai"]["max_tokens"],
        )
        return "".join(resolution.provider.generate(request))

    def compare(self, document_ids: list[str]) -> StudyMaterial:
        """Compare two or more documents: similarities, differences, gaps."""
        if len(document_ids) < 2:
            raise ValidationFailed("Select at least two documents to compare.")
        if len(document_ids) > 5:
            raise ValidationFailed("Select at most five documents to compare.")

        chunks = self._chunks_for(document_ids)
        if not chunks:
            raise ValidationFailed("No indexed content found in the selected documents.")

        context = RAGContext(chunks=chunks, citations=[])
        body = self.rag._build_prompt(
            "Compare the documents above. Identify: (1) key similarities, "
            "(2) key differences, (3) concepts present in some documents but "
            "missing in others, (4) an overall comparison summary. "
            "Clearly distinguish document evidence from your own interpretation.",
            context,
        )
        text = self._generate_raw(
            "You are an analytical assistant. Base all comparisons strictly on the provided documents. "
            "Do not invent facts. Clearly label model interpretation as interpretation.",
            body,
        )
        names = [f"Document {i + 1}" for i in range(len(document_ids))]
        title = "Comparison — " + ", ".join(names)
        content: dict[str, Any] = {"text": text, "document_ids": document_ids}
        with self.session_factory.begin() as session:
            material = StudyMaterial(
                id=gen_id(), kind="comparison", title=title,
                content_json=json.dumps(content, ensure_ascii=False),
            )
            session.add(material)
            session.flush()
            return material

    def resume_analysis(self, resume_id: str, job_description_id: str) -> StudyMaterial:
        """Resume compatibility analysis: skills, gaps, suggestions."""
        chunks = self._chunks_for([resume_id, job_description_id], limit=150)
        if not chunks:
            raise ValidationFailed("No indexed content found in the selected documents.")

        context = RAGContext(chunks=chunks, citations=[])
        body = self.rag._build_prompt(
            "This is a Resume Compatibility Analysis. Compare the resume and the job description and report: "
            "(1) skills found in the resume, (2) skills required by the job description, "
            "(3) matching skills, (4) missing skills, (5) experience alignment, "
            "(6) suggested improvements, (7) ATS-style keyword analysis (informational only; "
            "this is NOT an official ATS score). Clearly distinguish document evidence from interpretation.",
            context,
        )
        text = self._generate_raw(
            "You are a career-coach assistant. Base every finding strictly on the provided documents. "
            "Never claim an official ATS score. Label interpretation clearly.",
            body,
        )
        content: dict[str, Any] = {"text": text, "document_ids": [resume_id, job_description_id]}
        with self.session_factory.begin() as session:
            material = StudyMaterial(
                id=gen_id(), kind="resume_analysis", title="Resume Compatibility Analysis",
                content_json=json.dumps(content, ensure_ascii=False),
            )
            session.add(material)
            session.flush()
            return material