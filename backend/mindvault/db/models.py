from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mindvault.db.base import Base, utcnow


def gen_id() -> str:
    return uuid.uuid4().hex


class KnowledgeBase(Base):
    __tablename__ = "knowledge_bases"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=gen_id)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[Any] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[Any] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    documents: Mapped[list[Document]] = relationship(back_populates="knowledge_base")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=gen_id)
    knowledge_base_id: Mapped[str | None] = mapped_column(
        String(32), ForeignKey("knowledge_bases.id", ondelete="SET NULL"), nullable=True, index=True
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    extension: Mapped[str] = mapped_column(String(16), nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    chunk_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_job_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[Any] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[Any] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    knowledge_base: Mapped[KnowledgeBase | None] = relationship(back_populates="documents")
    chunks: Mapped[list[DocumentChunk]] = relationship(
        back_populates="document", cascade="all, delete-orphan", passive_deletes=True
    )


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=gen_id)
    document_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    page_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    section: Mapped[str | None] = mapped_column(String(512), nullable=True)
    start_char: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    end_char: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    document: Mapped[Document] = relationship(back_populates="chunks")

    __table_args__ = (Index("ix_document_chunks_doc_ord", "document_id", "ordinal"),)


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=gen_id)
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="New conversation")
    knowledge_base_id: Mapped[str | None] = mapped_column(
        String(32), ForeignKey("knowledge_bases.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[Any] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[Any] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    messages: Mapped[list[Message]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at",
        passive_deletes=True,
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=gen_id)
    conversation_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sources_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    model: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[Any] = mapped_column(DateTime(timezone=True), default=utcnow)

    conversation: Mapped[Conversation] = relationship(back_populates="messages")


class StudyMaterial(Base):
    __tablename__ = "study_materials"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=gen_id)
    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content_json: Mapped[str] = mapped_column(Text, nullable=False)
    document_id: Mapped[str | None] = mapped_column(
        String(32), ForeignKey("documents.id", ondelete="CASCADE"), nullable=True
    )
    knowledge_base_id: Mapped[str | None] = mapped_column(
        String(32), ForeignKey("knowledge_bases.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[Any] = mapped_column(DateTime(timezone=True), default=utcnow)


class AppSetting(Base):
    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    value_json: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[Any] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
