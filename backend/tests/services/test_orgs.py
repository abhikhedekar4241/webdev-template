from sqlmodel import Session
from app.models.org import OrgRole
from app.services.orgs import org_service

def test_create_org_service(session: Session, alice):
    org = org_service.create_org(session, name="Acme", slug="acme", created_by=alice.id)
    assert org.name == "Acme"
    assert org.slug == "acme"
    membership = org_service.get_membership(session, org_id=org.id, user_id=alice.id)
    assert membership is not None
    assert membership.role == OrgRole.owner


def test_list_user_orgs(session: Session, alice, bob):
    org1 = org_service.create_org(session, name="Org1", slug="org1", created_by=alice.id)
    org_service.create_org(session, name="Org2", slug="org2", created_by=bob.id)
    orgs = org_service.list_user_orgs(session, user_id=alice.id)
    assert len(orgs) == 1
    assert orgs[0].id == org1.id


def test_get_org_returns_none_if_not_member(session: Session, alice, bob):
    org = org_service.create_org(
        session, name="Private", slug="private", created_by=alice.id
    )
    result = org_service.get_org_for_member(session, org_id=org.id, user_id=bob.id)
    assert result is None


def test_get_org_returns_org_for_member_service(session: Session, alice):
    org = org_service.create_org(session, name="Mine", slug="mine", created_by=alice.id)
    result = org_service.get_org_for_member(session, org_id=org.id, user_id=alice.id)
    assert result is not None
    assert result.id == org.id


def test_update_org_service(session: Session, alice):
    org = org_service.create_org(session, name="Old", slug="old", created_by=alice.id)
    updated = org_service.update_org(session, org=org, name="New", slug="new-slug")
    assert updated.name == "New"
    assert updated.slug == "new-slug"


def test_soft_delete_org_service(session: Session, alice):
    org = org_service.create_org(
        session, name="ToDelete", slug="to-delete", created_by=alice.id
    )
    org_service.soft_delete_org(session, org=org)
    result = org_service.get_org_for_member(session, org_id=org.id, user_id=alice.id)
    assert result is None


def test_list_members_service(session: Session, alice, bob):
    org = org_service.create_org(session, name="Team", slug="team", created_by=alice.id)
    org_service.add_member(
        session, org_id=org.id, user_id=bob.id, role=OrgRole.member
    )
    members = org_service.list_members(session, org_id=org.id)
    assert len(members) == 2


def test_change_role_service(session: Session, alice, bob):
    org = org_service.create_org(session, name="Team", slug="team2", created_by=alice.id)
    org_service.add_member(
        session, org_id=org.id, user_id=bob.id, role=OrgRole.member
    )
    membership = org_service.change_role(
        session, org_id=org.id, user_id=bob.id, role=OrgRole.admin
    )
    assert membership is not None
    assert membership.role == OrgRole.admin


def test_remove_member_service(session: Session, alice, bob):
    org = org_service.create_org(session, name="Team", slug="team3", created_by=alice.id)
    org_service.add_member(
        session, org_id=org.id, user_id=bob.id, role=OrgRole.member
    )
    org_service.remove_member(session, org_id=org.id, user_id=bob.id)
    members = org_service.list_members(session, org_id=org.id)
    assert len(members) == 1
