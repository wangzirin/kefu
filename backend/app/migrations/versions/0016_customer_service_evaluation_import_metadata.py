"""customer service evaluation import metadata

Revision ID: 0016_customer_eval_import
Revises: 0015_customer_service_eval
Create Date: 2026-06-26
"""
import sqlalchemy as sa
from alembic import op

revision = "0016_customer_eval_import"
down_revision = "0015_customer_service_eval"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "knowledge_evaluation_cases",
        sa.Column("external_case_id", sa.String(length=120), nullable=False, server_default=""),
    )
    op.add_column(
        "knowledge_evaluation_cases",
        sa.Column("source_channel", sa.String(length=80), nullable=False, server_default=""),
    )
    op.add_column(
        "knowledge_evaluation_cases",
        sa.Column("source_category", sa.String(length=120), nullable=False, server_default=""),
    )
    op.add_column(
        "knowledge_evaluation_cases",
        sa.Column("annotation_notes", sa.Text(), nullable=False, server_default=""),
    )


def downgrade() -> None:
    op.drop_column("knowledge_evaluation_cases", "annotation_notes")
    op.drop_column("knowledge_evaluation_cases", "source_category")
    op.drop_column("knowledge_evaluation_cases", "source_channel")
    op.drop_column("knowledge_evaluation_cases", "external_case_id")
