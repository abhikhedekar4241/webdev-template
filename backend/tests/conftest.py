import pytest
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.pool import StaticPool

from app.core.db import get_session
from app.main import app
from app.services.auth import auth_service
from app.services.orgs import org_service


@pytest.fixture(name="session")
async def session_fixture():
    from sqlalchemy.ext.asyncio import create_async_engine

    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


@pytest.fixture(name="client")
async def client_fixture(session: AsyncSession):
    async def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    from httpx import ASGITransport, AsyncClient

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
async def alice(session: AsyncSession):
    return await auth_service.create_user(
        session, email="alice@example.com", password="password", full_name="Alice"
    )


@pytest.fixture
async def bob(session: AsyncSession):
    return await auth_service.create_user(
        session, email="bob@example.com", password="password", full_name="Bob"
    )


@pytest.fixture
async def superuser(session: AsyncSession):
    user = await auth_service.create_user(
        session,
        email="admin@example.com",
        password="password",
        full_name="Admin",
    )
    user.is_superuser = True
    user.is_verified = True
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest.fixture
async def alice_org(session: AsyncSession, alice):
    return await org_service.create_org(
        session, name="Alice Corp", slug="alice-corp", created_by=alice.id
    )
