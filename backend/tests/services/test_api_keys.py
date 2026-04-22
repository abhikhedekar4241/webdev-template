import uuid
import pytest
from app.services.api_keys import _hash_key, api_key_service

def test_create_returns_record_and_raw_key(session, alice, alice_org):
    record, raw_key = api_key_service.create(
        session, org_id=alice_org.id, name="CI key", created_by=alice.id
    )
    assert raw_key.startswith("sk_live_")
    assert len(raw_key) == 74  # "sk_live_" (8) + token_hex(33) produces 66 hex chars = 74 total
    assert record.key_prefix == raw_key[:10]
    assert record.key_hash == _hash_key(raw_key)
    assert record.revoked_at is None


def test_authenticate_valid_key(session, alice, alice_org):
    record, raw_key = api_key_service.create(
        session, org_id=alice_org.id, name="Key", created_by=alice.id
    )
    result = api_key_service.authenticate(session, raw_key=raw_key)
    assert result is not None
    assert result.id == record.id


def test_authenticate_wrong_key_returns_none(session, alice, alice_org):
    api_key_service.create(session, org_id=alice_org.id, name="Key", created_by=alice.id)
    result = api_key_service.authenticate(session, raw_key="sk_live_" + "0" * 64)
    assert result is None


def test_authenticate_updates_last_used_at(session, alice, alice_org):
    record, raw_key = api_key_service.create(
        session, org_id=alice_org.id, name="Key", created_by=alice.id
    )
    assert record.last_used_at is None
    api_key_service.authenticate(session, raw_key=raw_key)
    session.refresh(record)
    assert record.last_used_at is not None


def test_authenticate_revoked_key_returns_none(session, alice, alice_org):
    record, raw_key = api_key_service.create(
        session, org_id=alice_org.id, name="Key", created_by=alice.id
    )
    api_key_service.revoke(session, key_id=record.id, org_id=alice_org.id)
    result = api_key_service.authenticate(session, raw_key=raw_key)
    assert result is None


def test_revoke_wrong_org_returns_false(session, alice, alice_org):
    record, _ = api_key_service.create(
        session, org_id=alice_org.id, name="Key", created_by=alice.id
    )
    result = api_key_service.revoke(session, key_id=record.id, org_id=uuid.uuid4())
    assert result is False


def test_list_excludes_revoked(session, alice, alice_org):
    record, _ = api_key_service.create(
        session, org_id=alice_org.id, name="Key", created_by=alice.id
    )
    api_key_service.revoke(session, key_id=record.id, org_id=alice_org.id)
    keys = api_key_service.list_for_org(session, org_id=alice_org.id)
    assert keys == []
