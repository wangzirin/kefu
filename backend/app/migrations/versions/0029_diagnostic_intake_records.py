"""diagnostic intake records

Revision ID: 0029_diagnostic_intake_records
Revises: 0028_tenant_reply_strategies
Create Date: 2026-07-03
"""
from alembic import op
import sqlalchemy as sa

revision = "0029_diagnostic_intake_records"
down_revision = "0028_tenant_reply_strategies"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "diagnostic_intake_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("intake_id", sa.String(length=180), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="received"),
        sa.Column("validation_status", sa.String(length=40), nullable=False, server_default="passed"),
        sa.Column("package_filename", sa.String(length=260), nullable=False, server_default=""),
        sa.Column("diagnostic_bundle_filename", sa.String(length=260), nullable=False, server_default=""),
        sa.Column("package_sha256", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("diagnostic_bundle_sha256", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("package_size_bytes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("source_channel", sa.String(length=80), nullable=False, server_default="manual_transfer"),
        sa.Column("rejection_reason", sa.Text(), nullable=False, server_default=""),
        sa.Column("processing_note", sa.Text(), nullable=False, server_default=""),
        sa.Column("authorization_summary", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("safety", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("package_payload", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("received_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("handled_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("handled_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("tenant_id", "intake_id", name="uq_diagnostic_intake_records_tenant_intake"),
    )
    op.create_index(
        "ix_diagnostic_intake_records_tenant_status",
        "diagnostic_intake_records",
        ["tenant_id", "status"],
    )
    op.create_index(
        "ix_diagnostic_intake_records_tenant_created",
        "diagnostic_intake_records",
        ["tenant_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_diagnostic_intake_records_tenant_created", table_name="diagnostic_intake_records")
    op.drop_index("ix_diagnostic_intake_records_tenant_status", table_name="diagnostic_intake_records")
    op.drop_table("diagnostic_intake_records")
