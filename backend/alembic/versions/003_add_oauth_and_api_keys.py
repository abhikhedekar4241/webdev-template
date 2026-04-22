"""add oauth accounts and api keys

Revision ID: 003_add_oauth_and_api_keys
Revises: 002_add_email_verification
Create Date: 2026-04-22

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision = "003_add_oauth_and_api_keys"
down_revision = "002_add_email_verification"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Make hashed_password nullable (Google-only users have no password)
    op.alter_column("users", "hashed_password", nullable=True)

    # user_oauth_accounts
    op.create_table(
        "user_oauth_accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("provider_user_id", sa.String(), nullable=False),
        sa.Column("provider_email", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider", "provider_user_id", name="uq_oauth_provider_user"),
    )
    op.create_index(
        op.f("ix_user_oauth_accounts_user_id"),
        "user_oauth_accounts",
        ["user_id"],
    )
    op.create_index(
        op.f("ix_user_oauth_accounts_provider_user_id"),
        "user_oauth_accounts",
        ["provider_user_id"],
    )

    # org_api_keys
    op.create_table(
        "org_api_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("key_hash", sa.String(), nullable=False),
        sa.Column("key_prefix", sa.String(), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("last_used_at", sa.DateTime(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key_hash", name="uq_org_api_keys_key_hash"),
    )
    op.create_index(
        op.f("ix_org_api_keys_org_id"),
        "org_api_keys",
        ["org_id"],
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_org_api_keys_org_id"), table_name="org_api_keys")
    op.drop_table("org_api_keys")
    op.drop_index(
        op.f("ix_user_oauth_accounts_provider_user_id"),
        table_name="user_oauth_accounts",
    )
    op.drop_index(
        op.f("ix_user_oauth_accounts_user_id"),
        table_name="user_oauth_accounts",
    )
    op.drop_table("user_oauth_accounts")
    op.alter_column("users", "hashed_password", nullable=False)
