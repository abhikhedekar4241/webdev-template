def test_health_returns_ok(client):
    response = client.get("/health")
    assert response.status_code == 200


def test_health_body_has_status_ok(client):
    response = client.get("/health")
    data = response.json()
    assert data["status"] == "ok"


def test_health_body_has_db_ok(client):
    response = client.get("/health")
    data = response.json()
    assert data["db"] == "ok"


def test_health_has_request_id_header(client):
    response = client.get("/health")
    assert "x-request-id" in response.headers


def test_health_returns_503_when_db_fails():
    from unittest.mock import MagicMock

    from fastapi.testclient import TestClient
    from sqlmodel import Session

    from app.core.db import get_session
    from app.main import app as fastapi_app

    def broken_session():
        mock = MagicMock(spec=Session)
        mock.exec.side_effect = Exception("DB unreachable")
        yield mock

    fastapi_app.dependency_overrides[get_session] = broken_session
    try:
        client = TestClient(fastapi_app, raise_server_exceptions=False)
        response = client.get("/health")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "degraded"
        assert data["db"] == "error"
    finally:
        fastapi_app.dependency_overrides.clear()
