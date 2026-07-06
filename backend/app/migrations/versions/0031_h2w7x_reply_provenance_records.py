"""h2w7x reply provenance records

Revision ID: 0031_h2w7x_reply_provenance
Revises: 0030_diag_remediation_reqs
Create Date: 2026-07-04
"""
from alembic import op
import sqlalchemy as sa

revision = "0031_h2w7x_reply_provenance"
down_revision = "0030_diag_remediation_reqs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "reply_decisions",
        sa.Column("provenance_id", sa.String(length=180), nullable=False, server_default=""),
    )
    op.create_index(
        "ix_reply_decisions_tenant_provenance",
        "reply_decisions",
        ["tenant_id", "provenance_id"],
    )

    op.create_table(
        "model_call_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("channel_id", sa.Integer(), sa.ForeignKey("channels.id"), nullable=True),
        sa.Column("conversation_id", sa.Integer(), sa.ForeignKey("conversations.id"), nullable=True),
        sa.Column("message_id", sa.Integer(), sa.ForeignKey("messages.id"), nullable=True),
        sa.Column("workflow_run_id", sa.Integer(), sa.ForeignKey("workflow_runs.id"), nullable=True),
        sa.Column("reply_decision_id", sa.Integer(), sa.ForeignKey("reply_decisions.id"), nullable=True),
        sa.Column("outbox_draft_id", sa.Integer(), sa.ForeignKey("outbox_drafts.id"), nullable=True),
        sa.Column("evaluation_run_case_id", sa.Integer(), sa.ForeignKey("knowledge_evaluation_run_cases.id"), nullable=True),
        sa.Column("provenance_id", sa.String(length=180), nullable=False, server_default=""),
        sa.Column("request_id", sa.String(length=180), nullable=False, server_default=""),
        sa.Column("idempotency_key", sa.String(length=180), nullable=False),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("model", sa.String(length=160), nullable=False),
        sa.Column("route_name", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("target_model_tier", sa.String(length=40), nullable=False, server_default=""),
        sa.Column("complexity", sa.String(length=40), nullable=False, server_default=""),
        sa.Column("status", sa.String(length=40), nullable=False, server_default=""),
        sa.Column("error_code", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("input_units", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_units", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_units", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("unit_type", sa.String(length=20), nullable=False, server_default="chars"),
        sa.Column("latency_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("estimated_cost", sa.Float(), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(length=20), nullable=False, server_default="CNY"),
        sa.Column("pricing_source", sa.String(length=160), nullable=False, server_default=""),
        sa.Column("pricing_version", sa.String(length=80), nullable=False, server_default=""),
        sa.Column("budget_policy_snapshot", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("degrade_action", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("raw_text_logged", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("metadata_payload", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("tenant_id", "idempotency_key", name="uq_model_call_records_tenant_idempotency_key"),
    )
    op.create_index("ix_model_call_records_tenant_created", "model_call_records", ["tenant_id", "created_at"])
    op.create_index("ix_model_call_records_tenant_provenance", "model_call_records", ["tenant_id", "provenance_id"])
    op.create_index("ix_model_call_records_tenant_provider_model", "model_call_records", ["tenant_id", "provider", "model"])

    op.create_table(
        "reply_citation_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("provenance_id", sa.String(length=180), nullable=False, server_default=""),
        sa.Column("reply_decision_id", sa.Integer(), sa.ForeignKey("reply_decisions.id"), nullable=True),
        sa.Column("workflow_run_id", sa.Integer(), sa.ForeignKey("workflow_runs.id"), nullable=True),
        sa.Column("outbox_draft_id", sa.Integer(), sa.ForeignKey("outbox_drafts.id"), nullable=True),
        sa.Column("evaluation_run_case_id", sa.Integer(), sa.ForeignKey("knowledge_evaluation_run_cases.id"), nullable=True),
        sa.Column("source_kind", sa.String(length=60), nullable=False, server_default=""),
        sa.Column("knowledge_card_id", sa.Integer(), sa.ForeignKey("knowledge_cards.id"), nullable=True),
        sa.Column("object_knowledge_card_id", sa.Integer(), sa.ForeignKey("object_knowledge_cards.id"), nullable=True),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("knowledge_documents.id"), nullable=True),
        sa.Column("document_chunk_id", sa.Integer(), sa.ForeignKey("knowledge_document_chunks.id"), nullable=True),
        sa.Column("chunk_index", sa.Integer(), nullable=True),
        sa.Column("source_version", sa.String(length=80), nullable=False, server_default=""),
        sa.Column("content_hash", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("source_uri", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("char_start", sa.Integer(), nullable=True),
        sa.Column("char_end", sa.Integer(), nullable=True),
        sa.Column("score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("no_citation_reason", sa.Text(), nullable=False, server_default=""),
        sa.Column("citation_payload", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_reply_citation_snapshots_tenant_provenance",
        "reply_citation_snapshots",
        ["tenant_id", "provenance_id"],
    )
    op.create_index(
        "ix_reply_citation_snapshots_tenant_source",
        "reply_citation_snapshots",
        ["tenant_id", "source_kind"],
    )


def downgrade() -> None:
    op.drop_index("ix_reply_citation_snapshots_tenant_source", table_name="reply_citation_snapshots")
    op.drop_index("ix_reply_citation_snapshots_tenant_provenance", table_name="reply_citation_snapshots")
    op.drop_table("reply_citation_snapshots")

    op.drop_index("ix_model_call_records_tenant_provider_model", table_name="model_call_records")
    op.drop_index("ix_model_call_records_tenant_provenance", table_name="model_call_records")
    op.drop_index("ix_model_call_records_tenant_created", table_name="model_call_records")
    op.drop_table("model_call_records")

    op.drop_index("ix_reply_decisions_tenant_provenance", table_name="reply_decisions")
    op.drop_column("reply_decisions", "provenance_id")
