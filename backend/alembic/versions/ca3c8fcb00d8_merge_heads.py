"""merge_heads

Revision ID: ca3c8fcb00d8
Revises: 005_add_notifications_table, 827488ef1299
Create Date: 2026-04-22 12:46:32.301028

"""
from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = 'ca3c8fcb00d8'
down_revision: str | None = ('005_add_notifications_table', '827488ef1299')
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
