import uuid

import structlog
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from app.api.deps import get_current_user, require_org, require_role
from app.core.db import get_session
from app.models.org import OrgRole
from app.models.user import User
from app.schemas.orgs import (
    MembershipResponse,
    OrgCreate,
    OrgResponse,
    OrgUpdate,
    RoleUpdate,
)
from app.services.orgs import org_service

router = APIRouter(prefix="/api/v1/orgs", tags=["orgs"])
logger = structlog.get_logger()


@router.post("/", response_model=OrgResponse, status_code=201)
def create_org(
    body: OrgCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if not body.slug or not body.slug.strip():
        raise HTTPException(status_code=422, detail="Slug cannot be empty")
    try:
        org = org_service.create_org(
            session, name=body.name, slug=body.slug, created_by=current_user.id
        )
        session.commit()
        session.refresh(org)
        return org
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=409, detail="An organization with this slug already exists"
        )


@router.get("/", response_model=list[OrgResponse])
def list_orgs(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return org_service.list_user_orgs(session, user_id=current_user.id)


@router.get("/slug/{slug}", response_model=OrgResponse)
def get_org_by_slug(
    slug: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    org = org_service.get_org_for_member_by_slug(
        session, slug=slug, user_id=current_user.id
    )
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org


@router.get("/{org_id}", response_model=OrgResponse)
def get_org(
    org_id: uuid.UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return require_org(session, org_id, current_user.id)


@router.patch("/{org_id}", response_model=OrgResponse)
def update_org(
    org_id: uuid.UUID,
    body: OrgUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    org = require_org(session, org_id, current_user.id)
    require_role(session, org_id, current_user.id, [OrgRole.owner, OrgRole.admin])
    try:
        updated = org_service.update_org(
            session, org=org, name=body.name, slug=body.slug
        )
        session.commit()
        session.refresh(updated)
        return updated
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=409, detail="An organization with this slug already exists"
        )


@router.delete("/{org_id}", status_code=204)
def delete_org(
    org_id: uuid.UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    org = require_org(session, org_id, current_user.id)
    require_role(session, org_id, current_user.id, [OrgRole.owner])
    org_service.soft_delete_org(session, org=org)
    session.commit()


@router.get("/{org_id}/members", response_model=list[MembershipResponse])
def list_members(
    org_id: uuid.UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    require_org(session, org_id, current_user.id)
    memberships_with_users = org_service.list_members_with_users(session, org_id=org_id)
    return [
        MembershipResponse(
            user_id=m.user_id,
            email=u.email,
            full_name=u.full_name,
            role=m.role,
            joined_at=m.joined_at,
        )
        for m, u in memberships_with_users
    ]


@router.patch("/{org_id}/members/{user_id}", response_model=MembershipResponse)
def change_member_role(
    org_id: uuid.UUID,
    user_id: uuid.UUID,
    body: RoleUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    require_org(session, org_id, current_user.id)
    require_role(session, org_id, current_user.id, [OrgRole.owner, OrgRole.admin])
    membership = org_service.change_role(
        session, org_id=org_id, user_id=user_id, role=body.role
    )
    if not membership:
        raise HTTPException(status_code=404, detail="Member not found")

    session.commit()
    session.refresh(membership)

    user = session.get(User, membership.user_id)
    return MembershipResponse(
        user_id=membership.user_id,
        email=user.email if user else "",
        full_name=user.full_name if user else "",
        role=membership.role,
        joined_at=membership.joined_at,
    )


@router.delete("/{org_id}/members/{user_id}", status_code=204)
def remove_member(
    org_id: uuid.UUID,
    user_id: uuid.UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    require_org(session, org_id, current_user.id)
    require_role(session, org_id, current_user.id, [OrgRole.owner, OrgRole.admin])
    target_membership = org_service.get_membership(
        session, org_id=org_id, user_id=user_id
    )
    if target_membership and target_membership.role == OrgRole.owner:
        raise HTTPException(status_code=403, detail="Cannot remove the org owner")
    org_service.remove_member(session, org_id=org_id, user_id=user_id)
    session.commit()
