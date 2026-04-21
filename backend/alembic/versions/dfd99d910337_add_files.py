"""add files

Revision ID: dfd99d910337
Revises: 11a1bf2b6fbe
Create Date: 2026-04-21 07:53:06.067549

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel  # noqa: F401

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "dfd99d910337"
down_revision: str | None = "11a1bf2b6fbe"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "files",
        sa.Column("id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("org_id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("uploaded_by", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("filename", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("storage_key", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("content_type", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["org_id"],
            ["organizations.id"],
        ),
        sa.ForeignKeyConstraint(
            ["uploaded_by"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_files_org_id"), "files", ["org_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_files_org_id"), table_name="files")
    op.drop_table("files")
