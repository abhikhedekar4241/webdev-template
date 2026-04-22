"""make_datetimes_timezone_aware

Revision ID: 827488ef1299
Revises: aa41a24dbfc6_add_audit_logs_and_feature_flag_
Create Date: 2026-04-22 12:44:33.681684

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '827488ef1299'
down_revision: str | None = 'aa41a24dbfc6'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- Tables with DateTime changes ---

    tables_to_fix = {
        'audit_logs': ['created_at'],
        'feature_flag_overrides': ['updated_at'],
        'files': ['deleted_at', 'created_at'],
        'notifications': ['read_at', 'created_at'],
        'org_api_keys': ['last_used_at', 'expires_at', 'revoked_at', 'created_at'],
        'org_invitations': ['expires_at', 'created_at'],
        'org_memberships': ['joined_at'],
        'organizations': ['deleted_at', 'created_at'],
        'user_oauth_accounts': ['created_at'],
        'users': ['onboarding_completed_at', 'deleted_at', 'created_at'],
        'email_verifications': ['expires_at', 'used_at', 'created_at'],
    }

    for table, columns in tables_to_fix.items():
        for col in columns:
            op.execute(f"ALTER TABLE {table} ALTER COLUMN {col} TYPE TIMESTAMPTZ USING {col} AT TIME ZONE 'UTC'")

    # --- org_memberships.role enum fix ---
    # Convert role from VARCHAR to ENUM
    # Note: orgrole enum might already exist from previous migrations
    op.execute("ALTER TABLE org_memberships ALTER COLUMN role TYPE orgrole USING role::orgrole")


def downgrade() -> None:
    tables_to_fix = {
        'audit_logs': ['created_at'],
        'feature_flag_overrides': ['updated_at'],
        'files': ['deleted_at', 'created_at'],
        'notifications': ['read_at', 'created_at'],
        'org_api_keys': ['last_used_at', 'expires_at', 'revoked_at', 'created_at'],
        'org_invitations': ['expires_at', 'created_at'],
        'org_memberships': ['joined_at'],
        'organizations': ['deleted_at', 'created_at'],
        'user_oauth_accounts': ['created_at'],
        'users': ['onboarding_completed_at', 'deleted_at', 'created_at'],
        'email_verifications': ['expires_at', 'used_at', 'created_at'],
    }

    for table, columns in tables_to_fix.items():
        for col in columns:
            op.execute(f"ALTER TABLE {table} ALTER COLUMN {col} TYPE TIMESTAMP WITHOUT TIME ZONE")

    op.alter_column('org_memberships', 'role',
               existing_type=sa.Enum('owner', 'admin', 'member', name='orgrole'),
               type_=sa.VARCHAR(),
               existing_nullable=False)
