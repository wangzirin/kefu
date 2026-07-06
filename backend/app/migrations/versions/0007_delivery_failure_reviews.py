"""delivery failure reviews

Revision ID: 0007_delivery_failure_reviews
Revises: 0006_channel_connectors
Create Date: 2026-06-26
"""
from alembic import op
import sqlalchemy as sa

revision = "0007_delivery_failure_reviews"
down_revision = "0006_channel_connectors"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "channel_delivery_receipts",
        sa.Column("provider_status", sa.String(length=80), nullable=False, server_default=""),
    )
    op.add_column(
        "channel_delivery_receipts",
        sa.Column("provider_error_code", sa.String(length=80), nullable=False, server_default=""),
    )
    op.add_column(
        "channel_delivery_receipts",
        sa.Column("normalized_status", sa.String(length=80), nullable=False, server_default="unknown"),
    )
    op.add_column(
        "channel_delivery_receipts",
        sa.Column("retryable", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "channel_delivery_receipts",
        sa.Column("needs_review", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "channel_delivery_receipts",
        sa.Column(
            "next_action",
            sa.String(length=120),
            nullable=False,
            server_default="manual_review_provider_status",
        ),
    )

    op.create_table(
        "delivery_failure_reviews",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("channel_id", sa.Integer(), sa.ForeignKey("channels.id"), nullable=False),
        sa.Column("connector_id", sa.Integer(), sa.ForeignKey("channel_connectors.id"), nullable=True),
        sa.Column("receipt_id", sa.Integer(), sa.ForeignKey("channel_delivery_receipts.id"), nullable=False),
        sa.Column("matched_attempt_id", sa.Integer(), sa.ForeignKey("outbox_send_attempts.id"), nullable=True),
        sa.Column("outbox_draft_id", sa.Integer(), sa.ForeignKey("outbox_drafts.id"), nullable=True),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("external_message_id", sa.String(length=180), nullable=False, server_default=""),
        sa.Column("provider_status", sa.String(length=80), nullable=False, server_default=""),
        sa.Column("provider_error_code", sa.String(length=80), nullable=False, server_default=""),
        sa.Column("normalized_status", sa.String(length=80), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False, server_default="warning"),
        sa.Column("retryable", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("review_reason", sa.String(length=120), nullable=False),
        sa.Column("next_action", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="open"),
        sa.Column("resolution_note", sa.Text(), nullable=False, server_default=""),
        sa.Column("resolved_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("receipt_id", name="uq_delivery_failure_reviews_receipt_id"),
    )
    op.create_index(
        "ix_delivery_failure_reviews_tenant_status",
        "delivery_failure_reviews",
        ["tenant_id", "status"],
    )
    op.create_index(
        "ix_delivery_failure_reviews_provider_status",
        "delivery_failure_reviews",
        ["provider", "normalized_status"],
    )


def downgrade() -> None:
    op.drop_index("ix_delivery_failure_reviews_provider_status", table_name="delivery_failure_reviews")
    op.drop_index("ix_delivery_failure_reviews_tenant_status", table_name="delivery_failure_reviews")
    op.drop_table("delivery_failure_reviews")
    op.drop_column("channel_delivery_receipts", "next_action")
    op.drop_column("channel_delivery_receipts", "needs_review")
    op.drop_column("channel_delivery_receipts", "retryable")
    op.drop_column("channel_delivery_receipts", "normalized_status")
    op.drop_column("channel_delivery_receipts", "provider_error_code")
    op.drop_column("channel_delivery_receipts", "provider_status")
