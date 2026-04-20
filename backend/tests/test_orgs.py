import uuid

import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.models.org import OrgRole
from app.services.auth import auth_service
from app.services.orgs import org_service


def auth_header(user_id: uuid.UUID) -> dict:
    token = create_access_token(subject=str(user_id))
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def alice(session):
    return auth_service.create_user(
        session, email="alice@example.com", password="pass", full_name="Alice"
    )


@pytest.fixture
def bob(session):
    return auth_service.create_user(
        session, email="bob@example.com", password="pass", full_name="Bob"
    )


# --- Create org ---


def test_create_org(client: TestClient, alice):
    resp = client.post(
        "/api/v1/orgs/",
        json={"name": "Acme", "slug": "acme"},
        headers=auth_header(alice.id),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Acme"
    assert data["slug"] == "acme"


def test_create_org_unauthenticated(client: TestClient):
    resp = client.post("/api/v1/orgs/", json={"name": "Acme", "slug": "acme"})
    assert resp.status_code == 401


# --- List orgs ---


def test_list_orgs_returns_only_user_orgs(client: TestClient, alice, bob, session):
    org_service.create_org(
        session, name="Alice Org", slug="alice-org", created_by=alice.id
    )
    org_service.create_org(session, name="Bob Org", slug="bob-org", created_by=bob.id)
    resp = client.get("/api/v1/orgs/", headers=auth_header(alice.id))
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["slug"] == "alice-org"


# --- Get org ---


def test_get_org_as_member(client: TestClient, alice, session):
    org = org_service.create_org(session, name="Mine", slug="mine", created_by=alice.id)
    resp = client.get(f"/api/v1/orgs/{org.id}", headers=auth_header(alice.id))
    assert resp.status_code == 200
    assert resp.json()["id"] == str(org.id)


def test_get_org_as_non_member_returns_404(client: TestClient, alice, bob, session):
    org = org_service.create_org(
        session, name="Private", slug="private", created_by=alice.id
    )
    resp = client.get(f"/api/v1/orgs/{org.id}", headers=auth_header(bob.id))
    assert resp.status_code == 404


# --- Update org ---


def test_update_org_as_owner(client: TestClient, alice, session):
    org = org_service.create_org(session, name="Old", slug="old", created_by=alice.id)
    resp = client.patch(
        f"/api/v1/orgs/{org.id}",
        json={"name": "New"},
        headers=auth_header(alice.id),
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "New"


def test_update_org_as_member_returns_403(client: TestClient, alice, bob, session):
    org = org_service.create_org(session, name="Org", slug="org", created_by=alice.id)
    org_service.add_member(session, org_id=org.id, user_id=bob.id, role=OrgRole.member)
    resp = client.patch(
        f"/api/v1/orgs/{org.id}",
        json={"name": "Hack"},
        headers=auth_header(bob.id),
    )
    assert resp.status_code == 403


# --- Delete org ---


def test_delete_org_as_owner(client: TestClient, alice, session):
    org = org_service.create_org(
        session, name="ToDelete", slug="to-delete", created_by=alice.id
    )
    resp = client.delete(f"/api/v1/orgs/{org.id}", headers=auth_header(alice.id))
    assert resp.status_code == 204


def test_delete_org_as_admin_returns_403(client: TestClient, alice, bob, session):
    org = org_service.create_org(session, name="Org", slug="org2", created_by=alice.id)
    org_service.add_member(session, org_id=org.id, user_id=bob.id, role=OrgRole.admin)
    resp = client.delete(f"/api/v1/orgs/{org.id}", headers=auth_header(bob.id))
    assert resp.status_code == 403


# --- Members ---


def test_list_members(client: TestClient, alice, bob, session):
    org = org_service.create_org(session, name="Team", slug="team", created_by=alice.id)
    org_service.add_member(session, org_id=org.id, user_id=bob.id, role=OrgRole.member)
    resp = client.get(f"/api/v1/orgs/{org.id}/members", headers=auth_header(alice.id))
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_change_member_role(client: TestClient, alice, bob, session):
    org = org_service.create_org(
        session, name="Team2", slug="team2", created_by=alice.id
    )
    org_service.add_member(session, org_id=org.id, user_id=bob.id, role=OrgRole.member)
    resp = client.patch(
        f"/api/v1/orgs/{org.id}/members/{bob.id}",
        json={"role": "admin"},
        headers=auth_header(alice.id),
    )
    assert resp.status_code == 200
    assert resp.json()["role"] == "admin"


def test_remove_member(client: TestClient, alice, bob, session):
    org = org_service.create_org(
        session, name="Team3", slug="team3", created_by=alice.id
    )
    org_service.add_member(session, org_id=org.id, user_id=bob.id, role=OrgRole.member)
    resp = client.delete(
        f"/api/v1/orgs/{org.id}/members/{bob.id}",
        headers=auth_header(alice.id),
    )
    assert resp.status_code == 204
