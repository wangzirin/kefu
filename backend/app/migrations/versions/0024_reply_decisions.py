"""reply decisions

Revision ID: 0024_reply_decisions
Revises: 0023_business_object_knowledge
Create Date: 2026-07-02
"""
from alembic import op
import sqlalchemy as sa

revision = "0024_reply_decisions"
down_revision = "0023_business_object_knowledge"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "reply_decisions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("conversation_id", sa.Integer(), sa.ForeignKey("conversations.id"), nullable=False),
        sa.Column("message_id", sa.Integer(), sa.ForeignKey("messages.id"), nullable=False),
        sa.Column("channel_id", sa.Integer(), sa.ForeignKey("channels.id"), nullable=False),
        sa.Column("business_object_id", sa.Integer(), sa.ForeignKey("business_objects.id"), nullable=True),
        sa.Column("object_knowledge_card_id", sa.Integer(), sa.ForeignKey("object_knowledge_cards.id"), nullable=True),
        sa.Column("workflow_run_id", sa.Integer(), sa.ForeignKey("workflow_runs.id"), nullable=True),
        sa.Column("state", sa.String(length=40), nullable=False, server_default="manual_gate_required"),
        sa.Column("reason", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("delivery_mode", sa.String(length=40), nullable=False, server_default="draft_only"),
        sa.Column("draft_reply", sa.Text(), nullable=False, server_default=""),
        sa.Column("matched_terms", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("decision_payload", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("external_write_allowed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("idempotency_key", sa.String(length=180), nullable=False),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("tenant_id", "idempotency_key", name="uq_reply_decisions_tenant_idempotency_key"),
    )
    op.create_index(
        "ix_reply_decisions_tenant_state_created",
        "reply_decisions",
        ["tenant_id", "state", "created_at"],
    )
    op.create_index(
        "ix_reply_decisions_conversation_message",
        "reply_decisions",
        ["conversation_id", "message_id"],
    )
    op.create_index(
        "ix_reply_decisions_object_card",
        "reply_decisions",
        ["business_object_id", "object_knowledge_card_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_reply_decisions_object_card", table_name="reply_decisions")
    op.drop_index("ix_reply_decisions_conversation_message", table_name="reply_decisions")
    op.drop_index("ix_reply_decisions_tenant_state_created", table_name="reply_decisions")
    op.drop_table("reply_decisions")
