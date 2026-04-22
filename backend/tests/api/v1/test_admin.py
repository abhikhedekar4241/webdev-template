from fastapi.testclient import TestClient

from app.models.user import User
from tests.helpers import get_auth_header


async def test_get_stats_superuser(client: TestClient, superuser: User):
    response = await client.get(
        "/api/v1/admin/stats", headers=get_auth_header(superuser.id)
    )
    assert response.status_code == 200
    data = response.json()
    assert "user_count" in data
    assert "org_count" in data


async def test_get_stats_forbidden_for_normal_user(client: TestClient, alice: User):
    response = await client.get(
        "/api/v1/admin/stats", headers=get_auth_header(alice.id)
    )
    assert response.status_code == 403


async def test_impersonate_user(client: TestClient, superuser: User, alice: User):
    response = await client.post(
        f"/api/v1/admin/impersonate/{alice.id}",
        headers=get_auth_header(superuser.id),
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data

    # Verify the new token works as the normal user
    impersonation_token = data["access_token"]
    me_response = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {impersonation_token}"}
    )
    assert me_response.status_code == 200
    assert me_response.json()["email"] == alice.email


async def test_list_users(client: TestClient, superuser: User, alice: User):
    response = await client.get(
        "/api/v1/admin/users", headers=get_auth_header(superuser.id)
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert any(u["email"] == alice.email for u in data["items"])
    assert any(u["email"] == superuser.email for u in data["items"])
