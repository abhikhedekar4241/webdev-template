from datetime import UTC, datetime

import pytest
from sqlmodel import Session

from app.core.exceptions import InvitationInvalidError, MemberAlreadyExistsError
from app.models.invitation import InvitationStatus
from app.models.org import OrgRole
from app.services.invitations import invitation_service
from app.services.orgs import org_service


async def test_create_invitation_service(session: Session, alice, alice_org):
    inv = await invitation_service.create_invitation(
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


async def test_create_invitation_member_exists(session: Session, alice, alice_org, bob):
    await org_service.add_member(
        session, org_id=alice_org.id, user_id=bob.id, role=OrgRole.member
    )

    with pytest.raises(MemberAlreadyExistsError):
        await invitation_service.create_invitation(
            session,
            org_id=alice_org.id,
            invited_email=bob.email,
            role=OrgRole.member,
            invited_by=alice.id,
        )


async def test_list_pending_for_email(session: Session, alice, alice_org):
    await invitation_service.create_invitation(
        session,
        org_id=alice_org.id,
        invited_email="target@example.com",
        role=OrgRole.member,
        invited_by=alice.id,
    )
    result = await invitation_service.list_pending_for_email(
        session, "target@example.com"
    )
    assert len(result) == 1
    assert result[0].invited_email == "target@example.com"


async def test_list_pending_for_email_excludes_non_pending(
    session: Session, alice, alice_org
):
    inv = await invitation_service.create_invitation(
        session,
        org_id=alice_org.id,
        invited_email="target@example.com",
        role=OrgRole.member,
        invited_by=alice.id,
    )
    inv.status = InvitationStatus.accepted
    session.add(inv)
    await session.commit()
    result = await invitation_service.list_pending_for_email(
        session, "target@example.com"
    )
    assert len(result) == 0


async def test_accept_invitation_service(session: Session, alice, alice_org, bob):
    inv = await invitation_service.create_invitation(
        session,
        org_id=alice_org.id,
        invited_email=bob.email,
        role=OrgRole.member,
        invited_by=alice.id,
    )
    await invitation_service.accept_invitation(session, invitation=inv, user=bob)
    membership = await org_service.get_membership(
        session, org_id=alice_org.id, user_id=bob.id
    )
    assert membership is not None
    assert membership.role == OrgRole.member
    await session.refresh(inv)
    assert inv.status == InvitationStatus.accepted


async def test_accept_invitation_wrong_email(session: Session, alice, alice_org, bob):
    inv = await invitation_service.create_invitation(
        session,
        org_id=alice_org.id,
        invited_email="other@example.com",
        role=OrgRole.member,
        invited_by=alice.id,
    )
    with pytest.raises(InvitationInvalidError):
        await invitation_service.accept_invitation(session, invitation=inv, user=bob)


async def test_decline_invitation_service(session: Session, alice, alice_org, bob):
    inv = await invitation_service.create_invitation(
        session,
        org_id=alice_org.id,
        invited_email=bob.email,
        role=OrgRole.member,
        invited_by=alice.id,
    )
    await invitation_service.decline_invitation(session, invitation=inv, user=bob)
    await session.refresh(inv)
    assert inv.status == InvitationStatus.declined
