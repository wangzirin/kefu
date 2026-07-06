"""knowledge pgvector query path

Revision ID: 0012_knowledge_pgvector
Revises: 0011_knowledge_embedding_index
Create Date: 2026-06-26
"""
from alembic import op

revision = "0012_knowledge_pgvector"
down_revision = "0011_knowledge_embedding_index"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute(
        """
        ALTER TABLE knowledge_document_chunks
        ADD COLUMN IF NOT EXISTS embedding_pgvector vector
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_knowledge_document_chunks_pgvector_scope
        ON knowledge_document_chunks (
            tenant_id,
            status,
            vector_index_status,
            embedding_provider,
            embedding_model,
            embedding_dimension
        )
        """
    )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    op.execute("DROP INDEX IF EXISTS ix_knowledge_document_chunks_pgvector_scope")
    op.execute("ALTER TABLE knowledge_document_chunks DROP COLUMN IF EXISTS embedding_pgvector")
