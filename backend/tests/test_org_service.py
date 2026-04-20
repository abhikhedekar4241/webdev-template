import pytest

from app.models.org import Organization, OrgMembership, OrgRole
from app.models.user import User
from app.services.auth import auth_service
from app.services.orgs import org_service


@pytest.fixture(autouse=True)
def create_tables(session):
    User.__table__.create(session.get_bind(), checkfirst=True)
    Organization.__table__.create(session.get_bind(), checkfirst=True)
    OrgMembership.__table__.create(session.get_bind(), checkfirst=True)
    yield
    OrgMembership.__table__.drop(session.get_bind())
    Organization.__table__.drop(session.get_bind())
    User.__table__.drop(session.get_bind())


@pytest.fixture
def user(session):
    return auth_service.create_user(
        session, email="alice@example.com", password="pass", full_name="Alice"
    )


@pytest.fixture
def user2(session):
    return auth_service.create_user(
        session, email="bob@example.com", password="pass", full_name="Bob"
    )


def test_create_org_assigns_owner(session, user):
    org = org_service.create_org(session, name="Acme", slug="acme", created_by=user.id)
    assert org.name == "Acme"
    assert org.slug == "acme"
    membership = org_service.get_membership(session, org_id=org.id, user_id=user.id)
    assert membership is not None
    assert membership.role == OrgRole.owner


def test_list_user_orgs(session, user, user2):
    org1 = org_service.create_org(session, name="Org1", slug="org1", created_by=user.id)
    org_service.create_org(session, name="Org2", slug="org2", created_by=user2.id)
    orgs = org_service.list_user_orgs(session, user_id=user.id)
    assert len(orgs) == 1
    assert orgs[0].id == org1.id


def test_get_org_returns_none_if_not_member(session, user, user2):
    org = org_service.create_org(
        session, name="Private", slug="private", created_by=user.id
    )
    result = org_service.get_org_for_member(session, org_id=org.id, user_id=user2.id)
    assert result is None


def test_get_org_returns_org_for_member(session, user):
    org = org_service.create_org(session, name="Mine", slug="mine", created_by=user.id)
    result = org_service.get_org_for_member(session, org_id=org.id, user_id=user.id)
    assert result is not None
    assert result.id == org.id


def test_update_org(session, user):
    org = org_service.create_org(session, name="Old", slug="old", created_by=user.id)
    updated = org_service.update_org(session, org=org, name="New", slug="new-slug")
    assert updated.name == "New"
    assert updated.slug == "new-slug"


def test_soft_delete_org(session, user):
    org = org_service.create_org(
        session, name="ToDelete", slug="to-delete", created_by=user.id
    )
    org_service.soft_delete_org(session, org=org)
    result = org_service.get_org_for_member(session, org_id=org.id, user_id=user.id)
    assert result is None


def test_list_members(session, user, user2):
    org = org_service.create_org(session, name="Team", slug="team", created_by=user.id)
    org_service.add_member(
        session, org_id=org.id, user_id=user2.id, role=OrgRole.member
    )
    members = org_service.list_members(session, org_id=org.id)
    assert len(members) == 2


def test_change_role(session, user, user2):
    org = org_service.create_org(session, name="Team", slug="team2", created_by=user.id)
    org_service.add_member(
        session, org_id=org.id, user_id=user2.id, role=OrgRole.member
    )
    membership = org_service.change_role(
        session, org_id=org.id, user_id=user2.id, role=OrgRole.admin
    )
    assert membership is not None
    assert membership.role == OrgRole.admin


def test_remove_member(session, user, user2):
    org = org_service.create_org(session, name="Team", slug="team3", created_by=user.id)
    org_service.add_member(
        session, org_id=org.id, user_id=user2.id, role=OrgRole.member
    )
    org_service.remove_member(session, org_id=org.id, user_id=user2.id)
    members = org_service.list_members(session, org_id=org.id)
    assert len(members) == 1
