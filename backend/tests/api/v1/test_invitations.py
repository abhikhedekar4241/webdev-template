import uuid
from fastapi.testclient import TestClient
from sqlmodel import Session
from tests.helpers import get_auth_header
from app.models.invitation import InvitationStatus
from app.models.org import OrgRole
from app.services.auth import auth_service
from app.services.invitations import invitation_service
from app.services.orgs import org_service

async def test_create_invitation_as_owner(client: TestClient, alice, alice_org):
    resp = await client.post(
        "/api/v1/invitations/",
        json={
            "org_id": str(alice_org.id),
            "email": "newbie@example.com",
            "role": "member",
        },
        headers=get_auth_header(alice.id),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["invited_email"] == "newbie@example.com"
    assert data["status"] == "pending"


async def test_create_invitation_as_non_member_returns_403(client: TestClient, bob, alice_org):
    resp = await client.post(
        "/api/v1/invitations/",
        json={
            "org_id": str(alice_org.id),
            "email": "newbie@example.com",
            "role": "member",
        },
        headers=get_auth_header(bob.id),
    )
    assert resp.status_code == 403


async def test_create_invitation_as_plain_member_returns_403(client: TestClient, bob, alice_org, session: Session):
    await org_service.add_member(session, org_id=alice_org.id, user_id=bob.id, role=OrgRole.member)
    resp = await client.post(
        "/api/v1/invitations/",
        json={
            "org_id": str(alice_org.id),
            "email": "newbie@example.com",
            "role": "member",
        },
        headers=get_auth_header(bob.id),
    )
    assert resp.status_code == 403


async def test_list_invitations_returns_pending_for_current_user(
    client: TestClient, alice, bob, alice_org, session: Session
):
    await invitation_service.create_invitation(
        session,
        org_id=alice_org.id,
        invited_email=bob.email,
        role=OrgRole.member,
        invited_by=alice.id,
    )
    resp = await client.get("/api/v1/invitations/", headers=get_auth_header(bob.id))
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["invited_email"] == bob.email


async def test_list_invitations_empty_for_no_pending(client: TestClient, alice):
    resp = await client.get("/api/v1/invitations/", headers=get_auth_header(alice.id))
    assert resp.status_code == 200
    assert resp.json() == []


async def test_accept_invitation_api(client: TestClient, alice, bob, alice_org, session: Session):
    inv = await invitation_service.create_invitation(
        session,
        org_id=alice_org.id,
        invited_email=bob.email,
        role=OrgRole.member,
        invited_by=alice.id,
    )
    resp = await client.post(
        f"/api/v1/invitations/{inv.id}/accept",
        headers=get_auth_header(bob.id),
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "Invitation accepted"
    membership = await org_service.get_membership(session, org_id=alice_org.id, user_id=bob.id)
    assert membership is not None


async def test_accept_invitation_wrong_user_returns_403(
    client: TestClient, alice, bob, alice_org, session: Session
):
    await auth_service.create_user(
        session, email="carol@example.com", password="pass", full_name="Carol"
    )
    inv = await invitation_service.create_invitation(
        session,
        org_id=alice_org.id,
        invited_email="carol@example.com",
        role=OrgRole.member,
        invited_by=alice.id,
    )
    resp = await client.post(
        f"/api/v1/invitations/{inv.id}/accept",
        headers=get_auth_header(bob.id),
    )
    assert resp.status_code == 403


async def test_decline_invitation_api(client: TestClient, alice, bob, alice_org, session: Session):
    inv = await invitation_service.create_invitation(
        session,
        org_id=alice_org.id,
        invited_email=bob.email,
        role=OrgRole.member,
        invited_by=alice.id,
    )
    resp = await client.post(
        f"/api/v1/invitations/{inv.id}/decline",
        headers=get_auth_header(bob.id),
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "Invitation declined"
    await session.refresh(inv)
    assert inv.status == InvitationStatus.declined


async def test_accept_nonexistent_returns_404(client: TestClient, alice):
    resp = await client.post(
        f"/api/v1/invitations/{uuid.uuid4()}/accept",
        headers=get_auth_header(alice.id),
    )
    assert resp.status_code == 404


async def test_duplicate_invitation_rejected(client: TestClient, alice, alice_org):
    resp1 = await client.post(
        "/api/v1/invitations/",
        json={"org_id": str(alice_org.id), "email": "newbie@example.com", "role": "member"},
        headers=get_auth_header(alice.id),
    )
    assert resp1.status_code == 201

    resp2 = await client.post(
        "/api/v1/invitations/",
        json={"org_id": str(alice_org.id), "email": "newbie@example.com", "role": "member"},
        headers=get_auth_header(alice.id),
    )
    assert resp2.status_code == 409
    assert "pending invitation" in resp2.json()["detail"].lower()


async def test_invite_existing_member_rejected(client: TestClient, alice, bob, alice_org, session: Session):
    await org_service.add_member(session, org_id=alice_org.id, user_id=bob.id, role=OrgRole.member)
    resp = await client.post(
        "/api/v1/invitations/",
        json={"org_id": str(alice_org.id), "email": bob.email, "role": "member"},
        headers=get_auth_header(alice.id),
    )
    assert resp.status_code == 409
    assert "already a member" in resp.json()["detail"].lower()
