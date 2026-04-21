import uuid

import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.models.invitation import InvitationStatus, OrgInvitation
from app.models.org import OrgMembership, OrgRole, Organization
from app.models.user import User
from app.services.auth import auth_service
from app.services.invitations import invitation_service
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


@pytest.fixture
def org(session, alice):
    return org_service.create_org(
        session, name="Acme", slug="acme", created_by=alice.id
    )


def test_create_invitation_as_owner(client: TestClient, alice, org):
    resp = client.post(
        "/api/v1/invitations/",
        json={
            "org_id": str(org.id),
            "email": "newbie@example.com",
            "role": "member",
        },
        headers=auth_header(alice.id),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["invited_email"] == "newbie@example.com"
    assert data["status"] == "pending"


def test_create_invitation_as_non_member_returns_403(client: TestClient, bob, org):
    resp = client.post(
        "/api/v1/invitations/",
        json={
            "org_id": str(org.id),
            "email": "newbie@example.com",
            "role": "member",
        },
        headers=auth_header(bob.id),
    )
    assert resp.status_code == 403


def test_create_invitation_as_plain_member_returns_403(client: TestClient, bob, org, session):
    org_service.add_member(session, org_id=org.id, user_id=bob.id, role=OrgRole.member)
    resp = client.post(
        "/api/v1/invitations/",
        json={
            "org_id": str(org.id),
            "email": "newbie@example.com",
            "role": "member",
        },
        headers=auth_header(bob.id),
    )
    assert resp.status_code == 403


def test_list_invitations_returns_pending_for_current_user(
    client: TestClient, alice, bob, org, session
):
    invitation_service.create_invitation(
        session,
        org_id=org.id,
        invited_email=bob.email,
        role=OrgRole.member,
        invited_by=alice.id,
    )
    resp = client.get("/api/v1/invitations/", headers=auth_header(bob.id))
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["invited_email"] == bob.email


def test_list_invitations_empty_for_no_pending(client: TestClient, alice):
    resp = client.get("/api/v1/invitations/", headers=auth_header(alice.id))
    assert resp.status_code == 200
    assert resp.json() == []


def test_accept_invitation(client: TestClient, alice, bob, org, session):
    inv = invitation_service.create_invitation(
        session,
        org_id=org.id,
        invited_email=bob.email,
        role=OrgRole.member,
        invited_by=alice.id,
    )
    resp = client.post(
        f"/api/v1/invitations/{inv.id}/accept",
        headers=auth_header(bob.id),
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "Invitation accepted"
    membership = org_service.get_membership(session, org_id=org.id, user_id=bob.id)
    assert membership is not None


def test_accept_invitation_wrong_user_returns_403(
    client: TestClient, alice, bob, org, session
):
    carol = auth_service.create_user(
        session, email="carol@example.com", password="pass", full_name="Carol"
    )
    inv = invitation_service.create_invitation(
        session,
        org_id=org.id,
        invited_email="carol@example.com",
        role=OrgRole.member,
        invited_by=alice.id,
    )
    resp = client.post(
        f"/api/v1/invitations/{inv.id}/accept",
        headers=auth_header(bob.id),
    )
    assert resp.status_code == 403


def test_decline_invitation(client: TestClient, alice, bob, org, session):
    inv = invitation_service.create_invitation(
        session,
        org_id=org.id,
        invited_email=bob.email,
        role=OrgRole.member,
        invited_by=alice.id,
    )
    resp = client.post(
        f"/api/v1/invitations/{inv.id}/decline",
        headers=auth_header(bob.id),
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "Invitation declined"
    session.refresh(inv)
    assert inv.status == InvitationStatus.declined


def test_accept_nonexistent_returns_404(client: TestClient, alice):
    resp = client.post(
        f"/api/v1/invitations/{uuid.uuid4()}/accept",
        headers=auth_header(alice.id),
    )
    assert resp.status_code == 404
