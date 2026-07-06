"""outbox delivery jobs

Revision ID: 0008_outbox_delivery_jobs
Revises: 0007_delivery_failure_reviews
Create Date: 2026-06-26
"""
from alembic import op
import sqlalchemy as sa

revision = "0008_outbox_delivery_jobs"
down_revision = "0007_delivery_failure_reviews"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "outbox_delivery_jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("outbox_draft_id", sa.Integer(), sa.ForeignKey("outbox_drafts.id"), nullable=False),
        sa.Column("channel_id", sa.Integer(), sa.ForeignKey("channels.id"), nullable=False),
        sa.Column("connector_id", sa.Integer(), sa.ForeignKey("channel_connectors.id"), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="queued"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("attempts_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("locked_by", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("idempotency_key", sa.String(length=180), nullable=False),
        sa.Column("external_write_requested", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("external_write_permitted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("last_attempt_id", sa.Integer(), sa.ForeignKey("outbox_send_attempts.id"), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=False, server_default=""),
        sa.Column("dead_letter_reason", sa.String(length=160), nullable=False, server_default=""),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("tenant_id", "idempotency_key", name="uq_outbox_delivery_jobs_tenant_id_idempotency_key"),
    )
    op.create_index(
        "ix_outbox_delivery_jobs_tenant_status_next_run",
        "outbox_delivery_jobs",
        ["tenant_id", "status", "next_run_at"],
    )
    op.create_index(
        "ix_outbox_delivery_jobs_outbox_draft",
        "outbox_delivery_jobs",
        ["outbox_draft_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_outbox_delivery_jobs_outbox_draft", table_name="outbox_delivery_jobs")
    op.drop_index("ix_outbox_delivery_jobs_tenant_status_next_run", table_name="outbox_delivery_jobs")
    op.drop_table("outbox_delivery_jobs")
