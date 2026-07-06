"""pilot facts and material batches

Revision ID: 0032_pilot_facts
Revises: 0031_h2w7x_reply_provenance
Create Date: 2026-07-05
"""
from alembic import op
import sqlalchemy as sa

revision = "0032_pilot_facts"
down_revision = "0031_h2w7x_reply_provenance"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pilot_readiness_facts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("fact_key", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=80), nullable=False),
        sa.Column("source", sa.String(length=80), nullable=False, server_default="database"),
        sa.Column("evidence_path", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("payload", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("not_ready_for", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("tenant_id", "fact_key", name="uq_pilot_readiness_facts_tenant_key"),
    )
    op.create_index("ix_pilot_readiness_facts_tenant_status", "pilot_readiness_facts", ["tenant_id", "status"])

    op.create_table(
        "customer_material_batches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("batch_code", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=80), nullable=False),
        sa.Column("material_sha256", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("question_sha256", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("manifest_sha256", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("material_row_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("question_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("record_type_coverage", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("question_action_coverage", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("blocker_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("desensitization_risk_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("manifest_summary", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("tenant_id", "batch_code", name="uq_customer_material_batches_tenant_code"),
    )
    op.create_index("ix_customer_material_batches_tenant_created", "customer_material_batches", ["tenant_id", "created_at"])
    op.create_index("ix_customer_material_batches_tenant_status", "customer_material_batches", ["tenant_id", "status"])


def downgrade() -> None:
    op.drop_index("ix_customer_material_batches_tenant_status", table_name="customer_material_batches")
    op.drop_index("ix_customer_material_batches_tenant_created", table_name="customer_material_batches")
    op.drop_table("customer_material_batches")

    op.drop_index("ix_pilot_readiness_facts_tenant_status", table_name="pilot_readiness_facts")
    op.drop_table("pilot_readiness_facts")
