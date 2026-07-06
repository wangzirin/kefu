"""worker heartbeats

Revision ID: 0022_worker_heartbeats
Revises: 0021_inbound_worker_leases
Create Date: 2026-07-01
"""
from alembic import op
import sqlalchemy as sa

revision = "0022_worker_heartbeats"
down_revision = "0021_inbound_worker_leases"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "worker_heartbeats",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("worker_type", sa.String(length=80), nullable=False),
        sa.Column("worker_id", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="starting"),
        sa.Column("last_heartbeat_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_run_record_id", sa.Integer(), nullable=True),
        sa.Column("last_run_mode", sa.String(length=80), nullable=False, server_default=""),
        sa.Column("last_error", sa.Text(), nullable=False, server_default=""),
        sa.Column("loops_completed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("metadata_payload", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("tenant_id", "worker_type", "worker_id", name="uq_worker_heartbeats_tenant_worker"),
    )
    op.create_index(
        "ix_worker_heartbeats_tenant_type_status",
        "worker_heartbeats",
        ["tenant_id", "worker_type", "status"],
    )
    op.create_index(
        "ix_worker_heartbeats_tenant_heartbeat",
        "worker_heartbeats",
        ["tenant_id", "last_heartbeat_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_worker_heartbeats_tenant_heartbeat", table_name="worker_heartbeats")
    op.drop_index("ix_worker_heartbeats_tenant_type_status", table_name="worker_heartbeats")
    op.drop_table("worker_heartbeats")
