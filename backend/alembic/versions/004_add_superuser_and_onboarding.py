"""add superuser and onboarding fields

Revision ID: 004_add_superuser_and_onboarding
Revises: 003_add_oauth_and_api_keys
Create Date: 2026-04-22

"""

import sqlalchemy as sa

from alembic import op

revision = "004_add_superuser_and_onboarding"
down_revision = "003_add_oauth_and_api_keys"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("is_superuser", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "users",
        sa.Column("onboarding_completed_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "onboarding_completed_at")
    op.drop_column("users", "is_superuser")
