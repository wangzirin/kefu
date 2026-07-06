"""business object knowledge

Revision ID: 0023_business_object_knowledge
Revises: 0022_worker_heartbeats
Create Date: 2026-07-02
"""
from alembic import op
import sqlalchemy as sa

revision = "0023_business_object_knowledge"
down_revision = "0022_worker_heartbeats"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "business_objects",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("type", sa.String(length=40), nullable=False),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("external_id", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("attrs_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("updated_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_business_objects_tenant_type_status",
        "business_objects",
        ["tenant_id", "type", "status"],
    )
    op.create_index("ix_business_objects_tenant_title", "business_objects", ["tenant_id", "title"])

    op.create_table(
        "business_object_aliases",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("business_object_id", sa.Integer(), sa.ForeignKey("business_objects.id"), nullable=False),
        sa.Column("alias", sa.String(length=180), nullable=False),
        sa.Column("channel_scope", sa.String(length=80), nullable=False, server_default="all"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint(
            "business_object_id",
            "alias",
            "channel_scope",
            name="uq_business_object_aliases_object_alias_scope",
        ),
    )
    op.create_index(
        "ix_business_object_aliases_tenant_alias",
        "business_object_aliases",
        ["tenant_id", "alias"],
    )

    op.create_table(
        "object_knowledge_cards",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("business_object_id", sa.Integer(), sa.ForeignKey("business_objects.id"), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("trigger_keywords", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("media_refs", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("scope", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("source", sa.String(length=120), nullable=False, server_default="manual"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("updated_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_object_knowledge_cards_object_status",
        "object_knowledge_cards",
        ["business_object_id", "status"],
    )
    op.create_index(
        "ix_object_knowledge_cards_tenant_status",
        "object_knowledge_cards",
        ["tenant_id", "status"],
    )

    op.create_table(
        "knowledge_import_batches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("source_file_ref", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("object_type", sa.String(length=40), nullable=False, server_default=""),
        sa.Column("row_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("valid_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="draft"),
        sa.Column("result_payload", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_knowledge_import_batches_tenant_status",
        "knowledge_import_batches",
        ["tenant_id", "status"],
    )


def downgrade() -> None:
    op.drop_index("ix_knowledge_import_batches_tenant_status", table_name="knowledge_import_batches")
    op.drop_table("knowledge_import_batches")
    op.drop_index("ix_object_knowledge_cards_tenant_status", table_name="object_knowledge_cards")
    op.drop_index("ix_object_knowledge_cards_object_status", table_name="object_knowledge_cards")
    op.drop_table("object_knowledge_cards")
    op.drop_index("ix_business_object_aliases_tenant_alias", table_name="business_object_aliases")
    op.drop_table("business_object_aliases")
    op.drop_index("ix_business_objects_tenant_title", table_name="business_objects")
    op.drop_index("ix_business_objects_tenant_type_status", table_name="business_objects")
    op.drop_table("business_objects")
