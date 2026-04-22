import uuid

from fastapi.testclient import TestClient

from app.models.org import OrgRole
from app.services.api_keys import api_key_service
from app.services.orgs import org_service
from tests.helpers import get_auth_header


async def test_create_key_via_api(client: TestClient, session, alice, alice_org):
    resp = await client.post(
        f"/api/v1/orgs/{alice_org.id}/api-keys",
        json={"name": "CI/CD Key"},
        headers=get_auth_header(alice.id),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["key"].startswith("sk_live_")
    assert data["key_prefix"] == data["key"][:10]
    assert "key_hash" not in data  # hash must never be returned


async def test_list_keys_via_api(client: TestClient, session, alice, alice_org):
    await api_key_service.create(
        session, org_id=alice_org.id, name="Key", created_by=alice.id
    )
    resp = await client.get(
        f"/api/v1/orgs/{alice_org.id}/api-keys", headers=get_auth_header(alice.id)
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert "key" not in resp.json()[0]  # full key must not appear in list


async def test_revoke_key_via_api(client: TestClient, session, alice, alice_org):
    record, _ = await api_key_service.create(
        session, org_id=alice_org.id, name="Key", created_by=alice.id
    )
    resp = await client.delete(
        f"/api/v1/orgs/{alice_org.id}/api-keys/{record.id}",
        headers=get_auth_header(alice.id),
    )
    assert resp.status_code == 204


async def test_api_key_authenticates_on_existing_endpoint(
    client: TestClient, session, alice, alice_org
):
    _, raw_key = await api_key_service.create(
        session, org_id=alice_org.id, name="Key", created_by=alice.id
    )
    resp = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {raw_key}"}
    )
    assert resp.status_code == 200
    assert resp.json()["email"] == alice.email


async def test_member_cannot_create_key(client: TestClient, session, bob, alice_org):
    await org_service.add_member(
        session, org_id=alice_org.id, user_id=bob.id, role=OrgRole.member
    )
    resp = await client.post(
        f"/api/v1/orgs/{alice_org.id}/api-keys",
        json={"name": "Key"},
        headers=get_auth_header(bob.id),
    )
    assert resp.status_code == 403


async def test_revoke_nonexistent_key_returns_404(
    client: TestClient, session, alice, alice_org
):
    resp = await client.delete(
        f"/api/v1/orgs/{alice_org.id}/api-keys/{uuid.uuid4()}",
        headers=get_auth_header(alice.id),
    )
    assert resp.status_code == 404


async def test_revoke_already_revoked_key_returns_204(
    client: TestClient, session, alice, alice_org
):
    record, _ = await api_key_service.create(
        session, org_id=alice_org.id, name="Key", created_by=alice.id
    )
    await api_key_service.revoke(session, key_id=record.id, org_id=alice_org.id)
    resp = await client.delete(
        f"/api/v1/orgs/{alice_org.id}/api-keys/{record.id}",
        headers=get_auth_header(alice.id),
    )
    assert resp.status_code == 204
