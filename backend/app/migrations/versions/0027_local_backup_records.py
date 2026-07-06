"""local backup records

Revision ID: 0027_local_backup_records
Revises: 0026_signed_update_packages
Create Date: 2026-07-03
"""
from alembic import op
import sqlalchemy as sa

revision = "0027_local_backup_records"
down_revision = "0026_signed_update_packages"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "local_backup_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("backup_id", sa.String(length=160), nullable=False),
        sa.Column("backup_type", sa.String(length=60), nullable=False, server_default="sqlite_database"),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="created"),
        sa.Column("file_name", sa.String(length=260), nullable=False),
        sa.Column("file_path", sa.String(length=800), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sha256", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("source_database_label", sa.String(length=260), nullable=False, server_default=""),
        sa.Column("source_database_hash", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("restore_mode", sa.String(length=80), nullable=False, server_default="manual_rehearsal_only"),
        sa.Column("manifest_payload", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=False, server_default=""),
        sa.UniqueConstraint("tenant_id", "backup_id", name="uq_local_backup_records_tenant_backup"),
    )
    op.create_index(
        "ix_local_backup_records_tenant_created",
        "local_backup_records",
        ["tenant_id", "created_at"],
    )
    op.create_index(
        "ix_local_backup_records_tenant_status",
        "local_backup_records",
        ["tenant_id", "status"],
    )


def downgrade() -> None:
    op.drop_index("ix_local_backup_records_tenant_status", table_name="local_backup_records")
    op.drop_index("ix_local_backup_records_tenant_created", table_name="local_backup_records")
    op.drop_table("local_backup_records")
