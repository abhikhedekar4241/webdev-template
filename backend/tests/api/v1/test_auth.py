from fastapi.testclient import TestClient


async def test_register_short_password_rejected(client: TestClient):
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": "user@example.com", "password": "short", "full_name": "User"},
    )
    assert resp.status_code == 422


async def test_register_valid_password_succeeds(client: TestClient):
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "user@example.com",
            "password": "longenough",
            "full_name": "User",
        },
    )
    assert resp.status_code == 201


async def test_register_unverified_email_can_be_reclaimed(client: TestClient):
    # First registration — email reserved but unverified
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "dup@example.com",
            "password": "password123",
            "full_name": "First",
        },
    )
    # Second registration with same unverified email should succeed (not 409)
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "dup@example.com",
            "password": "newpassword",
            "full_name": "Second",
        },
    )
    assert resp.status_code == 201


async def test_register_verified_email_returns_409(client: TestClient, session):
    from app.core.security import hash_password
    from app.models.user import User

    # Insert a verified user directly
    user = User(
        email="taken@example.com",
        hashed_password=hash_password("password123"),
        full_name="Verified User",
        is_verified=True,
    )
    session.add(user)
    await session.commit()

    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "taken@example.com",
            "password": "password123",
            "full_name": "Attacker",
        },
    )
    assert resp.status_code == 409
