"""knowledge evaluations

Revision ID: 0010_knowledge_evaluations
Revises: 0009_knowledge_documents
Create Date: 2026-06-26
"""
from alembic import op
import sqlalchemy as sa

revision = "0010_knowledge_evaluations"
down_revision = "0009_knowledge_documents"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "knowledge_evaluation_sets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="draft"),
        sa.Column("evaluation_mode", sa.String(length=60), nullable=False, server_default="document_retrieval"),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("updated_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("tenant_id", "name", name="uq_knowledge_evaluation_sets_tenant_id_name"),
    )
    op.create_index(
        "ix_knowledge_evaluation_sets_tenant_status",
        "knowledge_evaluation_sets",
        ["tenant_id", "status"],
    )

    op.create_table(
        "knowledge_evaluation_cases",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("evaluation_set_id", sa.Integer(), sa.ForeignKey("knowledge_evaluation_sets.id"), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("expected_terms", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("expected_source_uri", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("expected_document_title", sa.String(length=180), nullable=False, server_default=""),
        sa.Column("required_citation", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_knowledge_evaluation_cases_set_status",
        "knowledge_evaluation_cases",
        ["evaluation_set_id", "status"],
    )

    op.create_table(
        "knowledge_evaluation_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("evaluation_set_id", sa.Integer(), sa.ForeignKey("knowledge_evaluation_sets.id"), nullable=False),
        sa.Column("run_mode", sa.String(length=60), nullable=False, server_default="document_retrieval"),
        sa.Column("retrieval_mode", sa.String(length=80), nullable=False, server_default=""),
        sa.Column("vector_engine", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("total_cases", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("answered_cases", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("no_hit_cases", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("passed_cases", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_cases", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("needs_review_cases", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("citation_covered_cases", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("expected_term_covered_cases", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("hit_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("citation_coverage", sa.Float(), nullable=False, server_default="0"),
        sa.Column("expected_term_coverage", sa.Float(), nullable=False, server_default="0"),
        sa.Column("average_confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("unsupported_answer_rate", sa.Float(), nullable=True),
        sa.Column("summary_payload", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_knowledge_evaluation_runs_set_created",
        "knowledge_evaluation_runs",
        ["evaluation_set_id", "created_at"],
    )

    op.create_table(
        "knowledge_evaluation_run_cases",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("evaluation_run_id", sa.Integer(), sa.ForeignKey("knowledge_evaluation_runs.id"), nullable=False),
        sa.Column("evaluation_case_id", sa.Integer(), sa.ForeignKey("knowledge_evaluation_cases.id"), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("top_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("top_confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("top_chunk_id", sa.Integer(), nullable=True),
        sa.Column("top_document_id", sa.Integer(), nullable=True),
        sa.Column("citation_present", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("expected_terms_found", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("matched_terms", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("failure_reason", sa.Text(), nullable=False, server_default=""),
        sa.Column("result_payload", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_knowledge_evaluation_run_cases_run",
        "knowledge_evaluation_run_cases",
        ["evaluation_run_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_knowledge_evaluation_run_cases_run", table_name="knowledge_evaluation_run_cases")
    op.drop_table("knowledge_evaluation_run_cases")
    op.drop_index("ix_knowledge_evaluation_runs_set_created", table_name="knowledge_evaluation_runs")
    op.drop_table("knowledge_evaluation_runs")
    op.drop_index("ix_knowledge_evaluation_cases_set_status", table_name="knowledge_evaluation_cases")
    op.drop_table("knowledge_evaluation_cases")
    op.drop_index("ix_knowledge_evaluation_sets_tenant_status", table_name="knowledge_evaluation_sets")
    op.drop_table("knowledge_evaluation_sets")
