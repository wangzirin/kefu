"""knowledge embedding index metadata

Revision ID: 0011_knowledge_embedding_index
Revises: 0010_knowledge_evaluations
Create Date: 2026-06-26
"""
from alembic import op
import sqlalchemy as sa

revision = "0011_knowledge_embedding_index"
down_revision = "0010_knowledge_evaluations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.add_column(
        "knowledge_document_chunks",
        sa.Column("embedding_vector", sa.JSON(), nullable=False, server_default="[]"),
    )
    op.add_column(
        "knowledge_document_chunks",
        sa.Column("embedding_provider", sa.String(length=80), nullable=False, server_default="deterministic_local"),
    )
    op.add_column(
        "knowledge_document_chunks",
        sa.Column(
            "embedding_model",
            sa.String(length=120),
            nullable=False,
            server_default="deterministic-token-vector-v1",
        ),
    )
    op.add_column(
        "knowledge_document_chunks",
        sa.Column("embedding_dimension", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "knowledge_document_chunks",
        sa.Column("vector_store", sa.String(length=80), nullable=False, server_default="sqlite_json_vector_store"),
    )
    op.add_column(
        "knowledge_document_chunks",
        sa.Column("vector_index_status", sa.String(length=40), nullable=False, server_default="indexed"),
    )
    op.create_index(
        "ix_knowledge_document_chunks_vector_status",
        "knowledge_document_chunks",
        ["tenant_id", "status", "vector_index_status"],
    )
    op.create_index(
        "ix_knowledge_document_chunks_embedding_provider",
        "knowledge_document_chunks",
        ["embedding_provider", "embedding_model"],
    )


def downgrade() -> None:
    op.drop_index("ix_knowledge_document_chunks_embedding_provider", table_name="knowledge_document_chunks")
    op.drop_index("ix_knowledge_document_chunks_vector_status", table_name="knowledge_document_chunks")
    op.drop_column("knowledge_document_chunks", "vector_index_status")
    op.drop_column("knowledge_document_chunks", "vector_store")
    op.drop_column("knowledge_document_chunks", "embedding_dimension")
    op.drop_column("knowledge_document_chunks", "embedding_model")
    op.drop_column("knowledge_document_chunks", "embedding_provider")
    op.drop_column("knowledge_document_chunks", "embedding_vector")
