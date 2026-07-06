"""diagnostic remediation requests

Revision ID: 0030_diag_remediation_reqs
Revises: 0029_diagnostic_intake_records
Create Date: 2026-07-03
"""
from alembic import op
import sqlalchemy as sa

revision = "0030_diag_remediation_reqs"
down_revision = "0029_diagnostic_intake_records"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "diagnostic_remediation_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("intake_record_id", sa.Integer(), sa.ForeignKey("diagnostic_intake_records.id"), nullable=False),
        sa.Column("request_id", sa.String(length=180), nullable=False),
        sa.Column("request_type", sa.String(length=60), nullable=False, server_default="knowledge_or_strategy_update"),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="draft"),
        sa.Column("priority", sa.String(length=30), nullable=False, server_default="normal"),
        sa.Column("title", sa.String(length=220), nullable=False, server_default=""),
        sa.Column("summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("recommended_actions", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("update_request_manifest", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("safety", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("updated_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("tenant_id", "request_id", name="uq_diagnostic_remediation_requests_tenant_request"),
    )
    op.create_index(
        "ix_diagnostic_remediation_requests_tenant_status",
        "diagnostic_remediation_requests",
        ["tenant_id", "status"],
    )
    op.create_index(
        "ix_diagnostic_remediation_requests_tenant_created",
        "diagnostic_remediation_requests",
        ["tenant_id", "created_at"],
    )
    op.create_index(
        "ix_diagnostic_remediation_requests_intake",
        "diagnostic_remediation_requests",
        ["intake_record_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_diagnostic_remediation_requests_intake", table_name="diagnostic_remediation_requests")
    op.drop_index("ix_diagnostic_remediation_requests_tenant_created", table_name="diagnostic_remediation_requests")
    op.drop_index("ix_diagnostic_remediation_requests_tenant_status", table_name="diagnostic_remediation_requests")
    op.drop_table("diagnostic_remediation_requests")
