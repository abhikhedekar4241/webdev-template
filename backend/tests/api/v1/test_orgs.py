from fastapi.testclient import TestClient
from sqlmodel import Session
from tests.helpers import get_auth_header
from app.models.org import OrgRole
from app.services.orgs import org_service

async def test_create_org_api(client: TestClient, alice):
    resp = await client.post(
        "/api/v1/orgs/",
        json={"name": "Acme", "slug": "acme"},
        headers=get_auth_header(alice.id),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Acme"
    assert data["slug"] == "acme"


async def test_create_org_unauthenticated(client: TestClient):
    resp = await client.post("/api/v1/orgs/", json={"name": "Acme", "slug": "acme"})
    assert resp.status_code == 401


async def test_list_orgs_returns_only_user_orgs_api(client: TestClient, alice, bob, session: Session):
    await org_service.create_org(
        session, name="Alice Org", slug="alice-org", created_by=alice.id
    )
    await org_service.create_org(session, name="Bob Org", slug="bob-org", created_by=bob.id)
    resp = await client.get("/api/v1/orgs/", headers=get_auth_header(alice.id))
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["slug"] == "alice-org"


async def test_get_org_as_member_api(client: TestClient, alice, session: Session):
    org = await org_service.create_org(session, name="Mine", slug="mine", created_by=alice.id)
    resp = await client.get(f"/api/v1/orgs/{org.id}", headers=get_auth_header(alice.id))
    assert resp.status_code == 200
    assert resp.json()["id"] == str(org.id)


async def test_get_org_as_non_member_returns_404(client: TestClient, alice, bob, session: Session):
    org = await org_service.create_org(
        session, name="Private", slug="private", created_by=alice.id
    )
    resp = await client.get(f"/api/v1/orgs/{org.id}", headers=get_auth_header(bob.id))
    assert resp.status_code == 404


async def test_update_org_as_owner_api(client: TestClient, alice, session: Session):
    org = await org_service.create_org(session, name="Old", slug="old", created_by=alice.id)
    resp = await client.patch(
        f"/api/v1/orgs/{org.id}",
        json={"name": "New"},
        headers=get_auth_header(alice.id),
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "New"


async def test_update_org_as_member_returns_403(client: TestClient, alice, bob, session: Session):
    org = await org_service.create_org(session, name="Org", slug="org", created_by=alice.id)
    await org_service.add_member(session, org_id=org.id, user_id=bob.id, role=OrgRole.member)
    resp = await client.patch(
        f"/api/v1/orgs/{org.id}",
        json={"name": "Hack"},
        headers=get_auth_header(bob.id),
    )
    assert resp.status_code == 403


async def test_delete_org_as_owner_api(client: TestClient, alice, session: Session):
    org = await org_service.create_org(
        session, name="ToDelete", slug="to-delete", created_by=alice.id
    )
    resp = await client.delete(f"/api/v1/orgs/{org.id}", headers=get_auth_header(alice.id))
    assert resp.status_code == 204


async def test_delete_org_as_admin_returns_403(client: TestClient, alice, bob, session: Session):
    org = await org_service.create_org(session, name="Org", slug="org2", created_by=alice.id)
    await org_service.add_member(session, org_id=org.id, user_id=bob.id, role=OrgRole.admin)
    resp = await client.delete(f"/api/v1/orgs/{org.id}", headers=get_auth_header(bob.id))
    assert resp.status_code == 403


async def test_list_members_api(client: TestClient, alice, bob, session: Session):
    org = await org_service.create_org(session, name="Team", slug="team", created_by=alice.id)
    await org_service.add_member(session, org_id=org.id, user_id=bob.id, role=OrgRole.member)
    resp = await client.get(f"/api/v1/orgs/{org.id}/members", headers=get_auth_header(alice.id))
    assert resp.status_code == 200
    assert len(resp.json()) == 2


async def test_change_member_role_api(client: TestClient, alice, bob, session: Session):
    org = await org_service.create_org(
        session, name="Team2", slug="team2", created_by=alice.id
    )
    await org_service.add_member(session, org_id=org.id, user_id=bob.id, role=OrgRole.member)
    resp = await client.patch(
        f"/api/v1/orgs/{org.id}/members/{bob.id}",
        json={"role": "admin"},
        headers=get_auth_header(alice.id),
    )
    assert resp.status_code == 200
    assert resp.json()["role"] == "admin"


async def test_remove_member_api(client: TestClient, alice, bob, session: Session):
    org = await org_service.create_org(
        session, name="Team3", slug="team3", created_by=alice.id
    )
    await org_service.add_member(session, org_id=org.id, user_id=bob.id, role=OrgRole.member)
    resp = await client.delete(
        f"/api/v1/orgs/{org.id}/members/{bob.id}",
        headers=get_auth_header(alice.id),
    )
    assert resp.status_code == 204


async def test_create_org_duplicate_slug_returns_409(client: TestClient, alice):
    resp1 = await client.post(
        "/api/v1/orgs/",
        json={"name": "Acme", "slug": "dup-slug"},
        headers=get_auth_header(alice.id),
    )
    assert resp1.status_code == 201

    resp2 = await client.post(
        "/api/v1/orgs/",
        json={"name": "Acme2", "slug": "dup-slug"},
        headers=get_auth_header(alice.id),
    )
    assert resp2.status_code == 409
    assert "slug" in resp2.json()["detail"].lower()


async def test_cannot_remove_owner_api(client: TestClient, alice, session: Session):
    org = await org_service.create_org(
        session, name="Team4", slug="team4", created_by=alice.id
    )
    resp = await client.delete(
        f"/api/v1/orgs/{org.id}/members/{alice.id}",
        headers=get_auth_header(alice.id),
    )
    assert resp.status_code == 403
    assert "owner" in resp.json()["detail"].lower()
