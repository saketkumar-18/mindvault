"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-01-01
"""

import sqlalchemy as sa
from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "knowledge_bases",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("name", name="uq_knowledge_bases_name"),
    )

    op.create_table(
        "documents",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column(
            "knowledge_base_id",
            sa.String(length=32),
            sa.ForeignKey("knowledge_bases.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("stored_name", sa.String(length=255), nullable=False),
        sa.Column("extension", sa.String(length=16), nullable=False),
        sa.Column("mime_type", sa.String(length=128), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("page_count", sa.Integer(), nullable=True),
        sa.Column("chunk_count", sa.Integer(), nullable=False),
        sa.Column("last_job_id", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("stored_name", name="uq_documents_stored_name"),
    )
    op.create_index("ix_documents_knowledge_base_id", "documents", ["knowledge_base_id"])
    op.create_index("ix_documents_content_hash", "documents", ["content_hash"])

    op.create_table(
        "document_chunks",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column(
            "document_id",
            sa.String(length=32),
            sa.ForeignKey("documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("page_start", sa.Integer(), nullable=True),
        sa.Column("page_end", sa.Integer(), nullable=True),
        sa.Column("section", sa.String(length=512), nullable=True),
        sa.Column("start_char", sa.Integer(), nullable=False),
        sa.Column("end_char", sa.Integer(), nullable=False),
    )
    op.create_index("ix_document_chunks_document_id", "document_chunks", ["document_id"])
    op.create_index("ix_document_chunks_doc_ord", "document_chunks", ["document_id", "ordinal"])

    op.create_table(
        "conversations",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column(
            "knowledge_base_id",
            sa.String(length=32),
            sa.ForeignKey("knowledge_bases.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "messages",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column(
            "conversation_id",
            sa.String(length=32),
            sa.ForeignKey("conversations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("sources_json", sa.Text(), nullable=True),
        sa.Column("model", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"])

    op.create_table(
        "study_materials",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("kind", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("content_json", sa.Text(), nullable=False),
        sa.Column(
            "document_id",
            sa.String(length=32),
            sa.ForeignKey("documents.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "knowledge_base_id",
            sa.String(length=32),
            sa.ForeignKey("knowledge_bases.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "app_settings",
        sa.Column("key", sa.String(length=128), primary_key=True),
        sa.Column("value_json", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("app_settings")
    op.drop_table("study_materials")
    op.drop_table("messages")
    op.drop_table("conversations")
    op.drop_table("document_chunks")
    op.drop_table("documents")
    op.drop_table("knowledge_bases")
