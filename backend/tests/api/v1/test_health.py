import pytest
from httpx import AsyncClient

async def test_health_returns_ok(client: AsyncClient):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200


async def test_health_body_has_status_ok(client: AsyncClient):
    response = await client.get("/api/v1/health")
    data = response.json()
    assert data["status"] == "ok"


async def test_health_body_has_db_ok(client: AsyncClient):
    response = await client.get("/api/v1/health")
    data = response.json()
    assert data["db"] == "ok"


async def test_health_has_request_id_header(client: AsyncClient):
    response = await client.get("/api/v1/health")
    assert "x-request-id" in response.headers


async def test_health_returns_503_when_db_fails(client: AsyncClient):
    from unittest.mock import AsyncMock
    from sqlmodel.ext.asyncio.session import AsyncSession
    from app.core.db import get_session
    from app.main import app as fastapi_app

    async def broken_session():
        mock = AsyncMock(spec=AsyncSession)
        mock.exec.side_effect = Exception("DB unreachable")
        yield mock

    fastapi_app.dependency_overrides[get_session] = broken_session
    try:
        response = await client.get("/api/v1/health")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "degraded"
        assert data["db"] == "error"
    finally:
        fastapi_app.dependency_overrides.clear()
