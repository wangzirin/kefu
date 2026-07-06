"""sales leads

Revision ID: 0019_sales_leads
Revises: 0018_support_tickets
Create Date: 2026-06-30
"""
from alembic import op
import sqlalchemy as sa

revision = "0019_sales_leads"
down_revision = "0018_support_tickets"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sales_leads",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("contact_id", sa.Integer(), sa.ForeignKey("contacts.id"), nullable=False),
        sa.Column("channel_id", sa.Integer(), sa.ForeignKey("channels.id"), nullable=False),
        sa.Column("conversation_id", sa.Integer(), sa.ForeignKey("conversations.id"), nullable=True),
        sa.Column("title", sa.String(length=180), nullable=False, server_default=""),
        sa.Column("summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("stage", sa.String(length=32), nullable=False, server_default="new"),
        sa.Column("intent_level", sa.String(length=32), nullable=False, server_default="warm"),
        sa.Column("expected_budget", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("next_step", sa.Text(), nullable=False, server_default=""),
        sa.Column("owner_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("source_type", sa.String(length=60), nullable=False, server_default="conversation"),
        sa.Column("source_ref", sa.String(length=180), nullable=False),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("updated_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("next_follow_up_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("tenant_id", "source_type", "source_ref", name="uq_sales_leads_tenant_source"),
    )
    op.create_index("ix_sales_leads_tenant_stage", "sales_leads", ["tenant_id", "stage"])
    op.create_index("ix_sales_leads_tenant_intent", "sales_leads", ["tenant_id", "intent_level"])
    op.create_index("ix_sales_leads_tenant_owner", "sales_leads", ["tenant_id", "owner_user_id"])
    op.create_index("ix_sales_leads_tenant_contact", "sales_leads", ["tenant_id", "contact_id"])


def downgrade() -> None:
    op.drop_index("ix_sales_leads_tenant_contact", table_name="sales_leads")
    op.drop_index("ix_sales_leads_tenant_owner", table_name="sales_leads")
    op.drop_index("ix_sales_leads_tenant_intent", table_name="sales_leads")
    op.drop_index("ix_sales_leads_tenant_stage", table_name="sales_leads")
    op.drop_table("sales_leads")
