"""signed update packages

Revision ID: 0026_signed_update_packages
Revises: 0025_channel_accounts
Create Date: 2026-07-03
"""
from alembic import op
import sqlalchemy as sa

revision = "0026_signed_update_packages"
down_revision = "0025_channel_accounts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "signed_update_packages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("package_id", sa.String(length=160), nullable=False),
        sa.Column("package_name", sa.String(length=180), nullable=False),
        sa.Column("package_type", sa.String(length=40), nullable=False),
        sa.Column("package_version", sa.String(length=80), nullable=False),
        sa.Column("current_app_version", sa.String(length=80), nullable=False, server_default=""),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="staged"),
        sa.Column("package_digest_sha256", sa.String(length=64), nullable=False),
        sa.Column("package_payload", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("preflight_result", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("backup_plan", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("health_checks", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("can_apply_now", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("backup_required", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("backup_created", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("staged_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("staged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=False, server_default=""),
        sa.UniqueConstraint("tenant_id", "package_id", name="uq_signed_update_packages_tenant_package"),
    )
    op.create_index(
        "ix_signed_update_packages_tenant_status",
        "signed_update_packages",
        ["tenant_id", "status"],
    )


def downgrade() -> None:
    op.drop_index("ix_signed_update_packages_tenant_status", table_name="signed_update_packages")
    op.drop_table("signed_update_packages")
