"""outbox send attempts

Revision ID: 0005_outbox_send_attempts
Revises: 0004_outbox_drafts
Create Date: 2026-06-26
"""
from alembic import op
import sqlalchemy as sa

revision = "0005_outbox_send_attempts"
down_revision = "0004_outbox_drafts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "outbox_send_attempts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("outbox_draft_id", sa.Integer(), sa.ForeignKey("outbox_drafts.id"), nullable=False),
        sa.Column("conversation_id", sa.Integer(), sa.ForeignKey("conversations.id"), nullable=False),
        sa.Column("channel_id", sa.Integer(), sa.ForeignKey("channels.id"), nullable=False),
        sa.Column("contact_id", sa.Integer(), sa.ForeignKey("contacts.id"), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("delivery_mode", sa.String(length=32), nullable=False, server_default="dry_run"),
        sa.Column("provider", sa.String(length=80), nullable=False, server_default="dry_run"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="queued"),
        sa.Column("delivery_status", sa.String(length=32), nullable=False, server_default="not_sent"),
        sa.Column("idempotency_key", sa.String(length=180), nullable=False),
        sa.Column("external_message_id", sa.String(length=180), nullable=False, server_default=""),
        sa.Column("request_payload", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("response_payload", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("error_message", sa.Text(), nullable=False, server_default=""),
        sa.Column("operator_note", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("tenant_id", "idempotency_key", name="uq_outbox_send_attempts_tenant_id_idempotency_key"),
        sa.UniqueConstraint("outbox_draft_id", "attempt_number", name="uq_outbox_send_attempts_draft_attempt_number"),
    )
    op.create_index(
        "ix_outbox_send_attempts_tenant_status",
        "outbox_send_attempts",
        ["tenant_id", "status"],
    )
    op.create_index(
        "ix_outbox_send_attempts_outbox_draft_id",
        "outbox_send_attempts",
        ["outbox_draft_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_outbox_send_attempts_outbox_draft_id", table_name="outbox_send_attempts")
    op.drop_index("ix_outbox_send_attempts_tenant_status", table_name="outbox_send_attempts")
    op.drop_table("outbox_send_attempts")
