import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlmodel import Session

from sqlmodel import select

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.db import get_session
from app.models.invitation import OrgInvitation, InvitationStatus
from app.models.org import Organization, OrgMembership, OrgRole
from app.models.user import User
from app.services.email import email_service
from app.services.invitations import invitation_service
from app.services.orgs import org_service

router = APIRouter(prefix="/api/v1/invitations", tags=["invitations"])


class InvitationCreate(BaseModel):
    org_id: uuid.UUID
    email: EmailStr
    role: OrgRole


class InvitationResponse(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    invited_email: str
    role: OrgRole
    status: str
    expires_at: datetime
    created_at: datetime


class MessageResponse(BaseModel):
    message: str


def _get_invitation_or_404(session: Session, inv_id: uuid.UUID) -> OrgInvitation:
    inv = session.get(OrgInvitation, inv_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Invitation not found")
    return inv


@router.post("/", response_model=InvitationResponse, status_code=201)
def create_invitation(
    body: InvitationCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    membership = org_service.get_membership(
        session, org_id=body.org_id, user_id=current_user.id
    )
    if not membership or membership.role not in (OrgRole.owner, OrgRole.admin):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    org = session.get(Organization, body.org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Check if the invitee is already a member
    existing_user = session.exec(select(User).where(User.email == body.email)).first()
    if existing_user:
        existing_membership = session.exec(
            select(OrgMembership).where(
                OrgMembership.org_id == body.org_id,
                OrgMembership.user_id == existing_user.id,
            )
        ).first()
        if existing_membership:
            raise HTTPException(status_code=409, detail="User is already a member of this organization")

    # Check for an existing pending invitation for this email+org
    existing_invite = session.exec(
        select(OrgInvitation).where(
            OrgInvitation.org_id == body.org_id,
            OrgInvitation.invited_email == body.email,
            OrgInvitation.status == InvitationStatus.pending,
        )
    ).first()
    if existing_invite:
        raise HTTPException(status_code=409, detail="A pending invitation already exists for this email")

    inv = invitation_service.create_invitation(
        session,
        org_id=body.org_id,
        invited_email=body.email,
        role=body.role,
        invited_by=current_user.id,
    )

    email_service.send(
        to=body.email,
        subject=f"You've been invited to join {org.name}",
        template="invite",
        context={
            "org_name": org.name,
            "invited_by_name": current_user.full_name,
            "role": body.role.value,
            "invitations_url": f"{settings.FRONTEND_URL}/invitations",
        },
    )

    return inv


@router.get("/", response_model=list[InvitationResponse])
def list_invitations(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return invitation_service.list_pending_for_email(session, current_user.email)


@router.post("/{inv_id}/accept", response_model=MessageResponse)
def accept_invitation(
    inv_id: uuid.UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    inv = _get_invitation_or_404(session, inv_id)
    success = invitation_service.accept_invitation(
        session, invitation=inv, user=current_user
    )
    if not success:
        raise HTTPException(status_code=403, detail="This invitation is not for you")
    return {"message": "Invitation accepted"}


@router.post("/{inv_id}/decline", response_model=MessageResponse)
def decline_invitation(
    inv_id: uuid.UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    inv = _get_invitation_or_404(session, inv_id)
    success = invitation_service.decline_invitation(
        session, invitation=inv, user=current_user
    )
    if not success:
        raise HTTPException(status_code=403, detail="This invitation is not for you")
    return {"message": "Invitation declined"}
