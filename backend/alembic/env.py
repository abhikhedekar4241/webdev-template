import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlmodel import SQLModel

from alembic import context
from app.models.api_key import OrgApiKey  # noqa: F401
from app.models.audit_log import AuditLog  # noqa: F401
from app.models.feature_flag import FeatureFlagOverride  # noqa: F401
from app.models.file import File  # noqa: F401
from app.models.invitation import InvitationStatus, OrgInvitation  # noqa: F401
from app.models.notification import Notification  # noqa: F401
from app.models.oauth_account import UserOAuthAccount  # noqa: F401
from app.models.org import Organization, OrgMembership, OrgRole  # noqa: F401

# Import all models here as they are created in later plans so Alembic
# can detect schema changes. Example (uncomment as models are added):
from app.models.user import User  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata


def get_url() -> str:
    from app.core.config import settings

    return settings.DATABASE_URL


def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()
    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
