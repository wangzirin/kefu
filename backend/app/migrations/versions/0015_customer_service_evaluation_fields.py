"""customer service evaluation fields

Revision ID: 0015_customer_service_eval
Revises: 0014_vector_index_plan
Create Date: 2026-06-26
"""
import sqlalchemy as sa
from alembic import op

revision = "0015_customer_service_eval"
down_revision = "0014_vector_index_plan"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "knowledge_evaluation_cases",
        sa.Column(
            "question_type",
            sa.String(length=80),
            nullable=False,
            server_default="standard_customer_question",
        ),
    )
    op.add_column(
        "knowledge_evaluation_cases",
        sa.Column("expected_chunk_ids", sa.JSON(), nullable=False, server_default="[]"),
    )
    op.add_column(
        "knowledge_evaluation_cases",
        sa.Column("must_have_all_evidence", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "knowledge_evaluation_cases",
        sa.Column("expected_human_review", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "knowledge_evaluation_cases",
        sa.Column("allow_auto_reply", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column(
        "knowledge_evaluation_cases",
        sa.Column("forbidden_terms", sa.JSON(), nullable=False, server_default="[]"),
    )
    op.add_column(
        "knowledge_evaluation_cases",
        sa.Column("risk_level", sa.String(length=32), nullable=False, server_default="low"),
    )


def downgrade() -> None:
    op.drop_column("knowledge_evaluation_cases", "risk_level")
    op.drop_column("knowledge_evaluation_cases", "forbidden_terms")
    op.drop_column("knowledge_evaluation_cases", "allow_auto_reply")
    op.drop_column("knowledge_evaluation_cases", "expected_human_review")
    op.drop_column("knowledge_evaluation_cases", "must_have_all_evidence")
    op.drop_column("knowledge_evaluation_cases", "expected_chunk_ids")
    op.drop_column("knowledge_evaluation_cases", "question_type")
