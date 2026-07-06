"""channel connectors

Revision ID: 0006_channel_connectors
Revises: 0005_outbox_send_attempts
Create Date: 2026-06-26
"""
from alembic import op
import sqlalchemy as sa

revision = "0006_channel_connectors"
down_revision = "0005_outbox_send_attempts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "channel_connectors",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("channel_id", sa.Integer(), sa.ForeignKey("channels.id"), nullable=False),
        sa.Column("provider", sa.String(length=80), nullable=False, server_default="wecom"),
        sa.Column("mode", sa.String(length=32), nullable=False, server_default="noop"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="draft"),
        sa.Column("display_name", sa.String(length=160), nullable=False, server_default=""),
        sa.Column("capabilities", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("public_config", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("webhook_path", sa.String(length=300), nullable=False, server_default=""),
        sa.Column("signature_mode", sa.String(length=80), nullable=False, server_default="not_configured"),
        sa.Column("secret_status", sa.String(length=40), nullable=False, server_default="not_configured"),
        sa.Column("external_write_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("updated_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("tenant_id", "channel_id", name="uq_channel_connectors_tenant_id_channel_id"),
    )
    op.create_index(
        "ix_channel_connectors_tenant_provider",
        "channel_connectors",
        ["tenant_id", "provider"],
    )
    op.create_index(
        "ix_channel_connectors_channel_id",
        "channel_connectors",
        ["channel_id"],
    )

    op.create_table(
        "channel_delivery_receipts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("channel_id", sa.Integer(), sa.ForeignKey("channels.id"), nullable=False),
        sa.Column("connector_id", sa.Integer(), sa.ForeignKey("channel_connectors.id"), nullable=True),
        sa.Column("matched_attempt_id", sa.Integer(), sa.ForeignKey("outbox_send_attempts.id"), nullable=True),
        sa.Column("provider", sa.String(length=80), nullable=False, server_default=""),
        sa.Column("external_message_id", sa.String(length=180), nullable=False, server_default=""),
        sa.Column("delivery_status", sa.String(length=40), nullable=False, server_default="unknown"),
        sa.Column("provider_event_id", sa.String(length=180), nullable=False, server_default=""),
        sa.Column(
            "verification_status",
            sa.String(length=60),
            nullable=False,
            server_default="not_verified_placeholder",
        ),
        sa.Column("signature_validated", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("raw_payload", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_channel_delivery_receipts_channel_id",
        "channel_delivery_receipts",
        ["channel_id"],
    )
    op.create_index(
        "ix_channel_delivery_receipts_external_message_id",
        "channel_delivery_receipts",
        ["external_message_id"],
    )
    op.create_index(
        "ix_channel_delivery_receipts_tenant_provider_status",
        "channel_delivery_receipts",
        ["tenant_id", "provider", "delivery_status"],
    )


def downgrade() -> None:
    op.drop_index("ix_channel_delivery_receipts_tenant_provider_status", table_name="channel_delivery_receipts")
    op.drop_index("ix_channel_delivery_receipts_external_message_id", table_name="channel_delivery_receipts")
    op.drop_index("ix_channel_delivery_receipts_channel_id", table_name="channel_delivery_receipts")
    op.drop_table("channel_delivery_receipts")
    op.drop_index("ix_channel_connectors_channel_id", table_name="channel_connectors")
    op.drop_index("ix_channel_connectors_tenant_provider", table_name="channel_connectors")
    op.drop_table("channel_connectors")
