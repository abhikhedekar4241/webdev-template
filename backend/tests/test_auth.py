from fastapi.testclient import TestClient


def test_register_short_password_rejected(client: TestClient):
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": "user@example.com", "password": "short", "full_name": "User"},
    )
    assert resp.status_code == 422


def test_register_valid_password_succeeds(client: TestClient):
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": "user@example.com", "password": "longenough", "full_name": "User"},
    )
    assert resp.status_code == 201


def test_register_duplicate_email_returns_409(client: TestClient):
    client.post(
        "/api/v1/auth/register",
        json={"email": "dup@example.com", "password": "password123", "full_name": "User"},
    )
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": "dup@example.com", "password": "password123", "full_name": "User"},
    )
    assert resp.status_code == 409
