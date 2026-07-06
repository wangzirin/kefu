"""support tickets

Revision ID: 0018_support_tickets
Revises: 0017_knowledge_gaps
Create Date: 2026-06-30
"""
from alembic import op
import sqlalchemy as sa

revision = "0018_support_tickets"
down_revision = "0017_knowledge_gaps"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "support_tickets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("conversation_id", sa.Integer(), sa.ForeignKey("conversations.id"), nullable=False),
        sa.Column("channel_id", sa.Integer(), sa.ForeignKey("channels.id"), nullable=False),
        sa.Column("contact_id", sa.Integer(), sa.ForeignKey("contacts.id"), nullable=False),
        sa.Column("subject", sa.String(length=180), nullable=False, server_default=""),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="open"),
        sa.Column("priority", sa.String(length=32), nullable=False, server_default="normal"),
        sa.Column("source_type", sa.String(length=60), nullable=False, server_default="conversation"),
        sa.Column("source_ref", sa.String(length=180), nullable=False),
        sa.Column("assigned_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("assigned_team_id", sa.Integer(), sa.ForeignKey("teams.id"), nullable=True),
        sa.Column("sla_target_minutes", sa.Integer(), nullable=False, server_default="240"),
        sa.Column("sla_due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sla_status", sa.String(length=32), nullable=False, server_default="ok"),
        sa.Column("resolution_note", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("updated_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("resolved_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("tenant_id", "source_type", "source_ref", name="uq_support_tickets_tenant_source"),
    )
    op.create_index("ix_support_tickets_tenant_status", "support_tickets", ["tenant_id", "status"])
    op.create_index("ix_support_tickets_tenant_priority", "support_tickets", ["tenant_id", "priority"])
    op.create_index("ix_support_tickets_tenant_assigned", "support_tickets", ["tenant_id", "assigned_user_id"])
    op.create_index("ix_support_tickets_sla_due", "support_tickets", ["tenant_id", "sla_due_at"])


def downgrade() -> None:
    op.drop_index("ix_support_tickets_sla_due", table_name="support_tickets")
    op.drop_index("ix_support_tickets_tenant_assigned", table_name="support_tickets")
    op.drop_index("ix_support_tickets_tenant_priority", table_name="support_tickets")
    op.drop_index("ix_support_tickets_tenant_status", table_name="support_tickets")
    op.drop_table("support_tickets")
