"""knowledge gaps

Revision ID: 0017_knowledge_gaps
Revises: 0016_customer_eval_import
Create Date: 2026-06-30
"""
from alembic import op
import sqlalchemy as sa

revision = "0017_knowledge_gaps"
down_revision = "0016_customer_eval_import"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "knowledge_gaps",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="open"),
        sa.Column("severity", sa.String(length=32), nullable=False, server_default="medium"),
        sa.Column("source_type", sa.String(length=60), nullable=False),
        sa.Column("source_ref", sa.String(length=180), nullable=False),
        sa.Column("source_title", sa.String(length=180), nullable=False, server_default=""),
        sa.Column("source_excerpt", sa.Text(), nullable=False, server_default=""),
        sa.Column("question_excerpt", sa.Text(), nullable=False, server_default=""),
        sa.Column("gap_type", sa.String(length=80), nullable=False, server_default=""),
        sa.Column("expected_terms", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("evidence_payload", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("linked_knowledge_card_id", sa.Integer(), sa.ForeignKey("knowledge_cards.id"), nullable=True),
        sa.Column("linked_knowledge_document_id", sa.Integer(), sa.ForeignKey("knowledge_documents.id"), nullable=True),
        sa.Column("assigned_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("updated_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("resolved_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("resolution_note", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("tenant_id", "source_type", "source_ref", name="uq_knowledge_gaps_tenant_source"),
    )
    op.create_index("ix_knowledge_gaps_tenant_status", "knowledge_gaps", ["tenant_id", "status"])
    op.create_index("ix_knowledge_gaps_tenant_severity", "knowledge_gaps", ["tenant_id", "severity"])
    op.create_index("ix_knowledge_gaps_source", "knowledge_gaps", ["tenant_id", "source_type"])


def downgrade() -> None:
    op.drop_index("ix_knowledge_gaps_source", table_name="knowledge_gaps")
    op.drop_index("ix_knowledge_gaps_tenant_severity", table_name="knowledge_gaps")
    op.drop_index("ix_knowledge_gaps_tenant_status", table_name="knowledge_gaps")
    op.drop_table("knowledge_gaps")
