import uuid

import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.models.org import OrgRole
from app.services.api_keys import ApiKeyService, _hash_key, api_key_service
from app.services.auth import auth_service
from app.services.orgs import org_service


@pytest.fixture
def owner_and_org(session):
    user = auth_service.create_user(
        session,
        email="apikey_owner@example.com",
        password="password123",
        full_name="Owner",
        is_verified=True,
    )
    org = org_service.create_org(
        session, name="API Key Org", slug="api-key-org", created_by=user.id
    )
    return user, org


def test_create_returns_record_and_raw_key(session, owner_and_org):
    user, org = owner_and_org
    record, raw_key = api_key_service.create(
        session, org_id=org.id, name="CI key", created_by=user.id
    )
    assert raw_key.startswith("sk_live_")
    assert len(raw_key) == 74  # "sk_live_" (8) + token_hex(33) = 66 hex chars
    assert record.key_prefix == raw_key[:10]
    assert record.key_hash == _hash_key(raw_key)
    assert record.revoked_at is None


def test_authenticate_valid_key(session, owner_and_org):
    user, org = owner_and_org
    record, raw_key = api_key_service.create(
        session, org_id=org.id, name="Key", created_by=user.id
    )
    result = api_key_service.authenticate(session, raw_key=raw_key)
    assert result is not None
    assert result.id == record.id


def test_authenticate_wrong_key_returns_none(session, owner_and_org):
    user, org = owner_and_org
    api_key_service.create(session, org_id=org.id, name="Key", created_by=user.id)
    result = api_key_service.authenticate(session, raw_key="sk_live_" + "0" * 64)
    assert result is None


def test_authenticate_updates_last_used_at(session, owner_and_org):
    user, org = owner_and_org
    record, raw_key = api_key_service.create(
        session, org_id=org.id, name="Key", created_by=user.id
    )
    assert record.last_used_at is None
    api_key_service.authenticate(session, raw_key=raw_key)
    session.refresh(record)
    assert record.last_used_at is not None


def test_authenticate_revoked_key_returns_none(session, owner_and_org):
    user, org = owner_and_org
    record, raw_key = api_key_service.create(
        session, org_id=org.id, name="Key", created_by=user.id
    )
    api_key_service.revoke(session, key_id=record.id, org_id=org.id)
    result = api_key_service.authenticate(session, raw_key=raw_key)
    assert result is None


def test_revoke_wrong_org_returns_false(session, owner_and_org):
    user, org = owner_and_org
    record, _ = api_key_service.create(
        session, org_id=org.id, name="Key", created_by=user.id
    )
    result = api_key_service.revoke(session, key_id=record.id, org_id=uuid.uuid4())
    assert result is False


def test_list_excludes_revoked(session, owner_and_org):
    user, org = owner_and_org
    record, _ = api_key_service.create(
        session, org_id=org.id, name="Key", created_by=user.id
    )
    api_key_service.revoke(session, key_id=record.id, org_id=org.id)
    keys = api_key_service.list_for_org(session, org_id=org.id)
    assert keys == []


def _auth(user_id):
    return {"Authorization": f"Bearer {create_access_token(str(user_id))}"}


def test_create_key_via_api(client: TestClient, session, owner_and_org):
    user, org = owner_and_org
    resp = client.post(
        f"/api/v1/orgs/{org.id}/api-keys",
        json={"name": "CI/CD Key"},
        headers=_auth(user.id),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["key"].startswith("sk_live_")
    assert data["key_prefix"] == data["key"][:10]
    assert "key_hash" not in data  # hash must never be returned


def test_list_keys_via_api(client: TestClient, session, owner_and_org):
    user, org = owner_and_org
    api_key_service.create(session, org_id=org.id, name="Key", created_by=user.id)
    resp = client.get(f"/api/v1/orgs/{org.id}/api-keys", headers=_auth(user.id))
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert "key" not in resp.json()[0]  # full key must not appear in list


def test_revoke_key_via_api(client: TestClient, session, owner_and_org):
    user, org = owner_and_org
    record, _ = api_key_service.create(
        session, org_id=org.id, name="Key", created_by=user.id
    )
    resp = client.delete(
        f"/api/v1/orgs/{org.id}/api-keys/{record.id}", headers=_auth(user.id)
    )
    assert resp.status_code == 204


def test_api_key_authenticates_on_existing_endpoint(
    client: TestClient, session, owner_and_org
):
    user, org = owner_and_org
    _, raw_key = api_key_service.create(
        session, org_id=org.id, name="Key", created_by=user.id
    )
    resp = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {raw_key}"}
    )
    assert resp.status_code == 200
    assert resp.json()["email"] == user.email


def test_member_cannot_create_key(client: TestClient, session, owner_and_org):
    user, org = owner_and_org
    member = auth_service.create_user(
        session,
        email="member_nokey@example.com",
        password="password123",
        full_name="Member",
        is_verified=True,
    )
    org_service.add_member(session, org_id=org.id, user_id=member.id, role=OrgRole.member)
    resp = client.post(
        f"/api/v1/orgs/{org.id}/api-keys",
        json={"name": "Key"},
        headers=_auth(member.id),
    )
    assert resp.status_code == 403


def test_revoke_nonexistent_key_returns_404(client: TestClient, session, owner_and_org):
    user, org = owner_and_org
    resp = client.delete(
        f"/api/v1/orgs/{org.id}/api-keys/{uuid.uuid4()}",
        headers=_auth(user.id),
    )
    assert resp.status_code == 404
