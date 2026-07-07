"""user self profile settings

Revision ID: 0033_user_self_profile_settings
Revises: 0032_pilot_facts
Create Date: 2026-07-07
"""
from alembic import op
import sqlalchemy as sa

revision = "0033_user_self_profile_settings"
down_revision = "0032_pilot_facts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("avatar_data_url", sa.Text(), nullable=False, server_default=""))
    op.add_column("users", sa.Column("public_profile", sa.JSON(), nullable=False, server_default="{}"))
    op.add_column("users", sa.Column("personal_settings", sa.JSON(), nullable=False, server_default="{}"))


def downgrade() -> None:
    op.drop_column("users", "personal_settings")
    op.drop_column("users", "public_profile")
    op.drop_column("users", "avatar_data_url")
