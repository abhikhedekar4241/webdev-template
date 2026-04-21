import uuid
from datetime import datetime, timedelta

import pytest

from app.models.invitation import InvitationStatus, OrgInvitation
from app.models.org import OrgMembership, OrgRole, Organization
from app.models.user import User
from app.services.auth import auth_service
from app.services.invitations import invitation_service
from app.services.orgs import org_service


@pytest.fixture(autouse=True)
def create_tables(session):
    User.__table__.create(session.get_bind(), checkfirst=True)
    Organization.__table__.create(session.get_bind(), checkfirst=True)
    OrgMembership.__table__.create(session.get_bind(), checkfirst=True)
    OrgInvitation.__table__.create(session.get_bind(), checkfirst=True)
    yield
    OrgInvitation.__table__.drop(session.get_bind())
    OrgMembership.__table__.drop(session.get_bind())
    Organization.__table__.drop(session.get_bind())
    User.__table__.drop(session.get_bind())


@pytest.fixture
def alice(session):
    return auth_service.create_user(
        session, email="alice@example.com", password="pass", full_name="Alice"
    )


@pytest.fixture
def org(session, alice):
    return org_service.create_org(
        session, name="Acme", slug="acme", created_by=alice.id
    )


def test_create_invitation(session, alice, org):
    inv = invitation_service.create_invitation(
        session,
        org_id=org.id,
        invited_email="newbie@example.com",
        role=OrgRole.member,
        invited_by=alice.id,
    )
    assert inv.org_id == org.id
    assert inv.invited_email == "newbie@example.com"
    assert inv.role == OrgRole.member
    assert inv.status == InvitationStatus.pending
    assert inv.expires_at > datetime.utcnow()


def test_list_pending_for_email(session, alice, org):
    invitation_service.create_invitation(
        session,
        org_id=org.id,
        invited_email="target@example.com",
        role=OrgRole.member,
        invited_by=alice.id,
    )
    result = invitation_service.list_pending_for_email(session, "target@example.com")
    assert len(result) == 1
    assert result[0].invited_email == "target@example.com"


def test_list_pending_for_email_excludes_non_pending(session, alice, org):
    inv = invitation_service.create_invitation(
        session,
        org_id=org.id,
        invited_email="target@example.com",
        role=OrgRole.member,
        invited_by=alice.id,
    )
    inv.status = InvitationStatus.accepted
    session.add(inv)
    session.commit()
    result = invitation_service.list_pending_for_email(session, "target@example.com")
    assert len(result) == 0


def test_accept_invitation(session, alice, org):
    bob = auth_service.create_user(
        session, email="bob@example.com", password="pass", full_name="Bob"
    )
    inv = invitation_service.create_invitation(
        session,
        org_id=org.id,
        invited_email=bob.email,
        role=OrgRole.member,
        invited_by=alice.id,
    )
    result = invitation_service.accept_invitation(session, invitation=inv, user=bob)
    assert result is True
    membership = org_service.get_membership(session, org_id=org.id, user_id=bob.id)
    assert membership is not None
    assert membership.role == OrgRole.member
    session.refresh(inv)
    assert inv.status == InvitationStatus.accepted


def test_accept_invitation_wrong_email(session, alice, org):
    bob = auth_service.create_user(
        session, email="bob@example.com", password="pass", full_name="Bob"
    )
    inv = invitation_service.create_invitation(
        session,
        org_id=org.id,
        invited_email="other@example.com",
        role=OrgRole.member,
        invited_by=alice.id,
    )
    result = invitation_service.accept_invitation(session, invitation=inv, user=bob)
    assert result is False


def test_decline_invitation(session, alice, org):
    bob = auth_service.create_user(
        session, email="bob@example.com", password="pass", full_name="Bob"
    )
    inv = invitation_service.create_invitation(
        session,
        org_id=org.id,
        invited_email=bob.email,
        role=OrgRole.member,
        invited_by=alice.id,
    )
    result = invitation_service.decline_invitation(session, invitation=inv, user=bob)
    assert result is True
    session.refresh(inv)
    assert inv.status == InvitationStatus.declined


def test_decline_invitation_wrong_email(session, alice, org):
    bob = auth_service.create_user(
        session, email="bob@example.com", password="pass", full_name="Bob"
    )
    inv = invitation_service.create_invitation(
        session,
        org_id=org.id,
        invited_email="other@example.com",
        role=OrgRole.member,
        invited_by=alice.id,
    )
    result = invitation_service.decline_invitation(session, invitation=inv, user=bob)
    assert result is False
