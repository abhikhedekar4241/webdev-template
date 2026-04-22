from sqlmodel import Session

from app.models.org import OrgRole
from app.services.orgs import org_service


async def test_create_org_service(session: Session, alice):
    org = await org_service.create_org(
        session, name="Acme", slug="acme", created_by=alice.id
    )
    assert org.name == "Acme"
    assert org.slug == "acme"
    membership = await org_service.get_membership(
        session, org_id=org.id, user_id=alice.id
    )
    assert membership is not None
    assert membership.role == OrgRole.owner


async def test_list_user_orgs(session: Session, alice, bob):
    org1 = await org_service.create_org(
        session, name="Org1", slug="org1", created_by=alice.id
    )
    await org_service.create_org(session, name="Org2", slug="org2", created_by=bob.id)
    orgs = await org_service.list_user_orgs(session, user_id=alice.id)
    assert len(orgs) == 1
    assert orgs[0].id == org1.id


async def test_get_org_returns_none_if_not_member(session: Session, alice, bob):
    org = await org_service.create_org(
        session, name="Private", slug="private", created_by=alice.id
    )
    result = await org_service.get_org_for_member(
        session, org_id=org.id, user_id=bob.id
    )
    assert result is None


async def test_get_org_returns_org_for_member_service(session: Session, alice):
    org = await org_service.create_org(
        session, name="Mine", slug="mine", created_by=alice.id
    )
    result = await org_service.get_org_for_member(
        session, org_id=org.id, user_id=alice.id
    )
    assert result is not None
    assert result.id == org.id


async def test_update_org_service(session: Session, alice):
    org = await org_service.create_org(
        session, name="Old", slug="old", created_by=alice.id
    )
    updated = await org_service.update_org(
        session, org=org, name="New", slug="new-slug"
    )
    assert updated.name == "New"
    assert updated.slug == "new-slug"


async def test_soft_delete_org_service(session: Session, alice):
    org = await org_service.create_org(
        session, name="ToDelete", slug="to-delete", created_by=alice.id
    )
    await org_service.soft_delete_org(session, org=org)
    result = await org_service.get_org_for_member(
        session, org_id=org.id, user_id=alice.id
    )
    assert result is None


async def test_list_members_service(session: Session, alice, bob):
    org = await org_service.create_org(
        session, name="Team", slug="team", created_by=alice.id
    )
    await org_service.add_member(
        session, org_id=org.id, user_id=bob.id, role=OrgRole.member
    )
    members = await org_service.list_members(session, org_id=org.id)
    assert len(members) == 2


async def test_change_role_service(session: Session, alice, bob):
    org = await org_service.create_org(
        session, name="Team", slug="team2", created_by=alice.id
    )
    await org_service.add_member(
        session, org_id=org.id, user_id=bob.id, role=OrgRole.member
    )
    membership = await org_service.change_role(
        session, org_id=org.id, user_id=bob.id, role=OrgRole.admin
    )
    assert membership is not None
    assert membership.role == OrgRole.admin


async def test_remove_member_service(session: Session, alice, bob):
    org = await org_service.create_org(
        session, name="Team", slug="team3", created_by=alice.id
    )
    await org_service.add_member(
        session, org_id=org.id, user_id=bob.id, role=OrgRole.member
    )
    await org_service.remove_member(session, org_id=org.id, user_id=bob.id)
    members = await org_service.list_members(session, org_id=org.id)
    assert len(members) == 1
