"""knowledge vector index plans

Revision ID: 0014_vector_index_plan
Revises: 0013_embedding_smoke
Create Date: 2026-06-26
"""
import sqlalchemy as sa
from alembic import op

revision = "0014_vector_index_plan"
down_revision = "0013_embedding_smoke"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "knowledge_vector_index_plans",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("knowledge_documents.id"), nullable=True),
        sa.Column("status_filter", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("plan_status", sa.String(length=32), nullable=False, server_default="planned"),
        sa.Column("requested_strategy", sa.String(length=40), nullable=False, server_default="auto"),
        sa.Column("selected_strategy", sa.String(length=80), nullable=False, server_default=""),
        sa.Column("index_method", sa.String(length=40), nullable=False, server_default="none"),
        sa.Column("index_name", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("vector_store", sa.String(length=80), nullable=False, server_default=""),
        sa.Column("retrieval_backend", sa.String(length=80), nullable=False, server_default=""),
        sa.Column("embedding_provider", sa.String(length=80), nullable=False, server_default=""),
        sa.Column("embedding_model", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("embedding_dimension", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("target_chunk_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("estimated_build_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("estimated_memory_mb", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("maintenance_window", sa.String(length=80), nullable=False, server_default="off_peak"),
        sa.Column("maintenance_window_required", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("dry_run", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("execute_performed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("concurrent_build", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("ddl_statements", sa.JSON(), nullable=False),
        sa.Column("rollback_statements", sa.JSON(), nullable=False),
        sa.Column("safety_checks", sa.JSON(), nullable=False),
        sa.Column("recommendation_reasons", sa.JSON(), nullable=False),
        sa.Column("query_options", sa.JSON(), nullable=False),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_knowledge_vector_index_plans_tenant_created",
        "knowledge_vector_index_plans",
        ["tenant_id", "created_at"],
    )
    op.create_index(
        "ix_knowledge_vector_index_plans_strategy",
        "knowledge_vector_index_plans",
        ["tenant_id", "selected_strategy", "plan_status"],
    )


def downgrade() -> None:
    op.drop_index("ix_knowledge_vector_index_plans_strategy", table_name="knowledge_vector_index_plans")
    op.drop_index("ix_knowledge_vector_index_plans_tenant_created", table_name="knowledge_vector_index_plans")
    op.drop_table("knowledge_vector_index_plans")
