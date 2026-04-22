import uuid

import structlog
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps import get_current_user, require_role
from app.core.config import settings
from app.core.db import get_session
from app.models.invitation import OrgInvitation
from app.models.org import Organization, OrgRole
from app.models.user import User
from app.schemas.invitations import (
    InvitationCreate,
    InvitationResponse,
    MessageResponse,
)
from app.services.email import email_service
from app.services.invitations import invitation_service

router = APIRouter(prefix="/api/v1/invitations", tags=["invitations"])
logger = structlog.get_logger()


async def _get_invitation_or_404(session: AsyncSession, inv_id: uuid.UUID) -> OrgInvitation:
    inv = await session.get(OrgInvitation, inv_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Invitation not found")
    return inv


@router.post("/", response_model=InvitationResponse, status_code=201)
async def create_invitation(
    body: InvitationCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    await require_role(session, body.org_id, current_user.id, [OrgRole.owner, OrgRole.admin])

    org = await session.get(Organization, body.org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    inv = await invitation_service.create_invitation(
        session,
        org_id=body.org_id,
        invited_email=body.email,
        role=body.role,
        invited_by=current_user.id,
    )

    # Capture values before commit (objects expire after commit)
    org_name = org.name
    invited_by_name = current_user.full_name
    role_value = body.role.value

    await session.commit()
    await session.refresh(inv)

    email_service.send(
        to=body.email,
        subject=f"You've been invited to join {org_name}",
        template="invite",
        context={
            "org_name": org_name,
            "invited_by_name": invited_by_name,
            "role": role_value,
            "invitations_url": f"{settings.FRONTEND_URL}/invitations",
        },
    )

    return InvitationResponse(
        id=inv.id,
        org_id=inv.org_id,
        org_name=org_name,
        invited_email=inv.invited_email,
        role=inv.role,
        status=inv.status,
        expires_at=inv.expires_at,
        created_at=inv.created_at,
    )


@router.get("/", response_model=list[InvitationResponse])
async def list_invitations(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    invitations = await invitation_service.list_pending_for_email(session, current_user.email)

    results = []
    for inv in invitations:
        org = await session.get(Organization, inv.org_id)
        results.append(
            InvitationResponse(
                id=inv.id,
                org_id=inv.org_id,
                org_name=org.name if org else "Unknown",
                invited_email=inv.invited_email,
                role=inv.role,
                status=inv.status,
                expires_at=inv.expires_at,
                created_at=inv.created_at,
            )
        )

    return results


@router.post("/{inv_id}/accept", response_model=MessageResponse)
async def accept_invitation(
    inv_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    inv = await _get_invitation_or_404(session, inv_id)
    await invitation_service.accept_invitation(session, invitation=inv, user=current_user)
    await session.commit()
    return MessageResponse(message="Invitation accepted")


@router.post("/{inv_id}/decline", response_model=MessageResponse)
async def decline_invitation(
    inv_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    inv = await _get_invitation_or_404(session, inv_id)
    await invitation_service.decline_invitation(session, invitation=inv, user=current_user)
    await session.commit()
    return MessageResponse(message="Invitation declined")
