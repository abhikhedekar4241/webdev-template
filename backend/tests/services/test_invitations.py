import pytest
from datetime import UTC, datetime
from sqlmodel import Session
from app.core.exceptions import InvitationInvalidError, MemberAlreadyExistsError
from app.models.invitation import InvitationStatus
from app.models.org import OrgRole
from app.services.invitations import invitation_service
from app.services.orgs import org_service

def test_create_invitation_service(session: Session, alice, alice_org):
    inv = invitation_service.create_invitation(
        session,
        org_id=alice_org.id,
        invited_email="newbie@example.com",
        role=OrgRole.member,
        invited_by=alice.id,
    )
    assert inv.org_id == alice_org.id
    assert inv.invited_email == "newbie@example.com"
    assert inv.role == OrgRole.member
    assert inv.status == InvitationStatus.pending
    assert inv.expires_at > datetime.now(UTC)


def test_create_invitation_member_exists(session: Session, alice, alice_org, bob):
    org_service.add_member(session, org_id=alice_org.id, user_id=bob.id, role=OrgRole.member)
    
    with pytest.raises(MemberAlreadyExistsError):
        invitation_service.create_invitation(
            session,
            org_id=alice_org.id,
            invited_email=bob.email,
            role=OrgRole.member,
            invited_by=alice.id,
        )


def test_list_pending_for_email(session: Session, alice, alice_org):
    invitation_service.create_invitation(
        session,
        org_id=alice_org.id,
        invited_email="target@example.com",
        role=OrgRole.member,
        invited_by=alice.id,
    )
    result = invitation_service.list_pending_for_email(session, "target@example.com")
    assert len(result) == 1
    assert result[0].invited_email == "target@example.com"


def test_list_pending_for_email_excludes_non_pending(session: Session, alice, alice_org):
    inv = invitation_service.create_invitation(
        session,
        org_id=alice_org.id,
        invited_email="target@example.com",
        role=OrgRole.member,
        invited_by=alice.id,
    )
    inv.status = InvitationStatus.accepted
    session.add(inv)
    session.commit()
    result = invitation_service.list_pending_for_email(session, "target@example.com")
    assert len(result) == 0


def test_accept_invitation_service(session: Session, alice, alice_org, bob):
    inv = invitation_service.create_invitation(
        session,
        org_id=alice_org.id,
        invited_email=bob.email,
        role=OrgRole.member,
        invited_by=alice.id,
    )
    invitation_service.accept_invitation(session, invitation=inv, user=bob)
    membership = org_service.get_membership(session, org_id=alice_org.id, user_id=bob.id)
    assert membership is not None
    assert membership.role == OrgRole.member
    session.refresh(inv)
    assert inv.status == InvitationStatus.accepted


def test_accept_invitation_wrong_email(session: Session, alice, alice_org, bob):
    inv = invitation_service.create_invitation(
        session,
        org_id=alice_org.id,
        invited_email="other@example.com",
        role=OrgRole.member,
        invited_by=alice.id,
    )
    with pytest.raises(InvitationInvalidError):
        invitation_service.accept_invitation(session, invitation=inv, user=bob)


def test_decline_invitation_service(session: Session, alice, alice_org, bob):
    inv = invitation_service.create_invitation(
        session,
        org_id=alice_org.id,
        invited_email=bob.email,
        role=OrgRole.member,
        invited_by=alice.id,
    )
    invitation_service.decline_invitation(session, invitation=inv, user=bob)
    session.refresh(inv)
    assert inv.status == InvitationStatus.declined
