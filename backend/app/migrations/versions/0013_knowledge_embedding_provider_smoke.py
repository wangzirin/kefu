"""knowledge embedding provider smoke runs

Revision ID: 0013_embedding_smoke
Revises: 0012_knowledge_pgvector
Create Date: 2026-06-26
"""
from alembic import op
import sqlalchemy as sa

revision = "0013_embedding_smoke"
down_revision = "0012_knowledge_pgvector"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "knowledge_embedding_provider_smoke_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("purpose", sa.String(length=80), nullable=False, server_default="embedding_provider_smoke"),
        sa.Column("privacy_level", sa.String(length=80), nullable=False, server_default="business_internal_no_pii"),
        sa.Column("embedding_provider", sa.String(length=80), nullable=False),
        sa.Column("embedding_model", sa.String(length=120), nullable=False),
        sa.Column("vector_engine", sa.String(length=120), nullable=False),
        sa.Column("vector_store", sa.String(length=80), nullable=False),
        sa.Column("embedding_dimension", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_dimension", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("input_text_hash", sa.String(length=80), nullable=False, server_default=""),
        sa.Column("input_character_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("estimated_input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("latency_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("pricing_input_per_1k_tokens", sa.Float(), nullable=False, server_default="0"),
        sa.Column("estimated_cost", sa.Float(), nullable=False, server_default="0"),
        sa.Column("cost_currency", sa.String(length=16), nullable=False, server_default="CNY"),
        sa.Column("provider_call_performed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("raw_text_logged", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("quality_checks", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("response_metadata", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("error_message", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_knowledge_embedding_smoke_tenant_created",
        "knowledge_embedding_provider_smoke_runs",
        ["tenant_id", "created_at"],
    )
    op.create_index(
        "ix_knowledge_embedding_smoke_provider_model",
        "knowledge_embedding_provider_smoke_runs",
        ["embedding_provider", "embedding_model"],
    )


def downgrade() -> None:
    op.drop_index("ix_knowledge_embedding_smoke_provider_model", table_name="knowledge_embedding_provider_smoke_runs")
    op.drop_index("ix_knowledge_embedding_smoke_tenant_created", table_name="knowledge_embedding_provider_smoke_runs")
    op.drop_table("knowledge_embedding_provider_smoke_runs")
