"""tenant reply strategies

Revision ID: 0028_tenant_reply_strategies
Revises: 0027_local_backup_records
Create Date: 2026-07-03
"""
from alembic import op
import sqlalchemy as sa

revision = "0028_tenant_reply_strategies"
down_revision = "0027_local_backup_records"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tenant_reply_strategies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("strategy_id", sa.String(length=160), nullable=False, server_default=""),
        sa.Column("strategy_version", sa.String(length=80), nullable=False, server_default=""),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="active"),
        sa.Column("strategy_payload", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("previous_strategy_payload", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("signed_update_package_id", sa.Integer(), sa.ForeignKey("signed_update_packages.id"), nullable=True),
        sa.Column("updated_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("tenant_id", name="uq_tenant_reply_strategies_tenant"),
    )
    op.create_index(
        "ix_tenant_reply_strategies_tenant_status",
        "tenant_reply_strategies",
        ["tenant_id", "status"],
    )


def downgrade() -> None:
    op.drop_index("ix_tenant_reply_strategies_tenant_status", table_name="tenant_reply_strategies")
    op.drop_table("tenant_reply_strategies")
