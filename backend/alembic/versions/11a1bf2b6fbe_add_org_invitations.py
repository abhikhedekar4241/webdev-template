"""add org invitations

Revision ID: 11a1bf2b6fbe
Revises: 001_add_orgs
Create Date: 2026-04-21 06:47:12.558988

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "11a1bf2b6fbe"
down_revision: str | None = "001_add_orgs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "org_invitations",
        sa.Column("id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("org_id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("invited_email", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column(
            "role", sa.Enum("owner", "admin", "member", name="orgrole"), nullable=False
        ),
        sa.Column("invited_by", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("pending", "accepted", "declined", name="invitationstatus"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["invited_by"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["org_id"],
            ["organizations.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_org_invitations_invited_email"),
        "org_invitations",
        ["invited_email"],
        unique=False,
    )
    op.create_index(
        op.f("ix_org_invitations_org_id"), "org_invitations", ["org_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_org_invitations_org_id"), table_name="org_invitations")
    op.drop_index(
        op.f("ix_org_invitations_invited_email"), table_name="org_invitations"
    )
    op.drop_table("org_invitations")
