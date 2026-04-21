"""add email verification

Revision ID: 002_add_email_verification
Revises: aa41a24dbfc6
Create Date: 2026-04-21 12:00:00.000000

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision = "002_add_email_verification"
down_revision = "aa41a24dbfc6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.create_table(
        "email_verifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("otp", sa.String(length=6), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_email_verifications_user_id"),
        "email_verifications",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_email_verifications_user_id"), table_name="email_verifications")
    op.drop_table("email_verifications")
    op.drop_column("users", "is_verified")
