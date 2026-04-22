import uuid

import pytest

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
    assert len(raw_key) == 74  # "sk_live_" (8) + token_hex(32) = 64 hex chars
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
