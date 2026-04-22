import uuid
from datetime import UTC, datetime, timedelta

import structlog
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.exceptions import (
    InvitationAlreadyExistsError,
    InvitationInvalidError,
    MemberAlreadyExistsError,
)
from app.models.invitation import InvitationStatus, OrgInvitation
from app.models.org import OrgMembership, OrgRole, Organization
from app.models.user import User
from app.services.auth import auth_service
from app.services.base import CRUDBase
from app.services.notifications import notification_service
from app.services.orgs import org_service

logger = structlog.get_logger()
INVITATION_TTL_DAYS = 7


class InvitationService(CRUDBase[OrgInvitation]):
    async def create_invitation(
        self,
        session: AsyncSession,
        *,
        org_id: uuid.UUID,
        invited_email: str,
        role: OrgRole,
        invited_by: uuid.UUID,
    ) -> OrgInvitation:
        # Check if the invitee is already a member
        existing_user = await auth_service.get_by_email(session, email=invited_email)
        if existing_user:
            existing_membership = await org_service.get_membership(
                session, org_id=org_id, user_id=existing_user.id
            )
            if existing_membership:
                raise MemberAlreadyExistsError()

        # Check for an existing pending invitation
        existing_invite = (await session.exec(
            select(OrgInvitation).where(
                OrgInvitation.org_id == org_id,
                OrgInvitation.invited_email == invited_email,
                OrgInvitation.status == InvitationStatus.pending,
            )
        )).first()
        if existing_invite:
            raise InvitationAlreadyExistsError()

        inv = OrgInvitation(
            org_id=org_id,
            invited_email=invited_email,
            role=role,
            invited_by=invited_by,
            expires_at=datetime.now(UTC) + timedelta(days=INVITATION_TTL_DAYS),
        )
        session.add(inv)
        await session.flush()

        logger.info(
            "invitation_created",
            invitation_id=str(inv.id),
            org_id=str(org_id),
            invited_email=invited_email,
            invited_by=str(invited_by),
        )

        # Create notification if user exists
        if existing_user:
            org = await session.get(Organization, org_id)
            org_name = org.name if org else "an organization"
            await notification_service.create_notification(
                session,
                user_id=existing_user.id,
                type="org_invitation",
                data={
                    "invitation_id": str(inv.id),
                    "org_id": str(org_id),
                    "org_name": org_name,
                },
            )

        return inv

    async def list_pending_for_email(
        self, session: AsyncSession, email: str
    ) -> list[OrgInvitation]:
        return list(
            (await session.exec(
                select(OrgInvitation)
                .where(OrgInvitation.invited_email == email)
                .where(OrgInvitation.status == InvitationStatus.pending)
            )).all()
        )

    async def accept_invitation(
        self, session: AsyncSession, *, invitation: OrgInvitation, user: User
    ) -> None:
        if invitation.invited_email != user.email:
            raise InvitationInvalidError("This invitation is not for you")
        
        if invitation.status != InvitationStatus.pending:
            raise InvitationInvalidError("Invitation is no longer pending")
            
        if invitation.expires_at < datetime.now(UTC):
            raise InvitationInvalidError("Invitation has expired")

        invitation.status = InvitationStatus.accepted
        session.add(invitation)
        
        await org_service.add_member(
            session,
            org_id=invitation.org_id,
            user_id=user.id,
            role=invitation.role,
        )
        await session.flush()
        
        logger.info(
            "invitation_accepted",
            invitation_id=str(invitation.id),
            user_id=str(user.id),
            org_id=str(invitation.org_id),
        )
        
        await self.cleanup_notification(session, invitation_id=invitation.id, user_id=user.id)

    async def decline_invitation(
        self, session: AsyncSession, *, invitation: OrgInvitation, user: User
    ) -> None:
        if invitation.invited_email != user.email:
            raise InvitationInvalidError("This invitation is not for you")
            
        invitation.status = InvitationStatus.declined
        session.add(invitation)
        await session.flush()
        
        logger.info(
            "invitation_declined",
            invitation_id=str(invitation.id),
            user_id=str(user.id),
            org_id=str(invitation.org_id),
        )
        
        await self.cleanup_notification(session, invitation_id=invitation.id, user_id=user.id)

    async def cleanup_notification(
        self, session: AsyncSession, *, invitation_id: uuid.UUID, user_id: uuid.UUID
    ) -> None:
        from app.models.notification import Notification

        statement = select(Notification).where(
            Notification.user_id == user_id,
            Notification.type == "org_invitation",
            Notification.read_at.is_(None),  # type: ignore
        )
        notifications = (await session.exec(statement)).all()
        for n in notifications:
            if n.data.get("invitation_id") == str(invitation_id):
                n.read_at = datetime.now(UTC)
                session.add(n)
        await session.flush()


invitation_service = InvitationService(OrgInvitation)
