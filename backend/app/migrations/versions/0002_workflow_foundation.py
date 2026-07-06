"""workflow foundation tables

Revision ID: 0002_workflow_foundation
Revises: 0001_foundation
Create Date: 2026-06-25
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_workflow_foundation"
down_revision = "0001_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "workflow_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("conversation_id", sa.Integer(), sa.ForeignKey("conversations.id"), nullable=False),
        sa.Column("trigger_message_id", sa.Integer(), sa.ForeignKey("messages.id"), nullable=True),
        sa.Column("workflow_type", sa.String(length=80), nullable=False, server_default="customer_reply"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="running"),
        sa.Column("current_step", sa.String(length=80), nullable=False, server_default="classify_intent"),
        sa.Column("idempotency_key", sa.String(length=160), nullable=False, server_default=""),
        sa.Column("state_payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_workflow_runs_tenant_id_status", "workflow_runs", ["tenant_id", "status"])
    op.create_index(
        "ix_workflow_runs_conversation_id",
        "workflow_runs",
        ["conversation_id"],
    )

    op.create_table(
        "workflow_checkpoints",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("workflow_run_id", sa.Integer(), sa.ForeignKey("workflow_runs.id"), nullable=False),
        sa.Column("step_name", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("state_payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("input_summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("output_summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("error_message", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_workflow_checkpoints_run_id",
        "workflow_checkpoints",
        ["workflow_run_id"],
    )

    op.create_table(
        "workflow_step_attempts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("workflow_run_id", sa.Integer(), sa.ForeignKey("workflow_runs.id"), nullable=False),
        sa.Column("step_name", sa.String(length=80), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("input_summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("output_summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("error_message", sa.Text(), nullable=False, server_default=""),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_workflow_step_attempts_run_step",
        "workflow_step_attempts",
        ["workflow_run_id", "step_name"],
    )

    op.create_table(
        "human_review_tasks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("workflow_run_id", sa.Integer(), sa.ForeignKey("workflow_runs.id"), nullable=False),
        sa.Column("conversation_id", sa.Integer(), sa.ForeignKey("conversations.id"), nullable=False),
        sa.Column("message_id", sa.Integer(), sa.ForeignKey("messages.id"), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="open"),
        sa.Column("reason", sa.String(length=120), nullable=False),
        sa.Column("risk_level", sa.String(length=32), nullable=False, server_default="medium"),
        sa.Column("draft_reply", sa.Text(), nullable=False, server_default=""),
        sa.Column("final_reply", sa.Text(), nullable=False, server_default=""),
        sa.Column("assigned_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("reviewer_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("resolution_note", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_human_review_tasks_tenant_id_status",
        "human_review_tasks",
        ["tenant_id", "status"],
    )
    op.create_index(
        "ix_human_review_tasks_workflow_run_id",
        "human_review_tasks",
        ["workflow_run_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_human_review_tasks_workflow_run_id", table_name="human_review_tasks")
    op.drop_index("ix_human_review_tasks_tenant_id_status", table_name="human_review_tasks")
    op.drop_table("human_review_tasks")
    op.drop_index("ix_workflow_step_attempts_run_step", table_name="workflow_step_attempts")
    op.drop_table("workflow_step_attempts")
    op.drop_index("ix_workflow_checkpoints_run_id", table_name="workflow_checkpoints")
    op.drop_table("workflow_checkpoints")
    op.drop_index("ix_workflow_runs_conversation_id", table_name="workflow_runs")
    op.drop_index("ix_workflow_runs_tenant_id_status", table_name="workflow_runs")
    op.drop_table("workflow_runs")
