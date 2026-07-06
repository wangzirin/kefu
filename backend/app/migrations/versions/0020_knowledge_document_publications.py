"""knowledge document publications

Revision ID: 0020_kdoc_publications
Revises: 0019_sales_leads
Create Date: 2026-07-01
"""
from alembic import op
import sqlalchemy as sa

revision = "0020_kdoc_publications"
down_revision = "0019_sales_leads"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "knowledge_document_publications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("knowledge_documents.id"), nullable=False),
        sa.Column("gap_id", sa.Integer(), sa.ForeignKey("knowledge_gaps.id"), nullable=True),
        sa.Column("publication_type", sa.String(length=40), nullable=False, server_default="publish_check"),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="passed"),
        sa.Column("from_status", sa.String(length=32), nullable=False, server_default=""),
        sa.Column("to_status", sa.String(length=32), nullable=False, server_default=""),
        sa.Column("evaluation_set_id", sa.Integer(), sa.ForeignKey("knowledge_evaluation_sets.id"), nullable=True),
        sa.Column("evaluation_run_id", sa.Integer(), sa.ForeignKey("knowledge_evaluation_runs.id"), nullable=True),
        sa.Column("checked_case_ids", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("case_results", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("blocking_reasons", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("advisory_reasons", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("checks", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("document_snapshot", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("previous_publication_id", sa.Integer(), nullable=True),
        sa.Column("rollback_target_publication_id", sa.Integer(), nullable=True),
        sa.Column("rollback_reason", sa.Text(), nullable=False, server_default=""),
        sa.Column("external_write_performed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("model_call_performed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_knowledge_document_publications_tenant_document_created",
        "knowledge_document_publications",
        ["tenant_id", "document_id", "created_at"],
    )
    op.create_index(
        "ix_knowledge_document_publications_tenant_status",
        "knowledge_document_publications",
        ["tenant_id", "status"],
    )
    op.create_index(
        "ix_knowledge_document_publications_tenant_type",
        "knowledge_document_publications",
        ["tenant_id", "publication_type"],
    )


def downgrade() -> None:
    op.drop_index("ix_knowledge_document_publications_tenant_type", table_name="knowledge_document_publications")
    op.drop_index("ix_knowledge_document_publications_tenant_status", table_name="knowledge_document_publications")
    op.drop_index(
        "ix_knowledge_document_publications_tenant_document_created",
        table_name="knowledge_document_publications",
    )
    op.drop_table("knowledge_document_publications")
