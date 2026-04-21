import uuid
from datetime import datetime, timedelta

from sqlmodel import Session, select

from app.models.invitation import InvitationStatus, OrgInvitation
from app.models.org import OrgRole
from app.models.user import User
from app.services.base import CRUDBase
from app.services.orgs import org_service

INVITATION_TTL_DAYS = 7


class InvitationService(CRUDBase[OrgInvitation]):
    def create_invitation(
        self,
        session: Session,
        *,
        org_id: uuid.UUID,
        invited_email: str,
        role: OrgRole,
        invited_by: uuid.UUID,
    ) -> OrgInvitation:
        inv = OrgInvitation(
            org_id=org_id,
            invited_email=invited_email,
            role=role,
            invited_by=invited_by,
            expires_at=datetime.utcnow() + timedelta(days=INVITATION_TTL_DAYS),
        )
        session.add(inv)
        session.commit()
        session.refresh(inv)
        return inv

    def list_pending_for_email(
        self, session: Session, email: str
    ) -> list[OrgInvitation]:
        return list(
            session.exec(
                select(OrgInvitation)
                .where(OrgInvitation.invited_email == email)
                .where(OrgInvitation.status == InvitationStatus.pending)
            ).all()
        )

    def accept_invitation(
        self, session: Session, *, invitation: OrgInvitation, user: User
    ) -> bool:
        if invitation.invited_email != user.email:
            return False
        invitation.status = InvitationStatus.accepted
        session.add(invitation)
        org_service.add_member(
            session,
            org_id=invitation.org_id,
            user_id=user.id,
            role=invitation.role,
        )
        session.commit()
        return True

    def decline_invitation(
        self, session: Session, *, invitation: OrgInvitation, user: User
    ) -> bool:
        if invitation.invited_email != user.email:
            return False
        invitation.status = InvitationStatus.declined
        session.add(invitation)
        session.commit()
        return True


invitation_service = InvitationService(OrgInvitation)
