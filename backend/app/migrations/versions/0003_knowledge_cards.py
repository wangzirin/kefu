"""knowledge cards

Revision ID: 0003_knowledge_cards
Revises: 0002_workflow_foundation
Create Date: 2026-06-25
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_knowledge_cards"
down_revision = "0002_workflow_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "knowledge_cards",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("question", sa.Text(), nullable=False, server_default=""),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("source_type", sa.String(length=40), nullable=False, server_default="manual"),
        sa.Column("source_uri", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("tags", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("aliases", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="draft"),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("updated_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_knowledge_cards_tenant_status",
        "knowledge_cards",
        ["tenant_id", "status"],
    )


def downgrade() -> None:
    op.drop_index("ix_knowledge_cards_tenant_status", table_name="knowledge_cards")
    op.drop_table("knowledge_cards")
