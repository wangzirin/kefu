"""channel accounts

Revision ID: 0025_channel_accounts
Revises: 0024_reply_decisions
Create Date: 2026-07-02
"""
from alembic import op
import sqlalchemy as sa

revision = "0025_channel_accounts"
down_revision = "0024_reply_decisions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "channel_accounts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("channel_id", sa.Integer(), sa.ForeignKey("channels.id"), nullable=False),
        sa.Column("connector_id", sa.Integer(), sa.ForeignKey("channel_connectors.id"), nullable=True),
        sa.Column("provider", sa.String(length=80), nullable=False, server_default=""),
        sa.Column("platform", sa.String(length=80), nullable=False, server_default=""),
        sa.Column("account_name", sa.String(length=160), nullable=False, server_default=""),
        sa.Column("external_account_id", sa.String(length=180), nullable=False, server_default=""),
        sa.Column("store_name", sa.String(length=160), nullable=False, server_default=""),
        sa.Column("entrypoint_name", sa.String(length=160), nullable=False, server_default=""),
        sa.Column("authorization_status", sa.String(length=40), nullable=False, server_default="not_configured"),
        sa.Column("access_status", sa.String(length=40), nullable=False, server_default="planned"),
        sa.Column("reply_mode", sa.String(length=40), nullable=False, server_default="draft_only"),
        sa.Column("health_status", sa.String(length=40), nullable=False, server_default="unknown"),
        sa.Column("public_profile", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("updated_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint(
            "tenant_id",
            "channel_id",
            "account_name",
            "entrypoint_name",
            name="uq_channel_accounts_tenant_channel_account_entrypoint",
        ),
    )
    op.create_index(
        "ix_channel_accounts_tenant_channel_status",
        "channel_accounts",
        ["tenant_id", "channel_id", "access_status"],
    )
    op.create_index(
        "ix_channel_accounts_tenant_provider",
        "channel_accounts",
        ["tenant_id", "provider"],
    )


def downgrade() -> None:
    op.drop_index("ix_channel_accounts_tenant_provider", table_name="channel_accounts")
    op.drop_index("ix_channel_accounts_tenant_channel_status", table_name="channel_accounts")
    op.drop_table("channel_accounts")
