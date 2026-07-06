"""knowledge documents

Revision ID: 0009_knowledge_documents
Revises: 0008_outbox_delivery_jobs
Create Date: 2026-06-26
"""
from alembic import op
import sqlalchemy as sa

revision = "0009_knowledge_documents"
down_revision = "0008_outbox_delivery_jobs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "knowledge_documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("source_type", sa.String(length=40), nullable=False, server_default="manual_document"),
        sa.Column("source_uri", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(length=80), nullable=False, server_default=""),
        sa.Column("tags", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="draft"),
        sa.Column("ingestion_status", sa.String(length=40), nullable=False, server_default="indexed"),
        sa.Column("chunk_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("updated_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_knowledge_documents_tenant_status", "knowledge_documents", ["tenant_id", "status"])

    op.create_table(
        "knowledge_document_chunks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("knowledge_documents.id"), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("section_title", sa.String(length=180), nullable=False, server_default=""),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(length=80), nullable=False, server_default=""),
        sa.Column("source_uri", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("char_start", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("char_end", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("token_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("embedding_signature", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("document_id", "chunk_index", name="uq_knowledge_document_chunks_document_id_chunk_index"),
    )
    op.create_index(
        "ix_knowledge_document_chunks_tenant_status",
        "knowledge_document_chunks",
        ["tenant_id", "status"],
    )
    op.create_index(
        "ix_knowledge_document_chunks_document",
        "knowledge_document_chunks",
        ["document_id", "chunk_index"],
    )


def downgrade() -> None:
    op.drop_index("ix_knowledge_document_chunks_document", table_name="knowledge_document_chunks")
    op.drop_index("ix_knowledge_document_chunks_tenant_status", table_name="knowledge_document_chunks")
    op.drop_table("knowledge_document_chunks")
    op.drop_index("ix_knowledge_documents_tenant_status", table_name="knowledge_documents")
    op.drop_table("knowledge_documents")
