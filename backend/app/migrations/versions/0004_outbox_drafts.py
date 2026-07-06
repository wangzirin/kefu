"""outbox drafts

Revision ID: 0004_outbox_drafts
Revises: 0003_knowledge_cards
Create Date: 2026-06-26
"""
from alembic import op
import sqlalchemy as sa

revision = "0004_outbox_drafts"
down_revision = "0003_knowledge_cards"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "outbox_drafts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("conversation_id", sa.Integer(), sa.ForeignKey("conversations.id"), nullable=False),
        sa.Column("channel_id", sa.Integer(), sa.ForeignKey("channels.id"), nullable=False),
        sa.Column("contact_id", sa.Integer(), sa.ForeignKey("contacts.id"), nullable=False),
        sa.Column("source_review_task_id", sa.Integer(), sa.ForeignKey("human_review_tasks.id"), nullable=True),
        sa.Column("source_workflow_run_id", sa.Integer(), sa.ForeignKey("workflow_runs.id"), nullable=True),
        sa.Column("source_message_id", sa.Integer(), sa.ForeignKey("messages.id"), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending_confirmation"),
        sa.Column("delivery_status", sa.String(length=32), nullable=False, server_default="not_sent"),
        sa.Column("reply_text", sa.Text(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=180), nullable=False),
        sa.Column("confirmation_note", sa.Text(), nullable=False, server_default=""),
        sa.Column("cancellation_reason", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("confirmed_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("canceled_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("canceled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("tenant_id", "idempotency_key", name="uq_outbox_drafts_tenant_id_idempotency_key"),
    )
    op.create_index("ix_outbox_drafts_tenant_status", "outbox_drafts", ["tenant_id", "status"])
    op.create_index("ix_outbox_drafts_conversation_id", "outbox_drafts", ["conversation_id"])
    op.create_index(
        "ix_outbox_drafts_source_review_task_id",
        "outbox_drafts",
        ["source_review_task_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_outbox_drafts_source_review_task_id", table_name="outbox_drafts")
    op.drop_index("ix_outbox_drafts_conversation_id", table_name="outbox_drafts")
    op.drop_index("ix_outbox_drafts_tenant_status", table_name="outbox_drafts")
    op.drop_table("outbox_drafts")
