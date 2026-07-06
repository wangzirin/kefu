"""trusted inbound worker leases

Revision ID: 0021_inbound_worker_leases
Revises: 0020_kdoc_publications
Create Date: 2026-07-01
"""
from alembic import op
import sqlalchemy as sa

revision = "0021_inbound_worker_leases"
down_revision = "0020_kdoc_publications"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "trusted_inbound_worker_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("worker_id", sa.String(length=120), nullable=False, server_default="manual_api_worker"),
        sa.Column("mode", sa.String(length=80), nullable=False, server_default="trusted_inbound_orchestrator"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="running"),
        sa.Column("batch_size", sa.Integer(), nullable=False, server_default="20"),
        sa.Column("rate_limit_per_minute", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("lease_seconds", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("scanned", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("processed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("succeeded", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("skipped", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rate_limited", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("external_write", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("request_payload", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("result_payload", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("error_message", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_trusted_inbound_worker_runs_tenant_started",
        "trusted_inbound_worker_runs",
        ["tenant_id", "started_at"],
    )
    op.create_index(
        "ix_trusted_inbound_worker_runs_tenant_status",
        "trusted_inbound_worker_runs",
        ["tenant_id", "status"],
    )

    op.create_table(
        "trusted_inbound_message_jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("conversation_id", sa.Integer(), sa.ForeignKey("conversations.id"), nullable=False),
        sa.Column("message_id", sa.Integer(), sa.ForeignKey("messages.id"), nullable=False),
        sa.Column("idempotency_key", sa.String(length=180), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="queued"),
        sa.Column("attempts_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("locked_by", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_run_record_id", sa.Integer(), sa.ForeignKey("trusted_inbound_worker_runs.id"), nullable=True),
        sa.Column("workflow_run_id", sa.Integer(), sa.ForeignKey("workflow_runs.id"), nullable=True),
        sa.Column("human_review_task_id", sa.Integer(), sa.ForeignKey("human_review_tasks.id"), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=False, server_default=""),
        sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("tenant_id", "message_id", name="uq_trusted_inbound_message_jobs_tenant_message"),
        sa.UniqueConstraint("tenant_id", "idempotency_key", name="uq_trusted_inbound_message_jobs_tenant_key"),
    )
    op.create_index(
        "ix_trusted_inbound_message_jobs_tenant_status_locked",
        "trusted_inbound_message_jobs",
        ["tenant_id", "status", "locked_at"],
    )
    op.create_index(
        "ix_trusted_inbound_message_jobs_tenant_message",
        "trusted_inbound_message_jobs",
        ["tenant_id", "message_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_trusted_inbound_message_jobs_tenant_message", table_name="trusted_inbound_message_jobs")
    op.drop_index("ix_trusted_inbound_message_jobs_tenant_status_locked", table_name="trusted_inbound_message_jobs")
    op.drop_table("trusted_inbound_message_jobs")
    op.drop_index("ix_trusted_inbound_worker_runs_tenant_status", table_name="trusted_inbound_worker_runs")
    op.drop_index("ix_trusted_inbound_worker_runs_tenant_started", table_name="trusted_inbound_worker_runs")
    op.drop_table("trusted_inbound_worker_runs")
